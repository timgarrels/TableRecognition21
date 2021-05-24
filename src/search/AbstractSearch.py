from abc import ABC, abstractmethod
from typing import List, Tuple

from graph.SpreadSheetGraph import SpreadSheetGraph
from rater.Rater import Rater


class AbstractSearch(ABC):
    def __init__(
            self,
            graph: SpreadSheetGraph,
            rater: Rater,
    ):
        self.graph = graph
        self.rater = rater

    @abstractmethod
    def run(self) -> Tuple[List[bool], float]:
        pass

    def rate_edge_toggle_list(self, edge_toggle_list: List[bool]):
        return self.rater.rate(self.graph, edge_toggle_list)

    @staticmethod
    def str_toggle_list(toggle_list):
        return ''.join([bin(x)[2] for x in toggle_list])
