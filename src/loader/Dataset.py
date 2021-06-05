import json
import logging
from functools import cached_property
from os import listdir
from os.path import isfile, join, split
from typing import Generator

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from labelregions.AnnotationPreprocessor import AnnotationPreprocessor
from loader.SheetData import SheetData

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# TODO: Preprocess Sheets to remove all hidden rows and columns
#       The Chair Annotations are based on csv's, which do not contain hidden cols/rows. This means that
#       we have to handle hidden rows/cols somehow.
#       There are multiple possible solutions:
#       1. Work on the csv files, by turning them into xls again. Easiest solution, requires little work
#           Problem: width and height are lost, which are required for certain metrics
#       2. Remove hidden rows/cols from the xls, by shifting data. Supported by openpyxl
#           Problem: Shifts only data, not formatting width and height are now wrongly assigned.
#       3. I rewrote the annotation preprocessor to skip over hidden rows and columns,
#           by creating a list of unhidden col_letters and unhidden row_indices, which I then can access with the
#           annotation coordinates
#           Problem: As label regions still have to be merged, it would require a major refactor
#           to enable label regions to span over hidden rows/columns.

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

    @staticmethod
    def worksheet_contains_hidden(worksheet: Worksheet):
        hidden_cols = [dim for _, dim in worksheet.column_dimensions.items() if dim.hidden is True]
        hidden_rows = [dim for _, dim in worksheet.row_dimensions.items() if dim.hidden is True]
        if len(hidden_cols) > 0 or len(hidden_rows) > 0:
            # Contains hidden
            return True
        return False

    def _get_workbooks(self):
        """Generator for all Workbook Objects"""
        for i, xls_path in enumerate(self._get_xls_file_paths()):
            logger.info(f"Loading workbook {i}/{len(self._get_xls_file_paths())}: {xls_path}")
            try:
                wb = load_workbook(xls_path)
            except:
                # Something went wrong with loading the workbook, log and skip
                logger.warning(f"Could not load workbook {xls_path}")
                continue
            wb.path = xls_path  # Path is wrongly defaulted to /xl/workbook.xml
            yield wb

    def get_sheet_data(self) -> Generator[SheetData, None, None]:
        """Generator for all Sheet Data Objects"""
        for workbook in self._get_workbooks():
            for sheet in workbook:
                if Dataset.worksheet_contains_hidden(sheet):
                    logger.debug(
                        f"The sheet {sheet.title} of workbook {workbook.path} contains hidden cols or rows, which we cant handle yet!")
                    continue
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
        if Dataset.worksheet_contains_hidden(sheet):
            raise NotImplementedError("This sheet contains hidden cols or rows, which we cant handle yet!")
        sheet_annotations = self._get_sheet_annotations(xls_file, sheet.title)
        label_regions, table_definitions = self.annotation_preprocessor.preprocess_annotations(
            sheet,
            sheet_annotations,
        )
        return SheetData(sheet, label_regions, table_definitions)

    def __str__(self):
        return f"Dataset: {self.name}"
