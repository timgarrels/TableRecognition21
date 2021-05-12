from os.path import join
from openpyxl import load_workbook, Workbook
import openpyxl
import random

from LabelRegionPreprocessor import LabelRegionPreprocessor
from SpreadSheetGraph import SpreadSheetGraph


DATA_DIR = "data"
VISUALIZATIONS_DIR = "visualizations"
ANNOTATIONS = "annotations_elements.json"
SPREADSHEET = "andrea_ring__3__HHmonthlyavg.xlsx"
ANNOTATION_FILE = join(DATA_DIR, ANNOTATIONS)
SPREADSHEET_FILE = join(DATA_DIR, SPREADSHEET)

def random_rgb_hex():
    """Creates a random rgb string like 00FF00FF"""
    return ''.join([hex(random.choice(range(16)))[2:] for _ in range(8)])

def visualize_lrs(lrs):
    """Creates a colorful spreadsheet from the lr data"""
    my_red = openpyxl.styles.colors.Color(rgb='00FF0000')
    redFill = openpyxl.styles.fills.PatternFill(patternType='solid', fgColor=my_red)

    wb = Workbook()
    ws = wb.create_sheet("Visualization")
    for i, lr in enumerate(lrs):
        color = openpyxl.styles.colors.Color(rgb=random_rgb_hex())
        fill = openpyxl.styles.fills.PatternFill(patternType='solid', fgColor=color)
        min_x, min_y = lr["top_left"]
        max_x, max_y = lr["bottom_right"]
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                d = ws.cell(y, x)
                d.value = f"{i} - {lr['type']}"
                d.fill = fill
    wb.save(join(VISUALIZATIONS_DIR, 'visualization.xlsx'))

def main():
    wb = load_workbook(SPREADSHEET_FILE)
    sheetname = wb.sheetnames[0]
    preprocessor = LabelRegionPreprocessor(
        ANNOTATION_FILE,
        SPREADSHEET_FILE,
        sheetname,
    )

    lrs = preprocessor.preproces_annotations()
    visualize_lrs(lrs)
    g = SpreadSheetGraph.from_label_regions(lrs)

    g.visualize(out=join(VISUALIZATIONS_DIR, 'graph'))

if __name__ == "__main__":
    main()
