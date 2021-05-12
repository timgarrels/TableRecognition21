"""Class which implements Metrics and Weight Training for Partition Evaluation"""
from typing import Callable, Dict, List
from SpreadSheetGraph import SpreadSheetGraph

# TODO: Implement metrics (how to access cell data? via graph?)
# TODO: Implement weight training

Metric = Callable[[SpreadSheetGraph], float]

class Rater(object):
    def __init__(self, enabled_metrics: List[Metric]=None):
        if enabled_metrics is None:
            enabled_metrics = [
                self.mock_metric
            ]
        self.enabled_metrics: List[Metric] = enabled_metrics

        self.weights: Dict[Metric, float] = {}.fromkeys(self.enabled_metrics, 1)

    def mock_metric(self, graph: SpreadSheetGraph) -> float:
        return sum(graph.edge_toggle_list)

    def rate_partition(self, graph: SpreadSheetGraph, edge_toggle_list: List[bool]) -> float:
        # Create graph copy with that partition
        new_graph = graph
        new_graph.edge_toggle_list = edge_toggle_list

        scores = []
        for metric in self.enabled_metrics:
            score = self.weights[metric] * metric(new_graph)
            scores.append(score)
        return sum(scores)
