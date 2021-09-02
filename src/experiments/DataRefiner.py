"""Outputs additional data for sheetdata which is later used for notebook analysis"""
import json
import logging
from itertools import chain
from os.path import join, exists

from openpyxl.utils import get_column_letter
from tqdm import tqdm

from dataset.Dataset import Dataset
from dataset.SheetData import SheetData
from graph.GraphComponentData import GraphComponentData
from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.BoundingBox import BoundingBox
from labelregions.LabelRegionLoader import LabelRegionLoader

logger = logging.getLogger(__name__)


def refine(dataset: Dataset):
    """Extracts metadata from all sheetdata and dumps it"""
    out_file = join(dataset.path, "refined.json")
    if exists(out_file):
        logger.info(f"Already refined!")
        return

    label_region_loader = LabelRegionLoader()
    refined_data = {}
    logger.info("Refining dataset")
    for key in tqdm(dataset.keys):
        refined = refine_sheet_data(dataset.get_specific_sheetdata(key, label_region_loader))
        refined_data[key] = refined
    with open(out_file, "w") as f:
        json.dump(refined_data, f, ensure_ascii=False, indent=4)


def refine_sheet_data(sheet_data: SheetData):
    """Returns metadata for a sheetdata object"""
    graph = SpreadSheetGraph(sheet_data)
    edge_count = len(graph.edge_toggle_list)

    components = [GraphComponentData(c, graph) for c in graph.get_components()]

    min_bounding_box_of_graph = BoundingBox.merge([component.bounding_box for component in components])
    left_most_col = min_bounding_box_of_graph.left
    right_most_col = min_bounding_box_of_graph.right

    xs_between = get_empty_columns_between_tables(left_most_col, right_most_col, components)
    xs_inside = get_empty_columns_inside_of_tables(components)

    # Column widths for later reproduction of figure 2
    xs_between_widths = [width_of_col(idx, graph) for idx in xs_between]
    xs_inside_widths = [width_of_col(idx, graph) for idx in xs_inside]

    return {
        "edge_count": edge_count,
        "xs_between_widths": xs_between_widths,
        "xs_inside_widths": xs_inside_widths,
        "table_count": len(components),
        "label_region_count": len(graph.nodes),
    }


def get_empty_columns_between_tables(left_most_col, right_most_col, components):
    """Returns a list of all columns, that are not covered by a table"""
    empty_xs_between = list(range(left_most_col, right_most_col + 1))

    for component_bounding_box in [component.bounding_box for component in components]:
        for covered_x in component_bounding_box.get_all_x():
            try:
                empty_xs_between.remove(covered_x)
            except ValueError:
                # col index not present, was already removed
                pass
    return empty_xs_between


def get_empty_columns_inside_of_tables(components):
    """Returns all columns that are within one component but not covered by a table in that component"""
    empty_xs_inside = set()
    for component in components:
        x_lists = [lr.get_all_x() for lr in component.label_regions]
        # All columns that are covered by at least on label region in our component
        x_s = set(list(chain(*x_lists)))
        # The Columns most left and most right in our component can not be empty
        # otherwise the component would be smaller
        # This means all columns in the components bounding box without x_s are all empty columns
        empty_columns = set(component.bounding_box.get_all_x()) - x_s
        empty_xs_inside = empty_xs_inside.union(empty_columns)
    return empty_xs_inside


def width_of_col(col_idx, graph):
    """Returns the width of the given column index for the given graph"""
    width = graph.sheet.column_dimensions[get_column_letter(col_idx)].width
    if width is None:
        # Dimensions are None if default values are used
        width = graph.sheet.sheet_format.defaultColWidth
    return width
