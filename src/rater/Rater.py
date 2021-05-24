"""Class which implements Metrics and Weight Training for Partition Evaluation"""
import logging
from typing import List

from graph.GraphComponentData import GraphComponentData
from graph.SpreadSheetGraph import SpreadSheetGraph

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


# TODO: Implement metrics (how to access cell data? via graph?)
# TODO: Implement weight training
class Rater(object):
    def ndar(self, component: GraphComponentData) -> float:
        c_ht = set([lr.get_all_x() for lr in component.header_top])
        c_d = set([lr.get_all_x() for lr in component.data])
        if len(c_d) < 1 or len(c_ht) < 1:
            return 0
        return 1 - len(c_d.intersection(c_ht)) / len(c_d)

    def nhar(self, component: GraphComponentData) -> float:
        c_ht = set([lr.get_all_x() for lr in component.header_top])
        c_d = set([lr.get_all_x() for lr in component.data])
        if len(c_d) < 1 or len(c_ht) < 1:
            return 0
        return 1 - len(c_d.intersection(c_ht)) / len(c_ht)

    def rate(self, graph: SpreadSheetGraph, edge_toggle_list: List[bool]) -> float:
        """Rates a graph based on a edge toggle list"""
        # Create graph copy and let it represent the partition
        new_graph = graph
        new_graph.edge_toggle_list = edge_toggle_list
        components = [GraphComponentData(c, graph) for c in graph.get_components()]

        scores_per_component = []

        for component in components:
            # TODO: implement
            logger.debug("Rating Mock!")
            if component.heads:
                score = component.header_top_row
            else:
                score = -100
            scores_per_component.append(score)

        return sum(scores_per_component)
