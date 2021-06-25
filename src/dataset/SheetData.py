"""Object containing a Worksheet Object, Label Regions and the Table Definition Ground Truth and the """
from os.path import basename
from typing import List

from openpyxl.worksheet.worksheet import Worksheet

from labelregions.BoundingBox import BoundingBox
from labelregions.LabelRegion import LabelRegion


class SheetData(object):
    def __init__(self, worksheet: Worksheet, label_regions: List[LabelRegion], table_definitions: List[BoundingBox]):
        self.worksheet = worksheet
        self.label_regions = label_regions
        self.table_definitions = table_definitions

    @property
    def annotation_key(self):
        return f"{basename(self.parent_path)}_{self.worksheet.title}.csv"

    @property
    def parent_path(self):
        return self.worksheet.parent.path

    def __str__(self):
        return f"Sheetdata({self.worksheet.title} of {self.parent_path}"
