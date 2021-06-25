import argparse
import logging
from os import getcwd
from os.path import join

from experiments.CrossValidationTraining import CrossValidationTraining
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

    actions = {
        "full_run": lambda ex: ex.start(),
        "prepare": lambda ex: ex.prepare(),
        "run_fold_number": lambda ex, num: ex.pickup_fold(num),
        "finalize": lambda ex: ex.finalize(),
    }
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", help=f"Specify the dataset. One of {list(datasets.keys())}", required=True)
    parser.add_argument("--action", help=f"Specify the action to perform: {list(actions.keys())}", required=True)
    parser.add_argument("--fold-number", help=f"Specify fold number (only on 'run_fold_number' action", required=False)
    args = parser.parse_args()

    dataset = datasets[args.dataset]

    data_preprocessor = DataPreprocessor(DATA_DIR, "preprocessed_annotations_elements.json")
    data_preprocessor.preprocess()

    experiment = CrossValidationTraining(dataset, OUTPUT_DIR)
    if args.action == "run_fold_number":
        if args.fold_number is None:
            raise ValueError("run_fold_number requires a fold number!")
        actions[args.action](experiment, args.fold_number)
    else:
        actions[args.action](experiment)


if __name__ == "__main__":
    main()
