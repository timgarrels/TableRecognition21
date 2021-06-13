import logging
import random
from typing import List, Dict

from scipy.optimize import minimize, Bounds

from graph.SpreadSheetGraph import SpreadSheetGraph
from rater.FitnessRater import FitnessRater

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# TODO: Implement proper weight tuning, with multiple, averaging runs, cross-validation, and with & without (?) noise
def objective_function(weights: List[float], partitions: Dict[SpreadSheetGraph, List[List[bool]]], rater: FitnessRater):
    """Objective function proposed by the paper"""
    rater.weights = weights
    score = 0
    for graph, alternative_toggle_lists in partitions.items():
        target_partition_part = 1 + rater.rate(graph, graph.edge_toggle_list)
        for alternative_toggle_list in alternative_toggle_lists:
            alternative_partition_part = 1 + rater.rate(graph, alternative_toggle_list)
            score += target_partition_part / alternative_partition_part
    logger.debug(f"score: {score}, weights: {weights}")
    return score


def generate_alternatives(graph: SpreadSheetGraph, n=1) -> List[List[bool]]:
    """Generates n random edge toggle lists for the given graph"""
    alternatives = []
    for _ in range(n):
        alternatives.append([random.choice([True, False]) for _ in range(len(graph.edge_toggle_list))])
    return alternatives


def train(graphs: List[SpreadSheetGraph]):
    """Takes a list of ground truth spreadsheet graphs, generates alternatives and generates a weight vector"""
    partitions = {}
    for graph in graphs:
        partitions[graph] = generate_alternatives(graph, 10)

    initial_weights = [1 for _ in range(10)]
    # Create rater object outside to leverage caching
    rater = FitnessRater(initial_weights)

    res = minimize(
        objective_function,
        initial_weights,
        args=(partitions, rater),
        method="SLSQP",
        bounds=Bounds(0, 1000),
    )
    return res.x
