"""Class which implements Metrics and Weight Training for Partition Evaluation"""
import logging
from itertools import chain
from typing import List

from openpyxl.utils import get_column_letter

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

    def avg_waec(self, component: GraphComponentData):
        x_lists = [lr.get_all_x() for lr in component.label_regions]
        # All columns that are covered by at least on label region in our component
        x_s = set(list(chain(*x_lists)))
        # The Columns most left and most right in our component can not be empty
        # otherwise the component would be smaller
        # This means all columns in the components bounding box without x_s are all empty columns
        empty_columns = set(component.bounding_box.get_all_x()) - x_s
        # Group adj empty columns
        c_emt = []
        group = []
        for col_index in sorted(empty_columns):
            if len(group) == 0:
                group = [col_index]
                continue
            if col_index - 1 != group[-1]:
                # column not left adj of last col in current group
                c_emt.append(group)
                group = [col_index]

            group.append(col_index)

        if len(c_emt) == 0:
            # Assumption: The metric lacks handling of missing empty columns, which would lead to division by zero
            # We will return 0 (the best possible score) if there are no empty columns
            return 0

        # Groups not necessary for total width of empty columns
        total_width = 0
        for empty_column in empty_columns:
            # TODO: This might die because empty column starts at 0, and has to be incremented by 1
            total_width += component.graph.sheet.column_dimensions[get_column_letter(empty_column)].width

        return total_width / len(c_emt)

    def avg_waer(self, component: GraphComponentData):
        y_lists = [lr.get_all_y() for lr in component.label_regions]
        # All columns that are covered by at least on label region in our component
        y_s = set(list(chain(*y_lists)))
        # The Columns most left and most right in our component can not be empty
        # otherwise the component would be smaller
        # This means all columns in the components bounding box without x_s are all empty columns
        empty_rows = set(component.bounding_box.get_all_y()) - y_s
        # Group adj empty columns
        r_emt = []
        group = []
        for row_index in sorted(empty_rows):
            if len(group) == 0:
                group = [row_index]
                continue
            if row_index - 1 != group[-1]:
                # column not left adj of last col in current group
                r_emt.append(group)
                group = [row_index]

            group.append(row_index)

        if len(r_emt) == 0:
            # Assumption: The metric lacks handling of missing empty rows, which would lead to division by zero
            # We will return 0 (the best possible score) if there are no empty rows
            return 0

        # Groups not necessary for total height of empty columns
        total_height = 0
        for empty_row in empty_rows:
            # TODO: This might die because empty row starts at 0, and has to be incremented by 1
            total_height += component.graph.sheet.row_dimensions[empty_row].height
        return total_height / len(r_emt)

    def ovr(self, components: List[GraphComponentData]):
        # Warning: This metric is really weird, as they use
        # len(cols_of_all_lrs) * len(rows_of_all_lrs) of all divisor, which does not make sense to me
        overlap = 0
        cols_of_all_lrs = set()
        rows_of_all_lrs = set()
        for i in range(len(components)):
            c_i = set(components[i].bounding_box.get_all_x())
            cols_of_all_lrs = cols_of_all_lrs.union(c_i)
            r_i = set(components[i].bounding_box.get_all_y())
            rows_of_all_lrs = rows_of_all_lrs.union(r_i)
            for j in range(len(components)):
                if j <= i:
                    continue
                c_j = components[j].bounding_box.get_all_x()
                r_j = components[j].bounding_box.get_all_y()

                overlap += len(c_i.intersection(c_j)) * len(r_i.intersection(r_j))
        return overlap / (len(cols_of_all_lrs) * len(rows_of_all_lrs))


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
