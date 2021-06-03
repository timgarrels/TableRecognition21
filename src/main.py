import json
import logging
import sys
from os import getcwd, makedirs
from os.path import join, split, exists
from shutil import rmtree

from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.AnnotationPreprocessor import AnnotationPreprocessor
from labelregions.BoundingBox import BoundingBox
from loader.Dataset import Dataset
from loader.SheetData import SheetData
from rater.Rater import Rater
from search.ExhaustiveSearch import ExhaustiveSearch
from search.GeneticSearch import GeneticSearch
from search.GeneticSearchConfiguration import GeneticSearchConfiguration
from visualization.GraphVisualization import visualize_graph
from visualization.SheetDataVisualization import visualize_sheet_data

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DATA_DIR = join(getcwd(), "data")
OUTPUT_DIR = join(getcwd(), "output")


def process_sheetdata(sheetdata: SheetData, output_dir: str):
    sheet_output_dir = join(
        output_dir,
        split(sheetdata.parent_path)[1],
        sheetdata.worksheet.title,
    )
    if exists(sheet_output_dir):
        rmtree(sheet_output_dir)
    makedirs(sheet_output_dir, exist_ok=True)

    logger.info(f"Exporting ground truth table definition")
    with open(join(sheet_output_dir, "ground_truth_table_definition.json"), "w", encoding="utf-8") as f:
        json.dump(sheetdata.table_definition_dict(), f, ensure_ascii=False, indent=4)

    logger.info(f"Visualizing sheet {sheetdata}")
    visualize_sheet_data(sheetdata, join(sheet_output_dir, "visualization_in.xlsx"))

    sheet_graph = SpreadSheetGraph(sheetdata)

    logger.debug(f"Edge Count: {len(sheet_graph.edge_list)}")

    visualize_graph(sheet_graph, out=join(sheet_output_dir, 'ground_truth_graph'))
    # Reset edge toggle list to remove ground truth from graph
    sheet_graph.enable_all_edges()
    visualize_graph(sheet_graph, out=join(sheet_output_dir, 'original_graph'))

    if len(sheet_graph.nodes) <= 10:
        # Less than 11 nodes, do exhaustive search
        search = ExhaustiveSearch(
            sheet_graph,
            Rater(),
        )
    else:
        search = GeneticSearch(
            sheet_graph,
            # TODO: Rater should be trained
            Rater(),
            GeneticSearchConfiguration(),
        )

    fittest, fittest_rating = search.run()

    logger.debug(f"Best rating: {fittest_rating}")
    logger.debug(f"Best individual: {fittest}")

    logger.info("Visualizing Fittest Graph Partition...")
    sheet_graph.edge_toggle_list = fittest

    table_definitions = [BoundingBox.merge(component) for component in
                         sheet_graph.get_components()]

    sheetdata.table_definitions = table_definitions
    logger.info(f"Exporting fittest table definition")
    with open(join(sheet_output_dir, "fittest_table_definition.json"), "w", encoding="utf-8") as f:
        json.dump(sheetdata.table_definition_dict(), f, ensure_ascii=False, indent=4)

    visualize_graph(sheet_graph, out=join(sheet_output_dir, 'fittest_graph'))
    visualize_sheet_data(sheetdata, join(sheet_output_dir, "visualization_out.xlsx"))


def process_dataset(dataset: Dataset, limit=None):
    """Runs the algorithm on the DECO dataset and processes
    only :limit sheets before returning"""
    processed_sheets = 0
    for sheetdata in dataset.get_sheet_data():
        if limit is not None and processed_sheets >= limit:
            break
        process_sheetdata(sheetdata, join(OUTPUT_DIR, dataset.name))
        processed_sheets += 1


def main():
    preprocessor = AnnotationPreprocessor()
    DECO = Dataset(join(DATA_DIR, "Deco"), "Deco", preprocessor)
    FUSTE = Dataset(join(DATA_DIR, "FusTe"), "FusTe", preprocessor)

    # Takes forever, because there are 334 nodes in this. Keep for later timing debug purposes
    # sheetdata = FUSTE.get_specific_sheetdata("fde8668c-7bc1-4da6-a2b3-833b14453f5f.xlsx", "Sheet1")

    sheetdata = DECO.get_specific_sheetdata("andrea_ring__3__HHmonthlyavg.xlsx", "Monthly HH Flows")
    process_sheetdata(sheetdata, join(OUTPUT_DIR, DECO.name))
    # for dataset in [DECO, FUSTE]:
    #     process_dataset(dataset, 1)


if __name__ == "__main__":
    main()
