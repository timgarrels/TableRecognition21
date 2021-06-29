import json
import logging
from os import makedirs, listdir
from os.path import join, isfile
from typing import List

from tqdm import tqdm

from dataset.Dataset import Dataset
from dataset.SheetData import SheetData
from graph.SpreadSheetGraph import SpreadSheetGraph
from labelregions.LabelRegionLoader import LabelRegionLoader
from search.ExhaustiveSearch import ExhaustiveSearch
from search.FitnessRater import FitnessRater, get_initial_weights, weight_vector_length
from search.GeneticSearch import GeneticSearch
from search.GeneticSearchConfiguration import GeneticSearchConfiguration

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NoTrainingNoSeed(object):
    def __init__(self, dataset: Dataset, output_dir: str, weights: List[int] = None):
        if weights is None:
            weights = get_initial_weights()

        if len(weights) != weight_vector_length():
            raise ValueError("Weight Vector does not have the correct size!")

        self._dataset = dataset
        self._weights = weights

        self._output_dir = join(output_dir, dataset.name, self.__class__.__name__)

        makedirs(self._output_dir, exist_ok=True)

        self._already_processed = sorted(
            [f.replace("_result.json", "") for f in listdir(self._output_dir) if isfile(join(self._output_dir, f))])

        self._label_region_loader = LabelRegionLoader()

    @property
    def expect_noise(self):
        return False

    def start(self):
        for sheetdata in tqdm(self._dataset.get_sheet_data(self._label_region_loader, self._already_processed),
                              total=self._dataset.sheet_data_count(self._already_processed)):
            logger.info(f"Processing sheetdata {sheetdata}")
            result = self.process(sheetdata)

            with open(join(self._output_dir, sheetdata.annotation_key + "_result.json"), "w",
                      encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

    def process(self, sheetdata: SheetData):
        """Creates ground truth and detected table definition by running just the search algorithm"""
        sheet_graph = SpreadSheetGraph(sheetdata)
        ground_truth = sheet_graph.get_table_definitions()
        rater = FitnessRater(self._weights)
        if len(sheet_graph.nodes) <= 10:
            # Less than 11 nodes, do exhaustive search
            search = ExhaustiveSearch(
                sheet_graph,
                rater,
            )
        else:
            search = GeneticSearch(
                sheet_graph,
                rater,
                GeneticSearchConfiguration(sheet_graph),
            )
        sheet_graph = search.run()
        detected = sheet_graph.get_table_definitions()

        result = {
            "ground_truth": [bb.__dict__() for bb in ground_truth],
            "detected": [bb.__dict__() for bb in detected],
        }
        return result
