"""Class to hold Configuration for GeneticSearch"""
import math
from typing import Callable

from graph.Edge import Edge
from graph.SpreadSheetGraph import SpreadSheetGraph


class GeneticSearchConfiguration(object):
    def __init__(
            self,
            graph: SpreadSheetGraph,
            n_gen=200,
            rand_mut_p=0.1,
            cross_mut_p=0.5,
            seed=None,
            rooster_size=3,
            edge_mutation_probability_callback: Callable[[Edge], int] = lambda x: 1,
    ):
        self.n_gen = n_gen
        self.rand_mut_p = rand_mut_p
        self.cross_mut_p = cross_mut_p
        self.seed = seed
        self.rooster_size = rooster_size
        # Callback used to determine edge mutation probability
        self.edge_mutation_probability_callback = edge_mutation_probability_callback

        self.n_pop = math.ceil(math.log10(len(graph.edge_list)) * 100)
        self.n_offspring = self.n_pop
        self.n_survivors = self.n_pop

    def __str__(self):
        return "\n\t".join([
            "GeneticSearchConfiguration:",
            f"n_gen: {self.n_gen}",
            f"rand_mut_p: {self.rand_mut_p}",
            f"cross_mut_p: {self.cross_mut_p}",
            f"seed: {self.seed}",
            f"rooster_size: {self.rooster_size}",
        ])
