from openpyxl import Workbook

from dataset.SheetData import SheetData
from visualization.LabelRegionVisualization import add_lr_visualization_sheet
from visualization.TableDefinitionVisualization import overlay_table_definition_visualization


def visualize_sheet_data(sheet_data: SheetData, out_path: str):
    """Creates a new workbook with two sheets: The visualisation of label regions without and with
    the ground truth table definition bounding boxes"""
    wb = Workbook()
    add_lr_visualization_sheet(sheet_data.label_regions, wb, sheet_name="Label Region Visualization")
    # Create label region visualization to overlay
    add_lr_visualization_sheet(sheet_data.label_regions, wb, sheet_name="Table Definition Visualization")
    overlay_table_definition_visualization(sheet_data.table_definitions, wb,
                                           sheet_name="Table Definition Visualization")
    wb.save(out_path)
