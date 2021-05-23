from GeneticSearchConfiguration import GeneticSearchConfiguration
from Rater import Rater
from os.path import join
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import logging

import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

from LabelRegionPreprocessor import LabelRegionPreprocessor
from SpreadSheetGraph import SpreadSheetGraph
from GeneticSearch import GeneticSearch

logger = logging.getLogger(__name__)


DATA_DIR = "data"
VISUALIZATIONS_DIR = "visualizations"
ANNOTATIONS = "annotations_elements.json"
SPREADSHEET = "andrea_ring__3__HHmonthlyavg.xlsx"
ANNOTATION_FILE = join(DATA_DIR, ANNOTATIONS)
SPREADSHEET_FILE = join(DATA_DIR, SPREADSHEET)


def main():
    logger.info("Creating Label Regions...")
    wb = load_workbook(SPREADSHEET_FILE)
    sheetname = wb.sheetnames[0]
    sheet = wb[sheetname]
    preprocessor = LabelRegionPreprocessor()

    label_regions = preprocessor.preproces_annotations(
        ANNOTATION_FILE,
        SPREADSHEET_FILE,
        sheetname,
    )
    logger.info("Visualizing Label Regions...")
    LabelRegionPreprocessor.visualize_lrs(label_regions, out=join(VISUALIZATIONS_DIR, 'lrs.xlsx'))

    logger.info("Creating Spreadsheet Graph...")
    sheet_graph = SpreadSheetGraph.from_label_regions_and_sheet(label_regions, sheet)
    logger.debug(f"Edge Count: {len(sheet_graph.edge_list)}")
    logger.info("Visualizing Spreadsheet Graph...")
    sheet_graph.visualize(out=join(VISUALIZATIONS_DIR, 'original_graph'))

    logger.info("Running Genetic Search...")
    genetic_search = GeneticSearch(
        sheet_graph,
        # TODO: Rater should be trained
        Rater(),
        GeneticSearchConfiguration(rand_mut_p=0.1, cross_mut_p=0.5, n_gen=200),
    )

    fittest, fittest_rating = genetic_search.run()
    logger.debug(f"Best rating: {fittest_rating}")

    logger.info("Visualizaing Fittest Graph Partition...")
    sheet_graph.edge_toggle_list = fittest
    sheet_graph.visualize(out=join(VISUALIZATIONS_DIR, 'fittest_graph'))


if __name__ == "__main__":
    main()
