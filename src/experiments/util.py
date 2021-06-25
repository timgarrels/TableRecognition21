import json
import logging
from os import makedirs
from os.path import join, split, exists
from shutil import rmtree
from typing import List

from dataset.SheetData import SheetData
from experiments.AccuracyRater import detection_evaluation, area_precision_and_recall
from graph.SpreadSheetGraph import SpreadSheetGraph
from search.ExhaustiveSearch import ExhaustiveSearch
from search.FitnessRater import FitnessRater
from search.GeneticSearch import GeneticSearch
from search.GeneticSearchConfiguration import GeneticSearchConfiguration
from visualization.GraphVisualization import visualize_graph
from visualization.SheetDataVisualization import visualize_sheet_data

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def process_and_visualize_sheetdata(sheetdata: SheetData, output_dir: str, weights: List[float] = None,
                                    visualize=False):
    logger.info(f"Processing sheet {sheetdata}")
    if weights is None:
        weights = [1.0 for _ in range(10)]
    sheet_output_dir = join(
        output_dir,
        split(sheetdata.parent_path)[1],
        sheetdata.worksheet.title,
    )

    if exists(sheet_output_dir):
        rmtree(sheet_output_dir)
    makedirs(sheet_output_dir, exist_ok=True)

    if visualize:
        logger.info(f"Visualizing Ground Truth Label Regions and Table Definition of sheet '{sheetdata}'")
        visualize_sheet_data(sheetdata, join(sheet_output_dir, "visualization_in.xlsx"))

    sheet_graph = SpreadSheetGraph(sheetdata)

    ground_truth = sheet_graph.get_table_definitions()
    logger.info(f"Exporting ground truth table definition")
    with open(join(sheet_output_dir, "ground_truth_table_definition.json"), "w", encoding="utf-8") as f:
        json.dump([bb.__dict__() for bb in ground_truth], f, ensure_ascii=False, indent=4)

    if visualize:
        logger.info(f"Visualizing ground truth graph")
        visualize_graph(sheet_graph, out=join(sheet_output_dir, 'ground_truth_graph'))

        logger.info(f"Visualizing input graph")
        # Reset edge toggle list to remove ground truth from graph
        sheet_graph.enable_all_edges()
        visualize_graph(sheet_graph, out=join(sheet_output_dir, 'input_graph'))

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
    logger.info(f"Running search...")
    sheet_graph = search.run()
    logger.info(f"Finished search...")

    if visualize:
        logger.info("Visualizing Fittest Graph")
        visualize_graph(sheet_graph, out=join(sheet_output_dir, 'fittest_graph'))

    detected = sheet_graph.get_table_definitions()
    logger.info(f"Exporting fittest table definition")
    with open(join(sheet_output_dir, "fittest_table_definition.json"), "w", encoding="utf-8") as f:
        json.dump([bb.__dict__() for bb in detected], f, ensure_ascii=False, indent=4)

    if visualize:
        logger.info(f"Visualizing Computed Label Regions and Table Definition of sheet '{sheetdata}'")
    visualize_sheet_data(sheetdata, join(sheet_output_dir, "visualization_out.xlsx"))

    eval_dict = detection_evaluation(ground_truth, detected)
    precision_recall_dict = area_precision_and_recall(ground_truth, detected)

    all_eval_results = {**eval_dict, **precision_recall_dict}
    logger.info(f"Exporting eval results")
    with open(join(sheet_output_dir, "eval_results.json"), "w", encoding="utf-8") as f:
        json.dump(all_eval_results, f, ensure_ascii=False, indent=4)
