import json
import logging
from os import getcwd, makedirs
from os.path import join, split, exists
from shutil import rmtree

from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.AnnotationPreprocessor import AnnotationPreprocessor
from loader.Dataset import Dataset
from loader.SheetData import SheetData
from rater.Rater import Rater
from search.ExhaustiveSearch import ExhaustiveSearch
from search.GeneticSearch import GeneticSearch
from search.GeneticSearchConfiguration import GeneticSearchConfiguration
from visualization.GraphVisualization import visualize_graph
from visualization.SheetDataVisualization import visualize_sheet_data

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("log"),
        logging.StreamHandler(),
    ],
)

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

    logger.info(f"Visualizing Ground Truth Label Regions and Table Definition of sheet '{sheetdata}'")
    visualize_sheet_data(sheetdata, join(sheet_output_dir, "visualization_in.xlsx"))

    sheet_graph = SpreadSheetGraph(sheetdata)

    logger.info(f"Exporting ground truth table definition")
    with open(join(sheet_output_dir, "ground_truth_table_definition.json"), "w", encoding="utf-8") as f:
        json.dump(sheet_graph.table_definition_dict(), f, ensure_ascii=False, indent=4)

    logger.info(f"Visualizing ground truth graph")
    visualize_graph(sheet_graph, out=join(sheet_output_dir, 'ground_truth_graph'))

    logger.info(f"Visualizing input graph")
    # Reset edge toggle list to remove ground truth from graph
    sheet_graph.enable_all_edges()
    visualize_graph(sheet_graph, out=join(sheet_output_dir, 'input_graph'))

    rater = Rater([1 for _ in range(10)])
    if len(sheet_graph.nodes) <= 10:
        # Less than 11 nodes, do exhaustive search
        search = ExhaustiveSearch(
            sheet_graph,
            rater,
        )
    else:
        search = GeneticSearch(
            sheet_graph,
            # TODO: Rater should be trained
            rater,
            GeneticSearchConfiguration(),
        )

    sheet_graph = search.run()

    logger.info("Visualizing Fittest Graph")
    visualize_graph(sheet_graph, out=join(sheet_output_dir, 'fittest_graph'))

    logger.info(f"Exporting fittest table definition")
    with open(join(sheet_output_dir, "fittest_table_definition.json"), "w", encoding="utf-8") as f:
        json.dump(sheet_graph.table_definition_dict(), f, ensure_ascii=False, indent=4)

    logger.info(f"Visualizing Computed Label Regions and Table Definition of sheet '{sheetdata}'")
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
    TEST = Dataset(join(DATA_DIR, "Test"), "Test", preprocessor)
    # TODO: Preprocess Sheets to remove all hidden rows and columns
    #       I rewrote the annotation preprocessor to skip over hidden rows and columns,
    #       by creating a list of unhidden col_letters and unhidden row_indices, which I then can access with the
    #       annotation coordinates. However, as label regions still have to be merged, it would require a major refactor
    #       to enable label regions to span over hidden rows/columns.
    #       Therefore I will just remove the hidden rows/columns from the sheet, matching its csv representation

    # Takes forever, because there are 334 nodes in this. Keep for later timing debug purposes
    # sheetdata = FUSTE.get_specific_sheetdata("fde8668c-7bc1-4da6-a2b3-833b14453f5f.xlsx", "Sheet1")

    # sheetdata = DECO.get_specific_sheetdata("matthew_lenhart__26080__NewPlants0102.xlsx", "By Region")
    # SpreadSheetGraph(sheetdata)

    # sheetdata = DECO.get_specific_sheetdata("gstorey__12089__Gas Projects.xlsx", "Sheet1")
    # sheetdata = DECO.get_specific_sheetdata("gstorey__12060__Tony_deals.xlsx", "Sheet1")
    #
    # process_sheetdata(sheetdata, join(OUTPUT_DIR, DECO.name))
    # x = train([SpreadSheetGraph(sd) for sd in TEST.get_sheet_data()])
    # print(x)
    # process_sheetdata(sheetdata, join(OUTPUT_DIR, DECO.name))
    # for dataset in [DECO, FUSTE]:
    process_dataset(TEST, 1)


if __name__ == "__main__":
    main()
