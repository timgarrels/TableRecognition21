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


def main():
    data_preprocessor = DataPreprocessor(DATA_DIR, "preprocessed_annotations_elements.json")
    data_preprocessor.preprocess()

    label_region_loader = LabelRegionLoader()
    TEST = Dataset(join(DATA_DIR, "Test"), "Test", label_region_loader)

    experiment = CrossValidationTraining(2, TEST, OUTPUT_DIR, weight_tuning_rounds=2)
    experiment.start()


if __name__ == "__main__":
    main()
