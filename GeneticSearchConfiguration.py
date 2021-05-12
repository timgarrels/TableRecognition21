"""Class to hold Configuration for GeneticSearch"""

class GeneticSearchConfiguration(object):
    def __init__(
        self,
        n_gen=200,
        rand_mut_p=0.1,
        cross_mut_p=0.5,
        cross_mut_scale=.8,
        seed=None,
        rooster_size=3,
    ):
        self.n_gen = n_gen
        self.rand_mut_p = rand_mut_p
        self.cross_mut_p = cross_mut_p
        self.cross_mut_scale = cross_mut_scale
        self.seed = seed
        self.rooster_size = rooster_size

    def __str__(self):
        return "\n\t".join([
            "GeneticSearchConfiguration:",
            f"n_gen: {self.n_gen}",
            f"rand_mut_p: {self.rand_mut_p}",
            f"cross_mut_p: {self.cross_mut_p}",
            f"cross_mut_scale: {self.cross_mut_scale}",
            f"seed: {self.seed}",
            f"rooster_size: {self.rooster_size}",
        ])

DEFAULT_CONFIG = GeneticSearchConfiguration()