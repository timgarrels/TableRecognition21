"""Implements genetic search on SpreadsheetGraphs"""
import logging

from rater.FitnessRater import FitnessRater
from search.AbstractSearch import AbstractSearch

logger = logging.getLogger(__name__)


class ExhaustiveSearch(AbstractSearch):

    def run(self):
        logger.info("Running Exhaustive Search...")
        bits = len(self.graph.edge_toggle_list)
        numbers = 2 ** bits

        fittest_partition = None
        fittest_rating = None
        for n in range(numbers):
            bitstring = bin(n)[2:]
            toggle_list = [bool(int(bit)) for bit in bitstring]
            missing_bits = bits - len(toggle_list)
            toggle_list = [False for _ in range(missing_bits)] + toggle_list

            rating = self.rate_edge_toggle_list(toggle_list)
            if fittest_rating is None or rating < fittest_rating:
                fittest_rating = rating
                fittest_partition = toggle_list

        logger.info(f"Best rating: {fittest_rating}")
        logger.info(f"Best individual: {fittest_partition}")
        self.graph.edge_toggle_list = fittest_partition
        return self.graph


def test():
    print("Running exhaustive search test")

    class MockSheetGraph():
        def __init__(self, edge_count):
            self.edge_list = [1 for _ in range(edge_count)]
            self.edge_toggle_list = [True for _ in range(len(self.edge_list))]

    class MockRater(FitnessRater):
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
    print(f"\tFittest: {ExhaustiveSearch.str_toggle_list(fittest)} (Rating: {fittest_rating})")
    print(f"\tTrue Count of Fittest: {sum(fittest)}")


if __name__ == "__main__":
    test()
