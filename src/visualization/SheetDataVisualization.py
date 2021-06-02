from openpyxl import Workbook

from loader.SheetData import SheetData
from visualization.LabelRegionVisualization import add_lr_visualization
from visualization.TableDefinitionVisualization import add_table_definition_visualization


def visualize_sheet_data(sheet_data: SheetData, out_path: str):
    wb = Workbook()
    add_lr_visualization(sheet_data.label_regions, wb, sheet_name="Label Region Visualization")
    # Create label region visualization to overlay
    add_lr_visualization(sheet_data.label_regions, wb, sheet_name="Table Definition Visualization")
    add_table_definition_visualization(sheet_data.table_definitions, wb, sheet_name="Table Definition Visualization")
    wb.save(out_path)
