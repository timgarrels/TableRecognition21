"""Implements genetic search on SpreadsheetGraphs"""
import logging

from search.AbstractSearch import AbstractSearch

logger = logging.getLogger(__name__)


class ExhaustiveSearch(AbstractSearch):

    def run(self):
        """Iterate through all possible edge permutations via binary encoding"""
        logger.debug("Running Exhaustive Search...")
        bits = len(self.graph.edge_toggle_list)
        numbers = 2 ** bits

        fittest_partition = None
        fittest_rating = None
        for n in range(numbers):
            # Map binary representation of permutation to toggle list
            bitstring = bin(n)[2:]
            missing_bits = bits - len(bitstring)
            # Prefix with zeros to fit the required length
            bitstring = "0" * missing_bits + bitstring
            # Transform 0 to false and 1 to true
            toggle_list = [bool(int(bit)) for bit in bitstring]

            # Calculate rating
            rating = self.rate_edge_toggle_list(toggle_list)
            if fittest_rating is None or rating < fittest_rating:
                fittest_rating = rating
                fittest_partition = toggle_list

        logger.debug(f"Best individual: {fittest_partition}")
        logger.debug(f"Best rating: {fittest_rating}")
        self.graph.edge_toggle_list = fittest_partition
        return self.graph
