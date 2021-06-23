import logging
from os import getcwd
from os.path import join

from experiments.NoTrainingNoSeed import NoTrainingNoSeed
from labelregions.AnnotationPreprocessor import AnnotationPreprocessor
from loader.Dataset import Dataset

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

DATA_DIR = join(getcwd(), "data")
OUTPUT_DIR = join(getcwd(), "output")


def main():
    preprocessor = AnnotationPreprocessor(introduce_noise=False)
    DECO = Dataset(join(DATA_DIR, "Deco"), "Deco", preprocessor)
    FUSTE = Dataset(join(DATA_DIR, "FusTe"), "FusTe", preprocessor)
    # TEST = Dataset(join(DATA_DIR, "Test"), "Test", preprocessor)

    experiment = NoTrainingNoSeed(DECO, OUTPUT_DIR)
    experiment.start()


if __name__ == "__main__":
    main()
