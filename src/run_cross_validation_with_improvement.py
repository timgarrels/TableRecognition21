import argparse
import logging
import sys
from os import getcwd
from os.path import join

from dataset.DataPreprocessor import DataPreprocessor
from dataset.Dataset import Dataset
from experiments import DataRefiner
from experiments.ImprovedCrossValidationTraining import ImprovedCrossValidationTraining
from labelregions.LabelRegionLoader import LabelRegionLoader

logging.basicConfig(level=logging.INFO, stream=sys.stderr)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

DATA_DIR = join(getcwd(), "data")
OUTPUT_DIR = join(getcwd(), "output")

DECO = Dataset(join(DATA_DIR, "Deco"), "Deco")
FUSTE = Dataset(join(DATA_DIR, "FusTe"), "FusTe")
TEST = Dataset(join(DATA_DIR, "Test"), "Test")


def main():
    datasets = dict([(ds.name, ds) for ds in [DECO, FUSTE, TEST]])

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", help=f"Specify the dataset. One of {list(datasets.keys())}", required=True)
    parser.add_argument("--seed", help="Set the seed for random module", type=int, default=1)
    parser.add_argument("--noise", default=False, action="store_true",
                        help="Add noise while loading label regions")
    args = parser.parse_args()

    dataset = datasets[args.dataset]

    data_preprocessor = DataPreprocessor(DATA_DIR, "preprocessed_annotations_elements.json")
    data_preprocessor.preprocess(dataset.name)

    DataRefiner.refine(dataset)

    label_region_loader = LabelRegionLoader(introduce_noise=args.noise)

    experiment = ImprovedCrossValidationTraining(dataset, label_region_loader, OUTPUT_DIR, random_seed=args.seed)
    experiment.start()


if __name__ == "__main__":
    main()