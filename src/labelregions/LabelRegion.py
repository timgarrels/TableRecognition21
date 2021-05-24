from labelregions.BoundingBox import BoundingBox
from labelregions.LabelRegionType import LabelRegionType


class LabelRegion(BoundingBox):
    def __init__(self, lr_id: int, lr_type: LabelRegionType, top: int, left: int, bottom: int, right: int):
        self.id = lr_id
        self.type = lr_type
        super().__init__(top, left, bottom, right)

    @staticmethod
    def from_bounding_box(lr_id: int, lr_type: LabelRegionType, box: BoundingBox):
        return LabelRegion(lr_id, lr_type, box.top, box.left, box.bottom, box.right)

    def __str__(self):
        return str(self.id)
