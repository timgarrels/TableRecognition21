from enum import Enum
from typing import List

from labelregions.BoundingBox import BoundingBox
from labelregions.LabelRegion import LabelRegion
from labelregions.LabelRegionType import LabelRegionType


class AlignmentType(Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


class ConnectionType(Enum):
    D_D = "D_D"
    D_H = "D_H"
    H_H = "H_H"


class Edge(object):
    def __init__(self, source: LabelRegion, destination: LabelRegion, aligned_indices: List[int],
                 alignment_type: AlignmentType):
        self.source = source
        self.destination = destination
        self.aligned_indices = aligned_indices
        self.alignment_type = alignment_type

        self.length = source.distance(destination)

        self.connection_type = ConnectionType.D_H
        if self.source.type == self.destination.type:
            if self.source.type == LabelRegionType.HEADER:
                self.connection_type = ConnectionType.H_H
            else:
                self.connection_type = ConnectionType.D_D

    def get_alignment_bounding_box(self) -> BoundingBox:
        """Returns the bounding box between source and dest
        containing only shared indices"""
        if self.alignment_type == AlignmentType.VERTICAL:
            # Vertical Alignment
            # Indices are col indices
            left = min(self.aligned_indices)
            right = max(self.aligned_indices)
            # The lower index bottom is the bounding box top
            # The higher index top is the bounding box bottom
            top = min(self.source.bottom, self.destination.bottom)
            bottom = max(self.source.top, self.destination.top)
        else:
            # Horizontal Alignment
            # Indices are row indices
            top = min(self.aligned_indices)
            bottom = max(self.aligned_indices)
            # The lower index right is the bounding box left
            # The higher index left is the bounding box right
            left = min(self.source.right, self.destination.right)
            right = max(self.source.left, self.destination.left)
        return BoundingBox(top, left, bottom, right)

    def __str__(self):
        return f"E-{self.source}-{self.destination}"
