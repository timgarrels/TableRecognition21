"""Class to represent a Graph Component, used to get attributes/data and cache them"""
import logging
from typing import List

from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.BoundingBox import BoundingBox
from labelregions.LabelRegion import LabelRegion
from labelregions.LabelRegionType import LabelRegionType

logger = logging.getLogger(__name__)


# logger.setLevel(logging.DEBUG)


class GraphComponentData(object):
    def __init__(self, label_regions: List[LabelRegion], graph: SpreadSheetGraph):
        self.label_regions: List[LabelRegion] = label_regions
        self.graph: SpreadSheetGraph = graph

        self._area = None
        self._data = None
        self._heads = None
        self._bounding_box = None
        self._rows = None
        self._cols = None
        self._header_groups = None
        self._header_top = None
        self._header_top_row = None
        self._c_ht = None
        self._c_d = None

    @property
    def bounding_box(self) -> BoundingBox:
        """Returns the minimum bounding box of this component"""
        if self._bounding_box is None:
            tops = [label_region.top for label_region in self.label_regions]
            lefts = [label_region.left for label_region in self.label_regions]
            bottoms = [label_region.bottom for label_region in self.label_regions]
            rights = [label_region.right for label_region in self.label_regions]

            min_x = min(tops)
            min_y = min(lefts)
            max_x = max(bottoms)
            max_y = max(rights)
            self._bounding_box = BoundingBox(min_x, min_y, max_x, max_y)
        return self._bounding_box

    @property
    def data(self) -> List[LabelRegion]:
        """Returns all data label regions"""
        if self._data is None:
            self._data = [label_region for label_region in self.label_regions if
                          label_region.type == LabelRegionType.DATA]
        return self._data

    @property
    def heads(self) -> List[LabelRegion]:
        """Returns all header label regions"""
        if self._heads is None:
            self._heads = [label_region for label_region in self.label_regions if
                           label_region.type == LabelRegionType.HEADER]
        return self._heads

    def area(self, label_region: LabelRegion) -> int:
        """Returns the number of cells in the given label region"""
        if self._area is None:
            self._area = {}
        if self._area.get(label_region, None) is None:
            x = len(range(label_region.top, label_region.bottom + 1))
            y = len(range(label_region.left, label_region.right + 1))
            self._area[label_region] = x * y
        return self._area[label_region]

    def rows(self, label_region: LabelRegion) -> List[int]:
        """Returns the row indices within the given label region"""
        if self._rows is None:
            self._rows = {}
        if self._rows.get(label_region, None) is None:
            self._rows[label_region] = label_region.get_all_x()
        return self._rows[label_region]

    def cols(self, label_region: LabelRegion) -> List[int]:
        """Returns the column indices within the given label region"""
        if self._cols is None:
            self._cols = {}
        if self._cols.get(label_region, None) is None:
            self._rows[label_region] = label_region.get_all_y()
        return self._cols[label_region]

    @property
    def header_groups(self):
        logger.debug(f"Searching header groups for component {sorted([n.id for n in self.label_regions])}")
        if len(self.heads) == 0:
            return []

        if self._header_groups is None:
            def belong_to_same_group(header1: LabelRegion, header2: LabelRegion):
                edges = self.graph.node_edges_lookup[header1]
                # Filter for edges connecting h1 and h2
                edges_h1_h2 = [edge for edge in edges if edge.source == header2 or edge.destination == header2]
                if (len(edges_h1_h2)) == 0:
                    # No edge connecting h1 and h2
                    return False

                # There can only be one edge between two nodes
                edge = edges_h1_h2[0]
                # Check whether there is a "blocking" data row in between
                # The box containing all rows/cols between both headers
                # but spanning only common indices
                alignment_bounding_box = edge.get_alignment_bounding_box()
                for data_lr in self.data:
                    if alignment_bounding_box.intersect(data_lr):
                        return False
                return True

            def belongs_to_group(group: List[LabelRegion], header: LabelRegion):
                belongs = [belong_to_same_group(h, header) for h in group]
                return any(belongs)

            # BFS
            grouped_lrs = []
            groups = []
            header_top = [self.heads[0]]
            header_top_lowest_row_index = self.heads[0].top
            for header in self.heads:
                if header in grouped_lrs:
                    continue
                logger.debug(f"Finding groups for {header.id}")
                group: List[LabelRegion] = [header]
                group_lowest_row = header.top
                grouped_lrs.append(header)
                neighbours = self.graph.get_neighbours(header)

                logger.debug(f"Direct neighbours:  {sorted([n.id for n in neighbours])}")
                # Filter for only header neighbours that are in this component
                header_neighbours = [
                    n for n in neighbours if n.type == LabelRegionType.HEADER and n in self.label_regions
                ]
                logger.debug(f"Direct filtered neighbours:  {sorted([n.id for n in header_neighbours])}")

                while len(header_neighbours) > 0:
                    hn = header_neighbours.pop(0)
                    if hn in grouped_lrs:
                        continue
                    if belongs_to_group(group, hn):
                        logger.debug(f"\t{hn.id} belongs to same group!")
                        group.append(hn)
                        if hn.top < group_lowest_row:
                            group_lowest_row = hn.top
                        neighbours = self.graph.get_neighbours(hn)
                        header_neighbours.extend([
                            n for n in neighbours if
                            n.type == LabelRegionType.HEADER and n in self.label_regions and n not in grouped_lrs
                        ])
                        logger.debug(f"\tIndirect neighbours:  {set(sorted([n.id for n in header_neighbours]))}")
                        grouped_lrs.append(hn)
                groups.append(group)
                if group_lowest_row <= header_top_lowest_row_index:
                    header_top_lowest_row_index = group_lowest_row
                    header_top = group

            self._header_groups = groups
            self._header_top = header_top
            self._header_top_row = header_top_lowest_row_index
        return self._header_groups

    @property
    def header_top(self) -> List[LabelRegion]:
        if len(self.heads) == 0:
            return []
        if self._header_top is None:
            # Generation of header groups also initializes header top
            _ = self.header_groups
        return self._header_top

    @property
    def header_top_row(self):
        if len(self.heads) == 0:
            raise ValueError("There are no headers in this component, unable to calculate highest header group row")
        if self._header_top_row is None:
            # Generation of header groups also initializes header top row
            _ = self.header_groups
        return self._header_top_row

    @property
    def avg_waec(self):
        # Assumption: "adjacent empty columns" are just all empty columns in our partition
        bounds = self.bounding_box
        min_x = bounds.left
        max_x = bounds.right
        empty_cols = []
        for col in self.graph.sheet.iter_cols(min_col=min_x, max_col=max_x, values_only=True):
            # TODO: Implement
            return 1

    @property
    def c_ht(self):
        if self._c_ht is None:
            self._c_ht = set([lr.get_all_x() for lr in self.header_top])
        return self._c_ht

    @property
    def c_d(self):
        if self._c_d is None:
            self._c_d = set([lr.get_all_x() for lr in self.data])
        return self._c_d
