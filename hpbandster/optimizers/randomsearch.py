import numpy as np
from ConfigSpace.configuration_space import ConfigurationSpace

from hpbandster.core.master import Master
from hpbandster.core.model import Structure
from hpbandster.optimizers.config_generators import RandomSampling
from hpbandster.optimizers.iterations import SuccessiveHalving


class RandomSearch(Master):
    def __init__(self,
                 configspace: ConfigurationSpace = None,
                 structure: Structure = None,
                 eta: float = 3,
                 min_budget: float = 1,
                 max_budget: float = 1,
                 **kwargs
                 ):
        """
        Implements a random search across the search space for comparison. Candidates are sampled at random and run on
        the maximum budget.
        :param configspace: valid representation of the search space
        :param structure: optional structure associated with the ConfigurationSpace
        :param eta: In each iteration, a complete run of sequential halving is executed. In it, after evaluating each
            configuration on the same subset size, only a fraction of 1/eta of them 'advances' to the next round. Must
            be greater or equal to 2.
        :param min_budget: budget for the evaluation
        :param max_budget: budget for the evaluation
        :param kwargs:
        """

        cg = RandomSampling(configspace=configspace, structure=structure)
        super().__init__(config_generator=cg, **kwargs)

        # Hyperband related stuff
        self.eta = eta
        self.min_budget = max_budget
        self.max_budget = max_budget

        # precompute some HB stuff
        self.max_iterations = -int(np.log(min_budget / max_budget) / np.log(eta)) + 1
        self.budgets = max_budget * np.power(eta, -np.linspace(self.max_iterations - 1, 0, self.max_iterations))

        # max total budget for one iteration
        self.budget_per_iteration = sum([b * self.eta ** i for i, b in enumerate(self.budgets[::-1])])

        self.config.update({
            'eta': eta,
            'min_budget': max_budget,
            'max_budget': max_budget,
        })

    def get_next_iteration(self,
                           iteration: int,
                           iteration_kwargs: dict = None) -> SuccessiveHalving:
        """
        Returns a SH iteration with only evaluations on the biggest budget
        :param iteration: the index of the iteration to be instantiated
        :param iteration_kwargs: default
        :return: the SuccessiveHalving iteration with the corresponding number of configurations
        """

        if iteration_kwargs is None:
            iteration_kwargs = {}
        budgets = [self.max_budget]
        ns = [self.budget_per_iteration // self.max_budget]

        return SuccessiveHalving(HPB_iter=iteration, num_configs=ns, budgets=budgets,
                                 config_sampler=self.config_generator, **iteration_kwargs)
