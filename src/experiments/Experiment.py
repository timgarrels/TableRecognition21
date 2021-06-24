import json
import logging
from abc import ABC, abstractmethod
from os import makedirs, listdir
from os.path import join, isfile

from tqdm import tqdm

from loader.Dataset import Dataset
from loader.SheetData import SheetData

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Experiment(ABC):
    def __init__(self, dataset: Dataset, output_dir: str):
        self._dataset = dataset
        if self._dataset.label_region_loader.introduce_noise != self.expect_noise:
            raise ValueError(
                f"This experiment ('{self.__class__.__name__}') expects noise={self.expect_noise}"
                f", but the dataset uses a preprocessor with noise="
                f"{self._dataset.label_region_loader.introduce_noise}")

        self._output_dir = join(output_dir, dataset.name, self.__class__.__name__)

        makedirs(self._output_dir, exist_ok=True)

        self._already_processed = sorted(
            [f.replace("_result.json", "") for f in listdir(self._output_dir) if isfile(join(self._output_dir, f))])

    @property
    def expect_noise(self):
        return False

    def start(self):
        for sheetdata in tqdm(self._dataset.get_sheet_data(self._already_processed),
                              total=self._dataset.sheet_data_count):
            logger.info(f"Processing sheetdata {sheetdata}")
            result = self.process(sheetdata)

            with open(join(self._output_dir, sheetdata.annotation_key + "_result.json"), "w",
                      encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

    @abstractmethod
    def process(self, sheetdata: SheetData) -> any:
        """Runs an experiment on sheet data and returns the experimental results"""
        pass
