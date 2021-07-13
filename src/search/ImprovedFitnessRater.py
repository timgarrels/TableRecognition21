"""Class which implements Metrics and Weight Training for Partition Evaluation"""
import logging
from typing import List

from graph.GraphComponentData import GraphComponentData
from graph.SpreadSheetGraph import SpreadSheetGraph
from search.FitnessRater import FitnessRater, COMPONENT_BASED_METRICS, PARTITION_BASED_METRICS

logger = logging.getLogger(__name__)


# logger.setLevel(logging.DEBUG)


class ImprovedFitnessRater(FitnessRater):
    def __init__(
            self,
            weights: List[float],
            single_table_file_mean_density: float,
            multi_table_file_mean_density: float,
    ):

        self.single_table_file_mean_density = single_table_file_mean_density
        self.multi_table_file_mean_density = multi_table_file_mean_density

        super().__init__(weights)

    @staticmethod
    def correct_weight_length():
        return len(COMPONENT_BASED_METRICS) + len(PARTITION_BASED_METRICS) + 2

    def multi_table_density_score(self, graph: SpreadSheetGraph) -> float:
        density = (2 * len(graph.edge_list) / (len(graph.nodes) * (len(graph.nodes) - 1)))
        likely_multi_table = density < self.multi_table_file_mean_density
        is_multi_table = len(graph.get_components()) > 1
        # Punish if the prediction is different from the density heuristic
        return is_multi_table and not likely_multi_table

    def single_table_density_score(self, graph: SpreadSheetGraph) -> float:
        density = (2 * len(graph.edge_list) / (len(graph.nodes) * (len(graph.nodes) - 1)))
        likely_single_table = density > self.single_table_file_mean_density
        if not likely_single_table:
            return 0
        # Likely to be a single table, return table count -1 as punishment
        return len(graph.get_components()) - 1

    def rate(self, graph: SpreadSheetGraph, edge_toggle_list: List[bool]) -> float:
        """Rates a graph based on a edge toggle list"""
        # Create graph copy and let it represent the partition

        old_toggle_list = graph.edge_toggle_list
        graph.edge_toggle_list = edge_toggle_list
        components = [GraphComponentData(c, graph) for c in graph.get_components()]

        single_table_density_score = self.single_table_density_score(graph)
        multi_table_density_score = self.multi_table_density_score(graph)

        graph.edge_toggle_list = old_toggle_list

        scores_per_component = []
        for component in components:
            score = 0
            for i, metric in enumerate(COMPONENT_BASED_METRICS):
                metric_score = self.get_from_component_cache(graph.sheet, component, metric)
                score += metric_score * self.weights[i]
            scores_per_component.append(score)

        scores_per_partition = []
        for j, metric in enumerate(PARTITION_BASED_METRICS):
            metric_score = self.get_from_partition_cache(graph.sheet, components, metric)
            score = metric_score * self.weights[len(COMPONENT_BASED_METRICS) - 1 + j]
            scores_per_partition.append(score)

        return (
                sum(scores_per_component) +
                sum(scores_per_partition) +
                single_table_density_score * self.weights[-2] +
                multi_table_density_score * self.weights[-1]
        )
