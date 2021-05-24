"""Class which implements Metrics and Weight Training for Partition Evaluation"""
import logging
from itertools import chain
from typing import List

from graph.GraphComponentData import GraphComponentData
from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.BoundingBox import BoundingBox

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


# TODO: Implement metrics (how to access cell data? via graph?)
# TODO: Implement weight training
class Rater(object):
    def ndar(self, component: GraphComponentData) -> float:
        if len(component.c_d) < 1 or len(component.c_ht) < 1:
            return 0
        return 1 - len(component.c_d.intersection(component.c_ht)) / len(component.c_d)

    def nhar(self, component: GraphComponentData) -> float:
        if len(component.c_d) < 1 or len(component.c_ht) < 1:
            return 0
        return 1 - len(component.c_d.intersection(component.c_ht)) / len(component.c_ht)

    def dp(self, component: GraphComponentData):
        if len(component.heads) == 0 and len(component.data) >= 1:
            return 1
        return 0

    def hp(self, component: GraphComponentData):
        if len(component.data) == 0 and len(component.heads) >= 1:
            return 1
        return 0

    def ioc(self, component: GraphComponentData):
        if (
                len(component.c_d) == 1 and
                len(component.c_ht) == 1 and
                len(component.c_d.intersection(component.c_ht)) == 1
        ):
            return 1
        return 0

    def ovh(self, component: GraphComponentData):
        ovh = []
        for header_group in component.header_groups:
            if header_group == component.header_top:
                # We are looking for other valid header groups than header top
                continue
            x_lists = [lr.get_all_x() for lr in header_group]
            x_s = set(list(chain(*x_lists)))
            if len(x_s) >= 2:
                ovh.append(header_group)
        return len(ovh)

    def dahr(self, component: GraphComponentData):
        # Data label regions that are to some degree above the header top row
        data_above_top_header = [data_lr for data_lr in component.data if data_lr.top < component.header_top_row]
        total_area_above_top_header = 0
        for data_lr in data_above_top_header:
            box_above_top_header = BoundingBox(data_lr.top, data_lr.left, component.header_top_row, data_lr.right)
            total_area_above_top_header += box_above_top_header.area
        total_area = 0
        for data_lr in component.data:
            total_area += data_lr.area
        return total_area_above_top_header / total_area

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
