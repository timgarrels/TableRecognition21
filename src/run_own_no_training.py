import argparse
import logging
from multiprocessing.pool import ThreadPool
from os import getcwd
from os.path import join

from dataset.DataPreprocessor import DataPreprocessor
from dataset.Dataset import Dataset
from experiments import DataRefiner
from experiments.OWN_NoTrainingNoSeed import OWN_NoTrainingNoSeed
from graph.Edge import Edge, AlignmentType
from labelregions.LabelRegionType import LabelRegionType

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

    factor = 5

    def same_over_different(edge: Edge) -> int:
        if edge.destination.type == edge.source.type:
            return factor
        return 1

    def header_over_data(edge: Edge) -> int:
        if edge.destination.type == edge.source.type and edge.destination.type == LabelRegionType.HEADER:
            return factor
        return 1

    def data_over_header(edge: Edge) -> int:
        if edge.destination.type == edge.source.type and edge.destination.type == LabelRegionType.DATA:
            return factor
        return 1

    def horizontal_over_vertical_alignment(edge: Edge) -> int:
        if edge.alignment_type == AlignmentType.HORIZONTAL:
            return factor
        return 1

    def long_over_short(edge: Edge) -> int:
        if edge.alignment_type == AlignmentType.HORIZONTAL:
            distance = edge.source.left - edge.destination.right
        else:
            distance = edge.source.top - edge.destination.bottom

        if distance > 3:
            return factor
        return 1

    def prefer_edges_with_similar_size(edge: Edge) -> int:
        total_size = edge.source.area - edge.destination.area
        if total_size == 0:
            return factor
        f = 1 - abs(edge.source.area / total_size - edge.destination.area / total_size)
        return f * factor

    callbacks = [
        same_over_different,
        header_over_data,
        data_over_header,
        horizontal_over_vertical_alignment,
        long_over_short,
        prefer_edges_with_similar_size,
    ]

    def wrapper(callback):
        OWN_NoTrainingNoSeed(dataset, OUTPUT_DIR, name=callback.__name__,
                             edge_mutation_probability_callback=callback).start()

    threads = ThreadPool(len(callbacks))
    threads.map(wrapper, callbacks)


if __name__ == "__main__":
    main()
