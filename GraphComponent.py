"""Class to represent a Graph Component, used to get attributes/data and cache them"""

from typing import List

from BoundingBox import BoundingBox
from LabelRegion import LabelRegion
from LabelRegionType import LabelRegionType


class GraphComponent(object):
    def __init__(self, label_regions: List[LabelRegion]):
        self.label_regions = label_regions

        self._area = None
        self._data = None
        self._heads = None
        self._bounding_box = None
        self._rows = None
        self._cols = None
        self._header_groups = None

    @property
    def bounding_box(self):
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
    def data(self):
        """Returns all data label regions"""
        if self._data is None:
            self._data = [label_region for label_region in self.label_regions if
                          label_region.type == LabelRegionType.DATA]
        return self._data

    @property
    def heads(self):
        """Returns all header label regions"""
        if self._heads is None:
            self._heads = [label_region for label_region in self.label_regions if
                           label_region.type == LabelRegionType.HEADER]
        return self._heads

    def area(self, label_region: LabelRegion):
        """Returns the number of cells in the given label region"""
        if self._area is None:
            self._area = {}
        if self._area.get(label_region, None) is None:
            x = len(range(label_region.top, label_region.bottom + 1))
            y = len(range(label_region.left, label_region.right + 1))
            self._area[label_region] = x * y
        return self._area[label_region]

    def rows(self, label_region: LabelRegion):
        """Returns the row indices within the given label region"""
        if self._rows is None:
            self._rows = {}
        if self._rows.get(label_region, None) is None:
            self._rows[label_region] = label_region.get_all_x()
        return self._rows[label_region]

    def cols(self, label_region: LabelRegion):
        """Returns the column indices within the given label region"""
        if self._cols is None:
            self._cols = {}
        if self._cols.get(label_region, None) is None:
            self._rows[label_region] = label_region.get_all_y()
        return self._cols[label_region]

    @property
    def header_groups(self):
        if self._header_groups is None:
            def belong_to_same_group(header1, header2):
                edges = self.graph.node_edges_lookup[header1]
                edge = [edge for edge in edges if edge["source"] == header2 or edge["dest"] == header2]
                if (len(edge)) == 0:
                    # No edge in between
                    return False

                edge = edge[0]
                # Check whether there is a "blocking" data row in between
                # The box containing all rows/cols between both headers
                # but spanning only common indices
                alignment_bounding_box = get_alignment_bounding_box(edge)
                for data_lr in self.data:
                    if bounding_box_intersect(alignment_bounding_box, data_lr):
                        return False
                return True

            # BFS
            grouped = []
            groups = []
            for header in self.heads:
                group = [header]
                neighbours = self.graph.get_neighbours(header)
                header_neighbours = [n for n in neighbours if self.graph.nodes[n]["type"] == "Header"]
                while len(header_neighbours) > 0:
                    hn = header_neighbours.pop(0)
                    if hn in grouped:
                        continue
                    if belong_to_same_group(header, hn):
                        group.append(hn)
                        neighbours = self.graph.get_neighbours(hn)
                        header_neighbours.extend([n for n in neighbours if self.graph.nodes[n]["type"] == "Header"])
                        grouped.append(hn)
                groups.append(group)
            self._header_groups = groups
        return self._header_groups

    @property
    def avg_waec(self):
        # Assumption: "adjacent empty columns" are just all empty columns in our partition
        bounds = self.bounding_box
        min_x = bounds["top_left"][0]
        max_x = bounds["bottom_right"][0]
        empty_cols = []
        for col in self.graph.ws.iter_cols(min_col=min_x, max_col=max_x, values_only=True):
            # TODO: Implement
            return 1
