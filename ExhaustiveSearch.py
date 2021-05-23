"""Implements genetic search on SpreadsheetGraphs"""
import logging
import sys

from AbstractSearch import AbstractSearch
from Rater import Rater

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


class ExhaustiveSearch(AbstractSearch):

    def run(self):
        logger.info("Running Exhaustive Search...")
        bits = len(self.graph.edge_toggle_list)
        numbers = 2 ** bits

        fittest_partition = None
        fittest_rating = None
        for n in range(numbers):
            bitstring = '{0:08b}'.format(n)
            toggle_list = [bool(int(bit)) for bit in bitstring]
            rating = self.rate_edge_toggle_list(toggle_list)
            if fittest_rating is None or rating < fittest_rating:
                fittest_rating = rating
                fittest_partition = toggle_list

        return fittest_partition, fittest_rating


def test():
    print("Running exhaustive search test")

    class MockSheetGraph():
        def __init__(self, edge_count):
            self.edge_list = [1 for _ in range(edge_count)]
            self.edge_toggle_list = [True for _ in range(len(self.edge_list))]

    class MockRater(Rater):
        def __init__(self):
            pass

        def rate(self, graph, edge_toggle_list):
            return sum(edge_toggle_list)

    edge_count = 10
    search = ExhaustiveSearch(
        MockSheetGraph(edge_count),
        MockRater(),
    )

    fittest, fittest_rating = search.run()
    print("-----------\nResult:")
    print(f"\tFittest: {ExhaustiveSearch.print_toggle_list(fittest)} (Rating: {fittest_rating})")
    print(f"\tTrue Count of Fittest: {sum(fittest)}")


if __name__ == "__main__":
    test()
