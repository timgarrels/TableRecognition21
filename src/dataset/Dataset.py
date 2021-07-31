"""Representation and Utility of a Spreadsheet Corpus"""

import json
import logging
from functools import cached_property
from os.path import join
from typing import Generator, List

from openpyxl import load_workbook

from dataset.DataPreprocessor import DataPreprocessor
from dataset.SheetData import SheetData
from labelregions.LabelRegionLoader import LabelRegionLoader

logger = logging.getLogger(__name__)


class Dataset(object):
    def __init__(
            self,
            path,
            name,
            # Uses preprocessed annotation elements per default. Parameterize with annotations_elements.json to use raw
            annotations_file_name="preprocessed_annotations_elements.json",
    ):
        self.path = path
        self.name = name
        self.annotations_file_name = annotations_file_name

    @cached_property
    def _annotations(self):
        """Load the annotation json"""
        annotation_file = join(self.path, self.annotations_file_name)
        with open(annotation_file) as f:
            data = f.read()
        return json.loads(data)

    @property
    def multi_table_keys(self):
        """Get all file keys with more than one table"""
        return [key for key, value in self._annotations.items() if value["n_regions"] > 1]

    @property
    def single_table_keys(self):
        """Get all file keys with exactly one table"""
        return [key for key, value in self._annotations.items() if value["n_regions"] == 1]

    @property
    def keys(self):
        """Get all file keys"""
        return self._annotations.keys()

    def sheet_data_count(self, exceptions: List[str] = None):
        """Get the count of all annotated sheets without the specified exceptions"""
        if exceptions is None:
            exceptions = []
        return len(set(self._annotations.keys()).difference(exceptions))

    def get_sheet_data(
            self,
            label_region_loader: LabelRegionLoader,
            exceptions: List[str] = None,
    ) -> Generator[SheetData, None, None]:
        """Generator for all Sheet Data Objects"""
        if exceptions is None:
            exceptions = []

        for key in self._annotations.keys():
            if key in exceptions:
                continue
            yield self.get_specific_sheetdata(key, label_region_loader)

    def get_specific_sheetdata(self, key: str, label_region_loader: LabelRegionLoader) -> SheetData:
        """Return sheet data object of the given file key, loaded with the given label region loader"""
        # Load the xls
        xls_file_name, sheet_name = DataPreprocessor.split_annotation_key(key)
        xls_file_path = join(self.path, "xls", xls_file_name)
        wb = load_workbook(xls_file_path)
        wb.path = xls_file_path  # Path is wrongly defaulted to /xl/workbook.xml, change it
        ws = wb[sheet_name]

        # Load the annotations
        sheet_annotations = self._annotations[key]
        label_regions, table_definitions = label_region_loader.load_label_regions_and_table_definitions(
            ws,
            sheet_annotations,
        )
        # Create & return the sheetdata
        return SheetData(ws, label_regions, table_definitions)

    def __str__(self):
        """Dataset String Representation"""
        return f"Dataset: {self.name}"
