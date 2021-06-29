import argparse
import logging
import random
from os import getcwd
from os.path import join

from dataset.DataPreprocessor import DataPreprocessor
from dataset.Dataset import Dataset
from experiments.CrossValidationTraining import CrossValidationTraining
from labelregions.LabelRegionLoader import LabelRegionLoader

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

DATA_DIR = join(getcwd(), "data")
OUTPUT_DIR = join(getcwd(), "output")

DECO = Dataset(join(DATA_DIR, "Deco"), "Deco")
FUSTE = Dataset(join(DATA_DIR, "FusTe"), "FusTe")
TEST = Dataset(join(DATA_DIR, "Test"), "Test")


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
    parser.add_argument(
        "--fold-number",
        help=f"Specify fold number (only on 'run_fold_number' action",
        required=False,
        type=int,
    )
    parser.add_argument("--noise", default=False, action="store_true",
                        help="Add noise while loading label regions")
    parser.add_argument("--seed", help="Set the seed for random module", type=int)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    dataset = datasets[args.dataset]

    data_preprocessor = DataPreprocessor(DATA_DIR, "preprocessed_annotations_elements.json")
    data_preprocessor.preprocess()

    label_region_loader = LabelRegionLoader(introduce_noise=args.noise)
    output_suffix = "noise" if args.noise else "no-noise"

    experiment = CrossValidationTraining(dataset, label_region_loader, join(OUTPUT_DIR, output_suffix))

    if args.action == "run_fold_number":
        if args.fold_number is None:
            raise ValueError("run_fold_number requires a fold number!")
        actions[args.action](experiment, args.fold_number)
    else:
        actions[args.action](experiment)


if __name__ == "__main__":
    main()
