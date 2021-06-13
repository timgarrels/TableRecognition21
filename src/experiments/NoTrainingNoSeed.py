from experiments.Experiment import Experiment
from graph.SpreadSheetGraph import SpreadSheetGraph
from loader.SheetData import SheetData
from rater.AccuracyRater import detection_evaluation, area_precision_and_recall
from rater.FitnessRater import FitnessRater
from search.ExhaustiveSearch import ExhaustiveSearch
from search.GeneticSearch import GeneticSearch
from search.GeneticSearchConfiguration import GeneticSearchConfiguration


class NoTrainingNoSeed(Experiment):
    def process(self, sheetdata: SheetData):
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
