"""k-fold cross validation with multiple weight tuning and genetic search rounds.
Weights and Accuracy are averaged.
Accuracy is measured as jacard-index >= 0.9"""

from os.path import join
from statistics import mean
from typing import List, Dict, Union, Tuple

from scipy.optimize import minimize, Bounds
from tqdm import tqdm

from experiments.CrossValidationTraining import CrossValidationTraining
from graph.SpreadSheetGraph import SpreadSheetGraph
from search.FitnessRater import get_initial_weights
from search.ImprovedFitnessRater import ImprovedFitnessRater


class ImprovedCrossValidationTraining(CrossValidationTraining):

    def get_density_means(self, keys: List[str]) -> Tuple[float, float]:
        single_table_file_densities = []
        multi_table_file_densities = []
        for key in keys:
            graph = SpreadSheetGraph(self._dataset.get_specific_sheetdata(key, self._label_region_loader))
            density = (2 * len(graph.edge_list) / (len(graph.nodes) * (len(graph.nodes) - 1)))
            if len(graph.get_components()) == 1:
                single_table_file_densities.append(density)
            else:
                multi_table_file_densities.append(density)
        return mean(single_table_file_densities), mean(multi_table_file_densities)

    def process_fold(self, fold: Dict[str, List], fold_num: int) -> float:
        """Evaluates on fold of the cross validation, returns the accuracy of the fold"""
        # Train multiple rounds
        weights_and_errors = [
            self.train(fold["train"], fold_num, i)
            for i in tqdm(range(self._weight_tuning_rounds), desc=f"Training Rounds of fold {fold_num}")
        ]
        weights = CrossValidationTraining.weighted_average(weights_and_errors)

        self.dump(
            f"fold_{fold_num}_weights.json",
            {"weights_and_errors": weights_and_errors, "weights": weights},
            subdir=f"fold_{fold_num}"
        )

        # Test accuracies on gold standard
        # Disable any noise
        self._label_region_loader.introduce_noise = False

        single_table_density_mean, multi_table_density_mean = self.get_density_means(fold["test"])
        file_accuracies = {}
        for key in tqdm(fold["test"], desc=f"Test Set Validation of fold {fold_num}"):
            sheet_data = self._dataset.get_specific_sheetdata(key, self._label_region_loader)
            sheet_graph = SpreadSheetGraph(sheet_data)
            ground_truth = sheet_graph.get_table_definitions()
            rater = ImprovedFitnessRater(weights, single_table_density_mean, multi_table_density_mean)
            if len(sheet_graph.nodes) <= 10:
                accuracy = CrossValidationTraining.exhaustive_search_accuracy(ground_truth, sheet_graph, rater)
            else:
                accuracy = self.genetic_search_accuracy(ground_truth, sheet_graph, rater)
            file_accuracies[key] = accuracy

        fold_accuracy = sum(file_accuracies.values()) / len(file_accuracies.values())
        self.dump(
            f"fold_{fold_num}_file_accuracies.json",
            {"fold_file_accuracies": file_accuracies, "fold_accuracy": fold_accuracy},
            subdir=f"fold_{fold_num}",
        )
        return fold_accuracy

    def train(self, train_keys: List[str], fold_num: int, training_round: int) -> Dict[str, Union[List[float], float]]:
        """Performs SQP on the given keys, outputs the resulting weights and their error rate"""
        graphs = [
            SpreadSheetGraph(self._dataset.get_specific_sheetdata(key, self._label_region_loader))
            for key in train_keys
        ]

        partitions = {}
        for graph in graphs:
            partitions[graph] = CrossValidationTraining.generate_alternatives(graph, 10 * len(graph.get_components()))

        self.dump(
            f"fold_{fold_num}_training_round_{training_round}_input.json",
            dict([(str(graph.sheet_data), partitions) for graph, partitions in partitions.items()]),
            subdir=join(f"fold_{fold_num}", "training")
        )

        initial_weights = get_initial_weights() + [1, 1]  # Add two weights for the two extra density scores
        single_table_density_mean, multi_table_density_mean = self.get_density_means(train_keys)
        # Create rater object outside to leverage caching
        rater = ImprovedFitnessRater(initial_weights, single_table_density_mean, multi_table_density_mean)

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
