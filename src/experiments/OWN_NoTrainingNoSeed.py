import logging
from os.path import join
from typing import List, Callable

from dataset.Dataset import Dataset
from dataset.SheetData import SheetData
from experiments.NoTrainingNoSeed import NoTrainingNoSeed
from graph.Edge import Edge
from graph.SpreadSheetGraph import SpreadSheetGraph
from search.ExhaustiveSearch import ExhaustiveSearch
from search.FitnessRater import FitnessRater
from search.GeneticSearchConfiguration import GeneticSearchConfiguration
from search.OWN_GeneticSearch import OWN_GeneticSearch

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OWN_NoTrainingNoSeed(NoTrainingNoSeed):
    def __init__(self, dataset: Dataset, output_dir: str,
                 name: str,
                 weights: List[int] = None,
                 edge_mutation_probability_callback: Callable[[Edge], int] = lambda _: 1):

        output_dir = join(output_dir, "own_" + name)
        super().__init__(dataset, output_dir, weights)
        self._edge_mutation_probability_callback: Callable[[Edge], int] = edge_mutation_probability_callback

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
            search = OWN_GeneticSearch(
                sheet_graph,
                rater,
                GeneticSearchConfiguration(sheet_graph),
                self._edge_mutation_probability_callback,
            )
        sheet_graph = search.run()
        detected = sheet_graph.get_table_definitions()

        result = {
            "ground_truth": [bb.__dict__() for bb in ground_truth],
            "detected": [bb.__dict__() for bb in detected],
        }
        return result
