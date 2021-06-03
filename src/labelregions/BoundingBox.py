from __future__ import annotations  # Necessary so class can refer to its own type in itself

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
        # TODO: Can be done smarter and more performant by top_left bottom_right comparison
        x_overlap = set(self.get_all_x()).intersection(box.get_all_x())
        y_overlap = set(self.get_all_y()).intersection(box.get_all_y())
        if len(x_overlap) > 0 and len(y_overlap) > 0:
            return True
        return False

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
