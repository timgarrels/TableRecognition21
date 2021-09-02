"""Implements genetic search on SpreadsheetGraphs"""
import logging
import math
import random
from typing import List, Tuple

from graph.SpreadSheetGraph import SpreadSheetGraph
from search.AbstractSearch import AbstractSearch
from search.FitnessRater import FitnessRater
from search.GeneticSearchConfiguration import GeneticSearchConfiguration

logger = logging.getLogger(__name__)

# logger.setLevel(logging.DEBUG)

IndividualType = Tuple[List[bool], float]


class GeneticSearch(AbstractSearch):
    def __init__(
            self,
            graph: SpreadSheetGraph,
            rater: FitnessRater,
            configuration: GeneticSearchConfiguration,
    ):
        self.configuration = configuration
        super().__init__(graph, rater)

        # Use list of tuples instead of dict to allow duplicates
        self._population: List[IndividualType] = []
        self._hof_individual: IndividualType = ([], math.inf)  # Low Rating better , inf is the worst rating

        # Mutation Probabilities
        # Contains the factor of mutation probability
        # An edge with factor 100 is 100 times more likely to mutate than an edge with factor 1
        self._mutation_probability_per_edge = []
        for i, edge in enumerate(graph.edge_list):
            self._mutation_probability_per_edge.append(
                self.configuration.edge_mutation_probability_callback(edge)
            )

    def random_edge_toggle_list(self) -> List[bool]:
        """Creates a single, random edge toggle list"""
        # TODO: Implement Seed
        if self.configuration.seed is not None:
            raise NotImplementedError("Seed is not implemented!")
        return [random.choice([True, False]) for _ in range(len(self.graph.edge_list))]

    def initialize(self):
        """Create first population and hof"""
        for _ in range(self.configuration.n_pop):
            individual = self.random_edge_toggle_list()
            rating = self.rate_edge_toggle_list(individual)
            self._population.append((individual, rating))

        # Set Hall of Fame individual
        self.update_hall_of_fame(self._population)

    def update_hall_of_fame(self, population: List[IndividualType]):
        """Updates hall of fame with a better individual, if such individual exists in the given population"""
        best_individual = GeneticSearch.get_best_individual(population)
        if best_individual[1] < self._hof_individual[1]:
            self._hof_individual = best_individual

    @staticmethod
    def get_best_individual(population: List[IndividualType]) -> IndividualType:
        """Finds the best individual of the given population and returns it"""
        best_individual = population[0]
        for individual, rating in population:
            if rating < best_individual[1]:
                best_individual = (individual, rating)
        return best_individual

    def run(self) -> SpreadSheetGraph:
        """Explore a part of the exhaustive search space using genetic search"""
        logger.debug("Running Genetic Search...")
        self.initialize()

        for generation in range(self.configuration.n_gen):
            logger.debug(f"Generation {generation}")

            children: List[IndividualType] = []
            for _ in range(self.configuration.n_offspring):
                children.append(self.child_from_population())

            self.update_hall_of_fame(children)

            # Total generation population
            total_generation_population = self._population + children
            self._population = self.tournament_selection(total_generation_population)

        logger.debug(f"Best individual: {self._hof_individual[0]}")
        logger.debug(f"Best rating: {self._hof_individual[1]}")
        self.graph.edge_toggle_list = self._hof_individual[0]
        return self.graph

    def child_from_population(self) -> IndividualType:
        """Generate a new individual using a parent population"""
        potential_parents = [toggle_list for toggle_list, rating in self._population]

        p = random.random()
        if p < self.configuration.rand_mut_p:
            # Do random mutation
            parent = random.choice(potential_parents)
            child = parent

            mutation_candidates = []
            for edge_index, mutation_probability in enumerate(self._mutation_probability_per_edge):
                # Put in the candidate mutation_probability times into the choice list
                mutation_candidates += [edge_index] * mutation_probability

            mutated_index = random.choice(mutation_candidates)
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

    def tournament_selection(self, population: List[IndividualType]) -> List[IndividualType]:
        """Create a new generation out of the given population using tournament selection"""
        survivors: List[IndividualType] = []
        for _ in range(self.configuration.n_survivors):
            # Choose participants
            rooster: List[IndividualType] = random.sample(population, self.configuration.rooster_size)
            # Select fittest of participants as survivor
            fittest_individual_of_rooster = self.get_best_individual(rooster)
            population.remove(fittest_individual_of_rooster)
            survivors.append(fittest_individual_of_rooster)
        return survivors
