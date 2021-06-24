import json
import logging
from multiprocessing.pool import ThreadPool
from os import makedirs
from os.path import join
from random import choice, shuffle
from typing import List, Dict, Union

from numpy import array_split
from scipy.optimize import minimize, Bounds
from tqdm import tqdm

from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.BoundingBox import BoundingBox
from loader.Dataset import Dataset
from rater.FitnessRater import FitnessRater
from search.ExhaustiveSearch import ExhaustiveSearch
from search.GeneticSearch import GeneticSearch
from search.GeneticSearchConfiguration import GeneticSearchConfiguration

logger = logging.getLogger(__name__)


class CrossValidationTraining(object):
    def __init__(self, k: int, dataset: Dataset, out_path: str, weight_tuning_rounds=10, search_rounds=10):
        self._k = k
        self._dataset = dataset

        self._out_path = join(out_path, dataset.name, self.__class__.__name__)
        makedirs(self._out_path, exist_ok=True)

        self._weight_tuning_rounds = weight_tuning_rounds
        self._training_pool = ThreadPool(self._weight_tuning_rounds)
        self._search_rounds = search_rounds

    def start(self):
        """Runs a cross validation training"""
        folds = self.get_folds()
        self.dump("folds.json", [{i: fold} for i, fold in enumerate(folds)])

        fold_accuracies = []
        for fold_num, fold in enumerate(folds):
            logger.info(f"Working on fold {fold_num + 1}/{self._k}")
            fold_file_accuracies = self.process_fold(fold, fold_num)
            fold_accuracy = sum(fold_file_accuracies.values()) / len(fold_file_accuracies.values())
            self.dump(
                f"fold_{fold_num}_file_accuracies.json",
                {"fold_file_accuracies": fold_file_accuracies, "fold_accuracy": fold_accuracy},
                subdir=f"fold_{fold_num}",
            )
            fold_accuracies.append(fold_accuracy)

        self.dump(
            "final_accuracy.json",
            sum(fold_accuracies) / len(fold_accuracies),
        )
        return sum(fold_accuracies) / len(fold_accuracies)

    def get_folds(self) -> List[Dict[str, List]]:
        """Creates folds for cross validation while balancing single and multi table files per fold"""
        single_table_keys = self._dataset.single_table_keys
        multi_table_keys = self._dataset.multi_table_keys

        shuffle(single_table_keys)
        shuffle(multi_table_keys)

        single_table_chunks = array_split(single_table_keys, self._k)
        multi_table_chunks = array_split(multi_table_keys, self._k)

        test_chunks = [list(s_chunk) + list(m_chunk) for s_chunk, m_chunk in
                       zip(single_table_chunks, multi_table_chunks)]
        train_chunks = [list(set(self._dataset.keys).difference(test_chunk)) for test_chunk in test_chunks]

        return [{"train": train_chunk, "test": test_chunk} for train_chunk, test_chunk in
                zip(train_chunks, test_chunks)]

    def process_fold(self, fold: Dict[str, List], fold_num: int) -> Dict[str, float]:
        """Evaluates on fold of the cross validation, returns the accuracy per file of the fold"""
        # Train multiple rounds
        logger.info("Training Rounds:")
        weights_and_errors = self._training_pool.map(lambda i: self.train(fold["train"], fold_num, i),
                                                     range(self._weight_tuning_rounds))
        weights = CrossValidationTraining.weighted_average(weights_and_errors)

        self.dump(
            f"fold_{fold_num}_weights.json",
            {"weights_and_errors": weights_and_errors, "weights": weights},
            subdir=f"fold_{fold_num}"
        )

        logger.info("Test Set Validation")
        file_accuracies = {}
        for key in tqdm(fold["test"]):
            logger.info(f"Processing {key}")
            sheet_data = self._dataset.get_specific_sheetdata(key)
            sheet_graph = SpreadSheetGraph(sheet_data)
            ground_truth = sheet_graph.get_table_definitions()
            rater = FitnessRater(weights)
            if len(sheet_graph.nodes) <= 10:
                accuracy = CrossValidationTraining.exhaustive_search_accuracy(ground_truth, sheet_graph, rater)
            else:
                accuracy = self.genetic_search_accuracy(ground_truth, sheet_graph, rater)
            file_accuracies[key] = accuracy
        return file_accuracies

    @staticmethod
    def objective_function(weights: List[float], partitions: Dict[SpreadSheetGraph, List[List[bool]]],
                           rater: FitnessRater):
        """Objective function proposed by the paper"""
        rater.weights = weights
        score = 0
        for graph, alternative_toggle_lists in partitions.items():
            target_partition_part = 1 + rater.rate(graph, graph.edge_toggle_list)
            for alternative_toggle_list in alternative_toggle_lists:
                alternative_partition_part = 1 + rater.rate(graph, alternative_toggle_list)
                score += target_partition_part / alternative_partition_part
        logger.debug(f"score: {score}, weights: {weights}")
        return score

    @staticmethod
    def generate_alternatives(graph: SpreadSheetGraph, n=1) -> List[List[bool]]:
        """Generates n random edge toggle lists for the given graph"""
        alternatives = []
        for _ in range(n):
            alternatives.append([choice([True, False]) for _ in range(len(graph.edge_toggle_list))])
        return alternatives

    def train(self, train_keys: List[str], fold_num: int, training_round: int) -> Dict[str, Union[List[float], float]]:
        """Performs SQP on the given keys, outputs the resulting weights and their error rate"""
        graphs = [SpreadSheetGraph(self._dataset.get_specific_sheetdata(key)) for key in train_keys]

        partitions = {}
        for graph in graphs:
            partitions[graph] = CrossValidationTraining.generate_alternatives(graph, 10)

        self.dump(
            f"fold_{fold_num}_training_round_{training_round}_input.json",
            dict([(str(graph.sheet_data), partitions) for graph, partitions in partitions.items()]),
            subdir=join(f"fold_{fold_num}", "training")
        )

        initial_weights = [1 for _ in range(10)]
        # Create rater object outside to leverage caching
        rater = FitnessRater(initial_weights)

        res = minimize(
            CrossValidationTraining.objective_function,
            initial_weights,
            args=(partitions, rater),
            method="SLSQP",
            bounds=Bounds(0, 1000),
        )

        weights = list(res.x)
        rater.weights = weights

        total_alternative_count = 0
        better_than_original_alternative_count = 0
        for graph, alternatives in partitions.items():
            obj_score_original_graph = rater.rate(graph, graph.edge_toggle_list)
            total_alternative_count += len(alternatives)
            better_than_original_alternative_count += len([
                alternative
                for alternative in alternatives
                if rater.rate(graph, alternative) < obj_score_original_graph
            ])

        self.dump(
            f"fold_{fold_num}_training_round_{training_round}_result.json",
            {
                "weights": weights,
                "total_alternative_count": total_alternative_count,
                "better_than_original_alternative_count": better_than_original_alternative_count,
            },
            subdir=join(f"fold_{fold_num}", "training"),
        )

        return {"weights": weights, "error_rate": better_than_original_alternative_count / total_alternative_count}

    @staticmethod
    def accuracy_of_result(ground_truth: List[BoundingBox], computed_result: List[BoundingBox]) -> float:
        """Percent of recognized tables as proposed in the paper Section V.D, based on the jacard index"""
        recognized_tables = []
        for table in ground_truth:
            for computed_table in computed_result:
                cells_in_common = len(table.intersection(computed_table))
                cells_in_union = table.area + computed_table.area - cells_in_common
                jacard_index = cells_in_common / cells_in_union
                if jacard_index >= 0.9:
                    recognized_tables.append(table)
        return len(recognized_tables) / len(ground_truth)

    @staticmethod
    def exhaustive_search_accuracy(ground_truth: List[BoundingBox], sheet_graph: SpreadSheetGraph,
                                   rater: FitnessRater):
        """Runs an exhaustive search, evaluates the result against the ground truth, and returns the accuracy score"""
        search = ExhaustiveSearch(
            sheet_graph,
            rater,
        )
        result = search.run()
        return CrossValidationTraining.accuracy_of_result(ground_truth, result.get_table_definitions())

    def genetic_search_accuracy(self, ground_truth: List[BoundingBox], sheet_graph: SpreadSheetGraph,
                                rater: FitnessRater):
        """Runs genetic searches, evaluates the results against the ground truth, and returns the avg. accuracy score"""
        search = GeneticSearch(
            sheet_graph,
            rater,
            GeneticSearchConfiguration(sheet_graph),
        )
        accuracies = []
        for _ in range(self._search_rounds):
            result = search.run()
            accuracy = CrossValidationTraining.accuracy_of_result(ground_truth, result.get_table_definitions())
            accuracies.append(accuracy)

        return sum(accuracies) / len(accuracies)

    @staticmethod
    def weighted_average(weights_and_errors: List[Dict[str, Union[List[float], float]]]) -> List[float]:
        """Averages the given weights based on the error rate for those weight"""
        # weights always refer to the machine learning weight vector and contribution to the relevance (the weight)
        # of one of these vectors in this method
        total_err = sum([1 - e["error_rate"] for e in weights_and_errors])

        weights_and_contribution = [(e["weights"], (1 - e["error_rate"]) / total_err) for e in weights_and_errors]

        weight_vector = [0 for _ in range(len(weights_and_errors[0]["weights"]))]
        for weights, contribution in weights_and_contribution:
            weight_vector = [weight_vector[i] + weights[i] * contribution for i in range(len(weights))]
        return weight_vector

    def dump(self, file_name, data, subdir=""):
        if subdir != "":
            makedirs(join(self._out_path, subdir), exist_ok=True)

        with open(join(self._out_path, subdir, file_name), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)