import argparse
import logging
from os import getcwd
from os.path import join

from experiments.NoTrainingNoSeed import NoTrainingNoSeed
from labelregions.LabelRegionLoader import LabelRegionLoader
from loader.DataPreprocessor import DataPreprocessor
from loader.Dataset import Dataset

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

DATA_DIR = join(getcwd(), "data")
OUTPUT_DIR = join(getcwd(), "output")

label_region_loader = LabelRegionLoader()
DECO = Dataset(join(DATA_DIR, "Deco"), "Deco", label_region_loader)
FUSTE = Dataset(join(DATA_DIR, "FusTe"), "FusTe", label_region_loader)
TEST = Dataset(join(DATA_DIR, "Test"), "Test", label_region_loader)


def main():
    datasets = dict([(ds.name, ds) for ds in [DECO, FUSTE, TEST]])

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", help=f"Specify the dataset. One of {list(datasets.keys())}", required=True)
    args = parser.parse_args()

    dataset = datasets[args.dataset]

    data_preprocessor = DataPreprocessor(DATA_DIR, "preprocessed_annotations_elements.json")
    data_preprocessor.preprocess()

    NoTrainingNoSeed(dataset, OUTPUT_DIR).start()


if __name__ == "__main__":
    main()
