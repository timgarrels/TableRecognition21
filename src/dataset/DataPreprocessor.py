"""Drops sheets with hidden rows/cols and sheets that are too large from the annotations"""
import json
import logging
import os
from os.path import isdir, join, getsize, exists
from typing import Dict

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from tqdm import tqdm

logger = logging.getLogger(__name__)


# TODO: Preprocess Sheets to remove all hidden rows and columns
#       The Chair Annotations are based on csv's, which do not contain hidden cols/rows. This means that
#       we have to handle hidden rows/cols somehow. CUrrently, all sheets with hidden cols/rows are just skipped
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

class DataPreprocessor(object):
    def __init__(self, data_path: str, preprocessed_annotation_file_name: str, remove_hidden=True,
                 file_size_cap=1000 * 100):
        self.data_path = data_path
        self.preprocessed_annotation_file_name = preprocessed_annotation_file_name
        self.remove_hidden = remove_hidden
        self.file_size_cap = file_size_cap

    def preprocess(self):
        dirs = [d for d in os.listdir(self.data_path) if isdir(join(self.data_path, d))]
        for data_dir in dirs:
            logger.info(f"Working on {data_dir}")
            annotation_file_path = join(self.data_path, data_dir, "annotations_elements.json")
            preprocessed_annotation_file_path = join(self.data_path, data_dir, self.preprocessed_annotation_file_name)
            xls_dir_path = join(self.data_path, data_dir, "xls")

            # Skip if already preprocessed
            if exists(preprocessed_annotation_file_path):
                continue

            with open(annotation_file_path) as f:
                annotations = json.load(f)
            new_annotations = {}

            for key in tqdm(annotations.keys()):
                xls_file_name, sheet_name = DataPreprocessor.split_annotation_key(key)

                xls_file_path = join(xls_dir_path, xls_file_name)

                # Skip if too large
                if getsize(xls_file_path) > self.file_size_cap:
                    continue

                # Skip if not loadable
                try:
                    wb = load_workbook(xls_file_path)
                except:
                    # Something went wrong with loading the workbook, log and skip
                    logger.warning(f"Could not load workbook {xls_file_path}")
                    continue

                # Skip is sheet contains hidden rows/cols
                ws = wb[sheet_name]
                if DataPreprocessor.worksheet_contains_hidden(ws):
                    continue

                # Add annotation
                new_annotations[key] = self.filter_and_rewrite_annotation(annotations[key])
            # Write new annotations
            with open(preprocessed_annotation_file_path, "w") as f:
                json.dump(new_annotations, f, ensure_ascii=False, indent=4)

    @staticmethod
    def worksheet_contains_hidden(worksheet: Worksheet):
        hidden_cols = [dim for _, dim in worksheet.column_dimensions.items() if dim.hidden is True]
        hidden_rows = [dim for _, dim in worksheet.row_dimensions.items() if dim.hidden is True]
        if len(hidden_cols) > 0 or len(hidden_rows) > 0:
            # Contains hidden
            return True
        return False

    @staticmethod
    def split_annotation_key(key):
        """Returns the xls file name and the sheet name within the key"""
        if ".xlsx_" in key:
            xls_file_name, sheet_name = key.split(".xlsx_")
            xls_file_name += ".xlsx"
        elif ".xls_" in key:
            xls_file_name, sheet_name = key.split(".xls_")
            xls_file_name += ".xls"
        else:
            raise ValueError(f"Annotations contain unexpected naming: {key}")
        sheet_name = sheet_name[:-4]

        return xls_file_name, sheet_name

    @staticmethod
    def filter_and_rewrite_annotation(sheet_annotation: Dict):
        """Removes annotations outside of tables and removes/rewrites label region types"""
        # Remove annotations outside of tables
        table_regions = [region for region in sheet_annotation["regions"] if region["region_type"] == "Table"]
        # Rewrite annotations
        for table_region in table_regions:
            label_regions = table_region["elements"]
            # Set Derived = Data and GroupHead = Header
            for label_region in label_regions:
                if label_region["type"] == "Derived":
                    label_region["type"] = "Data"
                if label_region["type"] == "GroupHead":
                    label_region["type"] = "Header"
            # Remove invalid annotations
            allowed_types = ["Data", "Header"]
            table_region["elements"] = [lr for lr in label_regions if lr["type"] in allowed_types]
            table_region["n_elements"] = len(table_region["elements"])

        return {
            "n_regions": len(table_regions),
            "regions": table_regions,
        }
