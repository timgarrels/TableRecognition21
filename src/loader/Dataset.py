import json
import logging
from functools import cached_property
from os import listdir
from os.path import isfile, join, split
from typing import Iterable

from openpyxl import load_workbook

from labelregions.AnnotationPreprocessor import AnnotationPreprocessor
from loader.SheetData import SheetData

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Dataset(object):
    def __init__(self, path, name, annotation_preprocessor: AnnotationPreprocessor):
        self.path = path
        self.name = name
        self.annotation_preprocessor = annotation_preprocessor

    @cached_property
    def _annotations(self):
        annotation_file = join(self.path, "annotations_elements.json")
        with open(annotation_file) as f:
            data = f.read()
        return json.loads(data)

    def _get_sheet_annotations(self, xls_name, sheetname):
        annotations_key = xls_name + '_' + sheetname + '.csv'
        return self._annotations[annotations_key]

    def _get_xls_file_paths(self):
        xls_file_directory = join(self.path, "xls")
        xls_files = [xls_file for xls_file in listdir(xls_file_directory) if isfile(join(xls_file_directory, xls_file))]
        return [join(xls_file_directory, xls_file) for xls_file in xls_files]

    def _get_workbooks(self):
        """Generator for all Workbook Objects"""
        for xls_path in self._get_xls_file_paths():
            logger.info(f"Loading workbook {xls_path}")
            try:
                wb = load_workbook(xls_path)
            except:
                # Something went wrong with loading the workbook, log and skip
                logger.warning(f"Could not load workbook {xls_path}")
                continue
            wb.path = xls_path  # Path is wrongly defaulted to /xl/workbook.xml
            yield wb

    def get_sheet_data(self) -> Iterable[SheetData]:
        """Generator for all Sheet Data Objects"""
        for workbook in self._get_workbooks():
            for sheet in workbook:
                wb_path = sheet.parent.path
                xls_file_name = split(wb_path)[1]
                try:
                    sheet_annotations = self._get_sheet_annotations(xls_file_name, sheet.title)
                except KeyError:
                    # No annotation for this sheet exists (probably empty or a graph)
                    continue
                label_regions, table_definitions = self.annotation_preprocessor.preprocess_annotations(
                    sheet,
                    sheet_annotations,
                )
                yield SheetData(sheet, label_regions, table_definitions)

    def get_specific_sheetdata(self, xls_file: str, sheet_name: str) -> SheetData:
        xls_file_path = join(self.path, "xls", xls_file)
        wb = load_workbook(xls_file_path)

        wb.path = xls_file_path  # Path is wrongly defaulted to /xl/workbook.xml
        sheet = wb[sheet_name]
        sheet_annotations = self._get_sheet_annotations(xls_file, sheet.title)
        label_regions, table_definitions = self.annotation_preprocessor.preprocess_annotations(
            sheet,
            sheet_annotations,
        )
        return SheetData(sheet, label_regions, table_definitions)

    def __str__(self):
        return f"Dataset: {self.name}"
