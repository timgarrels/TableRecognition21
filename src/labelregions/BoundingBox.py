from __future__ import annotations  # Necessary so class can refer to its own type in itself

from itertools import product
from typing import List


class BoundingBox(object):
    def __init__(self, top: int, left: int, bottom: int, right: int):
        self.top: int = top
        self.left: int = left
        self.bottom: int = bottom
        self.right: int = right

    @property
    def area(self):
        return (self.right + 1 - self.left) * (self.bottom + 1 - self.top)

    def intersect(self, box: BoundingBox):
        """Returns whether two bounding boxes intersect"""
        return len(self.intersection(box)) > 0

    def intersection(self, box: BoundingBox):
        """Returns the cells that are present in both this and the given box"""
        return set(self.cells()).intersection(box.cells())

    def cells(self):
        return list(product(self.get_all_x(), self.get_all_y()))

    def get_all_x(self):
        return [x for x in range(self.left, self.right + 1)]

    def get_all_y(self):
        return [y for y in range(self.top, self.bottom + 1)]

    @staticmethod
    def merge(bounding_boxes: List[BoundingBox]):
        """Creates the minimal bounding box containing all bounding boxes"""
        tops = [bb.top for bb in bounding_boxes]
        lefts = [bb.left for bb in bounding_boxes]
        bottoms = [bb.bottom for bb in bounding_boxes]
        rights = [bb.right for bb in bounding_boxes]

        min_x = min(tops)
        min_y = min(lefts)
        max_x = max(bottoms)
        max_y = max(rights)
        return BoundingBox(min_x, min_y, max_x, max_y)

    def __dict__(self):
        return {
            "top": self.top,
            "left": self.left,
            "bottom": self.bottom,
            "right": self.left,
        }
