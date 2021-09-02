"""k-fold cross validation with multiple weight tuning and genetic search rounds.
Weights and Accuracy are averaged.
Accuracy is measured as jacard-index >= 0.9"""

import json
import uuid
from os import makedirs
from os.path import join
from random import choice, shuffle, seed
from typing import List, Dict, Union, Callable

from numpy import array_split
from scipy.optimize import minimize, Bounds
from tqdm import tqdm

from dataset.Dataset import Dataset
from experiments import Analyser
from graph.Edge import Edge
from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.BoundingBox import BoundingBox
from labelregions.LabelRegionLoader import LabelRegionLoader
from search.ExhaustiveSearch import ExhaustiveSearch
from search.FitnessRater import FitnessRater, get_initial_weights
from search.GeneticSearch import GeneticSearch
from search.GeneticSearchConfiguration import GeneticSearchConfiguration


class CrossValidationTraining(object):
    def __init__(
            self,
            dataset: Dataset,
            label_region_loader: LabelRegionLoader,
            out_path: str,
            improvement_name: str,
            k=10,
            weight_tuning_rounds=10,
            search_rounds=10,
            random_seed=1,
            edge_mutation_probability_callback: Callable[[Edge], int] = lambda x: 1,
    ):
        seed(random_seed)
        self._dataset = dataset
        self._label_region_loader = label_region_loader

        # Create a unique output dir
        run_id = uuid.uuid1().hex
        noise_part = 'noise' if label_region_loader.introduce_noise else 'no_noise'
        dir_name = f"{noise_part}_{random_seed}_{run_id}"
        self._out_path = join(out_path, improvement_name, dataset.name, dir_name)
        makedirs(self._out_path, exist_ok=True)

        self._k = k
        self._weight_tuning_rounds = weight_tuning_rounds
        self._search_rounds = search_rounds

        # Used to create the Genetic Search Configuration
        self._edge_mutation_probability_callback = edge_mutation_probability_callback

        # Dump config
        self.dump("config.json", {
            "dataset": self._dataset.name,
            "noise": self._label_region_loader.introduce_noise,
            "k": self._k,
            "weight_tuning_rounds": self._weight_tuning_rounds,
            "search_rounds": self._search_rounds,
            "seed": random_seed,
        })

    def start(self):
        """Runs a cross validation training"""
        folds = self.get_folds()
        self.dump("folds.json", dict([(i, fold) for i, fold in enumerate(folds)]))

        fold_accuracies = []
        for fold_num_and_fold in tqdm(enumerate(folds)):
            fold_accuracies.append(self.process_fold(fold_num_and_fold[1], fold_num_and_fold[0]))

        self.dump(
            "final_accuracy.json",
            sum(fold_accuracies) / len(fold_accuracies),
        )
        # Total average accuracy
        return sum(fold_accuracies) / len(fold_accuracies)

    def get_folds(self) -> List[Dict[str, List]]:
        """Creates folds for cross validation while balancing single and multi table files per fold"""
        single_table_keys = self._dataset.single_table_keys
        multi_table_keys = self._dataset.multi_table_keys

        shuffle(single_table_keys)
        shuffle(multi_table_keys)

        single_table_chunks = array_split(single_table_keys, self._k)
        multi_table_chunks = array_split(multi_table_keys, self._k)

        # Combine Single and Multi Table Chunks to test folds
        test_chunks = [list(s_chunk) + list(m_chunk) for s_chunk, m_chunk in
                       zip(single_table_chunks, multi_table_chunks)]
        # Train fold is all keys without the test fold
        train_chunks = [list(set(self._dataset.keys).difference(test_chunk)) for test_chunk in test_chunks]

        return [{"train": train_chunk, "test": test_chunk} for train_chunk, test_chunk in
                zip(train_chunks, test_chunks)]

    def process_fold(self, fold: Dict[str, List], fold_num: int) -> float:
        """Evaluates on fold of the cross validation, returns the accuracy of the fold"""
        # Train multiple rounds
        weights_and_errors = [
            self.train(fold["train"], fold_num, i)
            for i in tqdm(range(self._weight_tuning_rounds), desc=f"Training Rounds of fold {fold_num}")
        ]
        # Average the training results weighted by their error
        weights = CrossValidationTraining.weighted_average(weights_and_errors)

        self.dump(
            f"fold_{fold_num}_weights.json",
            {"weights_and_errors": weights_and_errors, "weights": weights},
            subdir=f"fold_{fold_num}"
        )

        # Test accuracies on gold standard
        # Disable any noise
        self._label_region_loader.introduce_noise = False

        file_accuracies = {}
        for key in tqdm(fold["test"], desc=f"Test Set Validation of fold {fold_num}"):
            # Get ground truth data
            sheet_data = self._dataset.get_specific_sheetdata(key, self._label_region_loader)
            sheet_graph = SpreadSheetGraph(sheet_data)
            ground_truth = sheet_graph.get_table_definitions()

            # Evaluate the prediction
            rater = FitnessRater(weights)
            if len(sheet_graph.nodes) <= 10:
                accuracy = CrossValidationTraining.exhaustive_search_accuracy(ground_truth, sheet_graph, rater)
            else:
                accuracy = self.genetic_search_accuracy(ground_truth, sheet_graph, rater)
            file_accuracies[key] = accuracy

        # Average fold accuracies of test data
        fold_accuracy = sum(file_accuracies.values()) / len(file_accuracies.values())
        self.dump(
            f"fold_{fold_num}_file_accuracies.json",
            {"fold_file_accuracies": file_accuracies, "fold_accuracy": fold_accuracy},
            subdir=f"fold_{fold_num}",
        )
        return fold_accuracy

    @staticmethod
    def objective_function(weights: List[float], partitions: Dict[SpreadSheetGraph, List[List[bool]]],
                           rater: FitnessRater):
        """Objective function proposed by the paper used by the sqp optimizer"""
        # Update the weights
        rater.weights = weights
        # Calculate the score by summing target partition over alternative partitions scores
        score = 0
        for graph, alternative_toggle_lists in partitions.items():
            target_partition_part = 1 + rater.rate(graph, graph.edge_toggle_list)
            for alternative_toggle_list in alternative_toggle_lists:
                alternative_partition_part = 1 + rater.rate(graph, alternative_toggle_list)
                score += target_partition_part / alternative_partition_part
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
        graphs = [
            SpreadSheetGraph(self._dataset.get_specific_sheetdata(key, self._label_region_loader))
            for key in train_keys
        ]

        partitions = {}
        for graph in graphs:
            # Create more alternative partitions on multi table files (10 alternatives per table in file)
            partitions[graph] = CrossValidationTraining.generate_alternatives(graph, 10 * len(graph.get_components()))

        self.dump(
            f"fold_{fold_num}_training_round_{training_round}_input.json",
            dict([(str(graph.sheet_data), partitions) for graph, partitions in partitions.items()]),
            subdir=join(f"fold_{fold_num}", "training")
        )

        initial_weights = get_initial_weights()
        # Create rater object outside to leverage caching
        rater = FitnessRater(initial_weights)

        # Use SQP to minimize the obj. function
        res = minimize(
            CrossValidationTraining.objective_function,
            initial_weights,
            args=(partitions, rater),
            method="SLSQP",
            bounds=Bounds(0, 1000),
        )

        weights = list(res.x)
        rater.weights = weights

        # Calculate error rate components
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
    def exhaustive_search_accuracy(
            ground_truth: List[BoundingBox],
            sheet_graph: SpreadSheetGraph,
            rater: FitnessRater,
    ):
        """Runs an exhaustive search, evaluates the result against the ground truth, and returns the accuracy score"""
        search = ExhaustiveSearch(
            sheet_graph,
            rater,
        )
        result = search.run()
        return Analyser.accuracy_based_on_jacard_index(ground_truth, result.get_table_definitions())

    def genetic_search_accuracy(
            self,
            ground_truth: List[BoundingBox],
            sheet_graph: SpreadSheetGraph,
            rater: FitnessRater,
    ):
        """Runs genetic searches, evaluates the results against the ground truth, and returns the avg. accuracy score"""
        search = GeneticSearch(
            sheet_graph,
            rater,
            GeneticSearchConfiguration(
                sheet_graph,
                edge_mutation_probability_callback=self._edge_mutation_probability_callback,
            ),
        )

        # Genetic Search runs multiple times and gets averaged
        results = [search.run() for _ in range(self._search_rounds)]
        accuracies = [
            Analyser.accuracy_based_on_jacard_index(ground_truth, result.get_table_definitions())
            for result in results
        ]

        return sum(accuracies) / len(accuracies)

    @staticmethod
    def weighted_average(weights_and_errors: List[Dict[str, Union[List[float], float]]]) -> List[float]:
        """Averages the given weights based on the error rate for those weight"""

        # weights always refer to the machine learning weight vector and
        # contribution refers to the weights used in the weighted average
        total_err = sum([1 - e["error_rate"] for e in weights_and_errors])
        weights_and_contribution = [(e["weights"], (1 - e["error_rate"]) / total_err) for e in weights_and_errors]

        weight_vector = [0 for _ in range(len(weights_and_errors[0]["weights"]))]
        for weights, contribution in weights_and_contribution:
            weight_vector = [weight_vector[i] + weights[i] * contribution for i in range(len(weights))]
        return weight_vector

    def dump(self, file_name, data, subdir=""):
        """Dump given data to a json file"""
        if subdir != "":
            makedirs(join(self._out_path, subdir), exist_ok=True)

        with open(join(self._out_path, subdir, file_name), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
