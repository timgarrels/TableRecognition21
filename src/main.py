import logging
from os import getcwd
from os.path import join

from labelregions.LabelRegionLoader import LabelRegionLoader
from loader.DataPreprocessor import DataPreprocessor
from loader.Dataset import Dataset
from visualization.SheetDataVisualization import visualize_sheet_data

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

DATA_DIR = join(getcwd(), "data")
OUTPUT_DIR = join(getcwd(), "output")


def main():
    data_preprocessor = DataPreprocessor(DATA_DIR, "preprocessed_annotations_elements.json")
    data_preprocessor.preprocess()

    label_region_loader = LabelRegionLoader()
    DECO_pre = Dataset(join(DATA_DIR, "Deco"), "Deco", label_region_loader)
    DECO = Dataset(join(DATA_DIR, "Deco"), "Deco", label_region_loader, "annotations_elements.json")

    sd = DECO_pre.get_specific_sheetdata("andrea_ring__3__HHmonthlyavg.xlsx", "Monthly HH Flows")
    visualize_sheet_data(sd, "new_preproc.xlsx")


if __name__ == "__main__":
    main()
