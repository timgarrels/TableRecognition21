import argparse
import logging
import sys
from os import getcwd
from os.path import join

import experiments.EdgePropabilityCallback as EdgePropabilityCallback
from dataset.DataPreprocessor import DataPreprocessor
from dataset.Dataset import Dataset
from experiments import DataRefiner
from experiments.CrossValidationTraining import CrossValidationTraining
from labelregions.LabelRegionLoader import LabelRegionLoader

logging.basicConfig(level=logging.INFO, stream=sys.stderr)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

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
    parser.add_argument("--improvement", default="None", help="Specify an improvement to apply to the approach",
                        choices=["None", "EdgeMutationProbability", "EdgeMutationProbabilityExtreme"])
    args = parser.parse_args()

    dataset = datasets[args.dataset]

    data_preprocessor = DataPreprocessor(DATA_DIR, "preprocessed_annotations_elements.json")
    data_preprocessor.preprocess(dataset.name)

    DataRefiner.refine(dataset)

    label_region_loader = LabelRegionLoader(introduce_noise=args.noise)

    edge_probability_callback = EdgePropabilityCallback.default_edge_mutation_probability_callback

    if args.improvement == "None":
        print("No Improvement chosen!")
    elif args.improvment == "EdgeMutationProbability":
        print(f"Improvement EdgeMutationProbability chosen!")
        edge_probability_callback = EdgePropabilityCallback.short_edges_different_types
    elif args.improvment == "EdgeMutationProbabilityExtreme":
        print(f"Improvement EdgeMutationProbabilityExtreme chosen!")
        edge_probability_callback = EdgePropabilityCallback.extreme_short_edges_different_types
    else:
        raise ValueError("Unknown Improvement Chosen!")

    experiment = CrossValidationTraining(
        dataset,
        label_region_loader,
        OUTPUT_DIR,
        random_seed=args.seed,
        edge_mutation_probability_callback=edge_probability_callback,
    )
    experiment.start()


if __name__ == "__main__":
    main()
