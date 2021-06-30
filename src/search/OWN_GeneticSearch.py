"""Implements genetic search on SpreadsheetGraphs"""
import logging
import random
from typing import List, Tuple, Callable

from graph.Edge import Edge
from graph.SpreadSheetGraph import SpreadSheetGraph
from search.FitnessRater import FitnessRater
from search.GeneticSearch import GeneticSearch
from search.GeneticSearchConfiguration import GeneticSearchConfiguration

logger = logging.getLogger(__name__)

# logger.setLevel(logging.DEBUG)

IndividualType = Tuple[List[bool], float]


class OWN_GeneticSearch(GeneticSearch):
    def __init__(
            self,
            graph: SpreadSheetGraph,
            rater: FitnessRater,
            configuration: GeneticSearchConfiguration,
            edge_mutation_probability_callback: Callable[[Edge], int]
    ):
        self.configuration = configuration
        super().__init__(graph, rater, configuration)

        self._mutation_chances_per_edge = [1 / len(graph.edge_toggle_list) for _ in range(len(graph.edge_toggle_list))]
        for i, edge in enumerate(graph.edge_list):
            self._mutation_chances_per_edge[i] *= edge_mutation_probability_callback(edge)

    def child_from_population(self) -> IndividualType:
        """Generate a new individual using a parent population"""
        potential_parents = [toggle_list for toggle_list, rating in self._population]

        p = random.random()
        if p < self.configuration.rand_mut_p:
            # Do random mutation
            parent = random.choice(potential_parents)
            child = parent

            possible_indices = []
            for i, prob in enumerate(self._mutation_chances_per_edge):
                count = prob * len(self._mutation_chances_per_edge)
                possible_indices += [i] * int(count)

            mutated_index = random.choice(possible_indices)

            child[mutated_index] = not child[mutated_index]
        elif self.configuration.rand_mut_p < p < self.configuration.rand_mut_p + self.configuration.cross_mut_p:
            # Do uniform cross mutation
            father, mother = random.sample(potential_parents, 2)

            # For each index, randomly choose either p1 or p2 bit
            child: List[bool] = [random.choice([father[i], mother[i]]) for i in range(len(father))]
        else:
            # No mutation
            child = random.choice(potential_parents)

        return child, self.rate_edge_toggle_list(child)
