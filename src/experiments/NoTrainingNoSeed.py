import json
import logging
from os import makedirs, listdir
from os.path import join, isfile

from tqdm import tqdm

from graph.SpreadSheetGraph import SpreadSheetGraph
from loader.Dataset import Dataset
from loader.SheetData import SheetData
from rater.AccuracyRater import detection_evaluation, area_precision_and_recall
from rater.FitnessRater import FitnessRater
from search.ExhaustiveSearch import ExhaustiveSearch
from search.GeneticSearch import GeneticSearch
from search.GeneticSearchConfiguration import GeneticSearchConfiguration

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NoTrainingNoSeed(object):
    def __init__(self, dataset: Dataset, output_dir: str):
        self._dataset = dataset
        if self._dataset.label_region_loader.introduce_noise:
            raise ValueError(
                f"This experiment does not expect noise, but the dataset uses a preprocessor with noise="
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
                              total=self._dataset.sheet_data_count(self._already_processed)):
            logger.info(f"Processing sheetdata {sheetdata}")
            result = NoTrainingNoSeed.process(sheetdata)

            with open(join(self._output_dir, sheetdata.annotation_key + "_result.json"), "w",
                      encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

    @staticmethod
    def process(sheetdata: SheetData):
        """Creates ground truth and detected table definition by running just the search algorithm"""
        weights = [1.0 for _ in range(10)]
        sheet_graph = SpreadSheetGraph(sheetdata)
        edge_count = len(sheet_graph.edge_toggle_list)
        ground_truth = sheet_graph.get_table_definitions()
        rater = FitnessRater(weights)
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
        eval_dict = detection_evaluation(ground_truth, detected)
        precision_recall_dict = area_precision_and_recall(ground_truth, detected)
        all_eval_results = {**eval_dict, **precision_recall_dict}

        result = {
            "evaluation": all_eval_results,
            "edge_count": edge_count,
            "ground_truth": [bb.__dict__() for bb in ground_truth],
            "detected": [bb.__dict__() for bb in detected],
        }
        return result
