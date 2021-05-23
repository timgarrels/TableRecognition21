"""Implements genetic search on SpreadsheetGraphs"""
from AbstractSearch import AbstractSearch
import math
import random
from typing import List
import logging
import sys

from GeneticSearchConfiguration import GeneticSearchConfiguration
from SpreadSheetGraph import SpreadSheetGraph
from Rater import Rater

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

class GeneticSearch(AbstractSearch):
    def __init__(
        self,
        graph: SpreadSheetGraph,
        rater: Rater,
        configuration: GeneticSearchConfiguration,
    ):
        self.configuration = configuration
        super().__init__(graph, rater)

    def random_edge_toggle_list(self) -> List[bool]:
        """Creates a single, random edge toggle list"""
        # TODO: Implement Seed
        if self.configuration.seed is not None:
            raise NotImplementedError("Seed is not implemented!")
        return [random.choice([True, False]) for _ in range(len(self.graph.edge_list))]

    def run(self):
        logger.info("Running Genetic Search...")
        logger.info("Creating initial population...")
        n_pop = math.ceil(math.log10(len(self.graph.edge_list)) * 100)
        n_offspring = n_pop
        n_survivors = n_pop

        # Create first population and hof
        pop = [self.random_edge_toggle_list() for _ in range(n_pop)]
        ratings = list(map(lambda individual: self.rate_edge_toggle_list(individual), pop))
        hof_individual = None
        hof_rating = None
        for i in range(len(pop)):
            if hof_individual is None and hof_rating is None:
                hof_individual = pop[i]
                hof_rating = ratings[i]
            else:
                if ratings[i] < hof_rating:
                    hof_individual = pop[i]
                    hof_rating = ratings[i]

        logger.debug(f"Fittest: {self.print_toggle_list(hof_individual)}")

        logger.info("Starting genetic search...")
        for generation in range(self.configuration.n_gen):
            logger.debug(f"Generation {generation}")
            # createOffsprings
            logger.debug("\tCreating children from population...")
            children = [self.child_from_popultaion(pop) for _ in range(n_offspring)]

            # updateHallOfFame
            logger.debug("\tUpdating Hall of Fame...")
            children_ratings = list(map(lambda individual: self.rate_edge_toggle_list(individual), children))
            for i in range(len(children)):
                if children_ratings[i] < hof_rating:
                    _ = 1
                    hof_individual = children[i][:] # By value
                    hof_rating = children_ratings[i]
                    logger.debug(f"\t\tNew Hall of Fame with a rating of {hof_rating}")
                    _ = 1
            # selectFittest
            logger.debug("\Selecting fittest for next population...")
            pop, ratings = self.select_fittest(pop, ratings, children, children_ratings, n_survivors, self.configuration.rooster_size)

        return hof_individual, hof_rating

    def child_from_popultaion(self, population: List[List[bool]]) -> List[bool]:
        """Generate a child toggle list for the next generation using a parent population and propabilities for the mutations"""
        population = population[:] # By value
        p = random.random()
        if p < self.configuration.rand_mut_p:
            # Do random mutation
            parent_toggle_list = random.choice((population))
            mutated_index = random.randint(0, len(parent_toggle_list) - 1)
            child = parent_toggle_list
            child[mutated_index] = not child[mutated_index]
            return child
        elif p > self.configuration.rand_mut_p and p < self.configuration.cross_mut_p + self.configuration.rand_mut_p:
            # Do uniform cross mutation
            p1_index = random.randint(0, len(population) - 1)
            p1_toggle_list = population.pop(p1_index)
            p2_toggle_list = random.choice(population)

            # For each index, randomly choose either p1 or p2 bit
            child = [random.choice([p1_toggle_list[i], p2_toggle_list[i]]) for i in range(len(p1_toggle_list))]
            return child
        else:
            # No mutation
            return random.choice(population)

    def select_fittest(
        self,
        parents: List[bool],
        parent_ratings: List[float],
        children: List[bool],
        children_ratings: List[bool],
        n_survivors: int,
        rooster_size=3,
    ):
        participants = parents + children
        ratings = parent_ratings + children_ratings

        survivors = []
        survivor_ratings = []
        while len(survivor_ratings) < n_survivors:
            # Choose three participants
            participant_indices = list(range(len(participants)))

            if len(participants) < rooster_size:
                # Not enough participants for rooster, add random participant
                participant_index = random.choice(participant_indices)
                participant_indices.pop(participant_indices.index(participant_index))
                survivors.append(participants.pop(participant_index))
                survivor_ratings.append(ratings.pop(participant_index))
                continue

            rooster = []
            for _ in range(rooster_size):
                # Choose a participant and add him and his rating to the rooster
                participant_index = random.choice(participant_indices)
                participant_indices.pop(participant_indices.index(participant_index))
                rooster.append((participant_index, ratings[participant_index]))
            # Select fittest of participants as survivor
            fittest_participant_index = sorted(rooster, key=lambda x: x[1])[0][0]
            fittest_participant = participants.pop(fittest_participant_index)
            fittest_rating = ratings.pop(fittest_participant_index)
            survivors.append(fittest_participant)
            survivor_ratings.append(fittest_rating)
        return survivors, survivor_ratings


def test():
    print("Running genetic search test")
    config = GeneticSearchConfiguration()
    print(config)
    class MockSheetGraph():
        def __init__(self, edge_count):
            self.edge_list = [1 for _ in range(edge_count)]

    class MockRater():
        def __init__(self):
            pass
        def rate(self, graph, edge_toggle_list):
            return sum(edge_toggle_list)

    edge_count = 100
    search = GeneticSearch(
        MockSheetGraph(edge_count),
        MockRater(),
        config,
    )

    fittest, fittest_rating = search.run()
    print("-----------\nResult:")
    print(f"\tFittest: {GeneticSearch.print_toggle_list(fittest)} (Rating: {fittest_rating})")
    print(f"\tTrue Count of Fittest: {sum(fittest)}")

if __name__ == "__main__":
    test()
