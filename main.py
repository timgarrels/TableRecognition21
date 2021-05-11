from os.path import join
from openpyxl import load_workbook

from label_region_preprocessing import LabelRegionPreprocessor


DATA_DIR = "data"
ANNOTATIONS = "annotations_elements.json"
SPREADSHEET = "andrea_ring__3__HHmonthlyavg.xlsx"
ANNOTATION_FILE = join(DATA_DIR, ANNOTATIONS)
SPREADSHEET_FILE = join(DATA_DIR, SPREADSHEET)

def main():
    wb = load_workbook(SPREADSHEET_FILE)
    sheetname = wb.sheetnames[0]
    preprocessor = LabelRegionPreprocessor(
        ANNOTATION_FILE,
        SPREADSHEET_FILE,
        sheetname,
    )

    lrs = preprocessor.preproces_annotations()


if __name__ == "__main__":
    main()
