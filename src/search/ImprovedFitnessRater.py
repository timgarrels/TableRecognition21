"""Class which implements Metrics and Weight Training for Partition Evaluation"""
import logging
from typing import List

from graph.Edge import ConnectionType
from graph.GraphComponentData import GraphComponentData
from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.LabelRegionType import LabelRegionType
from search.FitnessRater import FitnessRater, COMPONENT_BASED_METRICS, PARTITION_BASED_METRICS

logger = logging.getLogger(__name__)


# logger.setLevel(logging.DEBUG)


class ImprovedFitnessRater(FitnessRater):
    def __init__(
            self,
            weights: List[float],
            degree_avg_cut_median: float
    ):

        self.degree_avg_cut_median = degree_avg_cut_median

        super().__init__(weights)

    @staticmethod
    def correct_weight_length():
        return len(COMPONENT_BASED_METRICS) + len(PARTITION_BASED_METRICS) + 1

    @staticmethod
    def header_lrs(graph):
        return list(filter(lambda x: x.type == LabelRegionType.HEADER, graph.nodes))

    @staticmethod
    def data_lrs(graph):
        return list(filter(lambda x: x.type == LabelRegionType.DATA, graph.nodes))

    @staticmethod
    def degree_avg_cut(graph):
        d_d = [edge for edge in graph.edge_list if edge.connection_type == ConnectionType.D_D]
        h_h = [edge for edge in graph.edge_list if edge.connection_type == ConnectionType.H_H]

        try:
            d_d_degree_avg = len(d_d) / len(ImprovedFitnessRater.data_lrs(graph))
        except ZeroDivisionError:
            d_d_degree_avg = 0
        try:
            h_h_degree_avg = len(h_h) / len(ImprovedFitnessRater.header_lrs(graph))
        except ZeroDivisionError:
            h_h_degree_avg = 0
        return d_d_degree_avg * h_h_degree_avg

    def multi_table_prediction_score(self, graph: SpreadSheetGraph) -> float:
        degree_avg_cut = ImprovedFitnessRater.degree_avg_cut(graph)
        likely_multi_table = degree_avg_cut <= self.degree_avg_cut_median

        is_multi_table = len(graph.get_components()) > 1
        # Punish if the prediction is different from the density heuristic
        return is_multi_table and not likely_multi_table

    def rate(self, graph: SpreadSheetGraph, edge_toggle_list: List[bool]) -> float:
        """Rates a graph based on a edge toggle list"""
        # Create graph copy and let it represent the partition

        old_toggle_list = graph.edge_toggle_list
        graph.edge_toggle_list = edge_toggle_list
        components = [GraphComponentData(c, graph) for c in graph.get_components()]

        degree_avg_cut_score = self.multi_table_prediction_score(graph)

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
                degree_avg_cut_score * self.weights[-1]
        )
