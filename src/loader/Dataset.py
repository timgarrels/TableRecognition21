import json
import logging
from functools import cached_property
from os.path import join
from typing import Generator, List

from openpyxl import load_workbook

from labelregions.LabelRegionLoader import LabelRegionLoader
from loader.DataPreprocessor import DataPreprocessor
from loader.SheetData import SheetData

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# TODO: Investigate, what is running so long with huge files, and think to either remove or document skipping of huge files!
# TODO: Investigate, which files contribute with the extremely worse precision
# TODO: Improve logging of skipped wb & sheets, so the reasons are transparent, uniformly logged and in the same place, maybe introduce custom exceptions for that

class Dataset(object):
    def __init__(self, path, name, label_region_loader: LabelRegionLoader,
                 annotations_file_name="preprocessed_annotations_elements.json"):
        self.path = path
        self.name = name
        self.label_region_loader = label_region_loader
        self.annotations_file_name = annotations_file_name

    @cached_property
    def _annotations(self):
        annotation_file = join(self.path, self.annotations_file_name)
        with open(annotation_file) as f:
            data = f.read()
        return json.loads(data)

    @property
    def multi_table_keys(self):
        return [key for key, value in self._annotations.items() if value["n_regions"] > 1]

    @property
    def single_table_keys(self):
        return [key for key, value in self._annotations.items() if value["n_regions"] == 1]

    @property
    def keys(self):
        return self._annotations.keys()

    def sheet_data_count(self, exceptions: List[str] = None):
        if exceptions is None:
            exceptions = []
        return len(set(self._annotations.keys()).difference(exceptions))

    def get_sheet_data(self, exceptions: List[str] = None) -> Generator[SheetData, None, None]:
        """Generator for all Sheet Data Objects"""
        for key in self._annotations.keys():
            if key in exceptions:
                continue
            yield self.get_specific_sheetdata(key)

    def get_specific_sheetdata(self, key: str) -> SheetData:
        xls_file_name, sheet_name = DataPreprocessor.split_annotation_key(key)
        xls_file_path = join(self.path, "xls", xls_file_name)
        wb = load_workbook(xls_file_path)
        wb.path = xls_file_path  # Path is wrongly defaulted to /xl/workbook.xml
        ws = wb[sheet_name]

        sheet_annotations = self._annotations[key]
        label_regions, table_definitions = self.label_region_loader.load_label_regions_and_table_definitions(
            ws,
            sheet_annotations,
        )
        return SheetData(ws, label_regions, table_definitions)

    def summarize(self):
        """Summarizes Dataset Annotations"""
        data = self._annotations

        analytical_data = {}
        for sheet, sheetdata in data.items():
            analytical_data[sheet] = {
                "table_count": 0,
            }
            for region in sheetdata["regions"]:
                if region["region_type"] == "Table":
                    analytical_data[sheet]["table_count"] += 1

        print(f"Total Sheets: {len(analytical_data.keys())}")
        print(
            f"Single Table Sheets: {len([sheet for sheet, analytical_sheetdata in analytical_data.items() if analytical_sheetdata['table_count'] == 1])}")
        print(
            f"Multi Table Sheets: {len([sheet for sheet, analytical_sheetdata in analytical_data.items() if analytical_sheetdata['table_count'] > 1])}")

        print(f"Total Annotatd Tables: {sum([data['table_count'] for data in analytical_data.values()])}")

    def __str__(self):
        return f"Dataset: {self.name}"
