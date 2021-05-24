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
    def ndar(self, graph: SpreadSheetGraph) -> float:
        pass

    def nhar(self, graph: SpreadSheetGraph) -> float:
        pass

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
            score = len(component.header_groups)
            scores_per_component.append(score)
            logger.debug(f"Component {[n.id for n in component.label_regions]} has the following header groups")
            for hg in component.header_groups:
                logger.debug(f"\t {[n.id for n in hg]}")

        return sum(scores_per_component) + len(components)
