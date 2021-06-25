from abc import ABC, abstractmethod
from typing import List

from graph.SpreadSheetGraph import SpreadSheetGraph
from search.FitnessRater import FitnessRater


class AbstractSearch(ABC):
    def __init__(
            self,
            graph: SpreadSheetGraph,
            rater: FitnessRater,
    ):
        self.graph = graph
        self.rater = rater

    @abstractmethod
    def run(self) -> SpreadSheetGraph:
        pass

    def rate_edge_toggle_list(self, edge_toggle_list: List[bool]):
        return self.rater.rate(self.graph, edge_toggle_list)

    @staticmethod
    def str_toggle_list(toggle_list):
        return ''.join([bin(x)[2] for x in toggle_list])
