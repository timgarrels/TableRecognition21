import argparse
import logging
from os import getcwd
from os.path import join

from dataset.DataPreprocessor import DataPreprocessor
from dataset.Dataset import Dataset
from experiments import DataRefiner
from experiments.NoTrainingNoSeed import NoTrainingNoSeed

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

DATA_DIR = join(getcwd(), "data")
OUTPUT_DIR = join(getcwd(), "output")


def main():
    DECO = Dataset(join(DATA_DIR, "Deco"), "Deco")
    FUSTE = Dataset(join(DATA_DIR, "FusTe"), "FusTe")
    TEST = Dataset(join(DATA_DIR, "Test"), "Test")

    datasets = dict([(ds.name, ds) for ds in [DECO, FUSTE, TEST]])

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", help=f"Specify the dataset. One of {list(datasets.keys())}", required=True)
    args = parser.parse_args()

    dataset = datasets[args.dataset]

    data_preprocessor = DataPreprocessor(DATA_DIR, "preprocessed_annotations_elements.json")
    data_preprocessor.preprocess(dataset.name)

    DataRefiner.refine(dataset)

    NoTrainingNoSeed(dataset, OUTPUT_DIR).start()


if __name__ == "__main__":
    main()
