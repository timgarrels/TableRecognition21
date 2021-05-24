from __future__ import annotations  # Necessary so class can refer to its own type in itself


class BoundingBox(object):
    def __init__(self, top: int, left: int, bottom: int, right: int):
        self.top: int = top
        self.left: int = left
        self.bottom: int = bottom
        self.right: int = right

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
