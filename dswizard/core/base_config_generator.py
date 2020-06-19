from __future__ import annotations

import abc
import logging

from ConfigSpace.configuration_space import ConfigurationSpace, Configuration

from dswizard.core.model import StatusType


class BaseConfigGenerator(abc.ABC):
    """
    The config generator determines how new configurations are sampled. This can take very different levels of
    complexity, from random sampling to the construction of complex empirical prediction models for promising
    configurations.
    """

    def __init__(self,
                 configspace: ConfigurationSpace,
                 working_directory: str = None,
                 logger: logging.Logger = None):
        """
        :param configspace:
        :param working_directory:
        :param logger: for some debug output
        """
        if configspace is None:
            raise ValueError('You have to provide a valid ConfigSpace object')

        if logger is None:
            self.logger = logging.getLogger('ConfigGenerator')
        else:
            self.logger = logger
        self.configspace: ConfigurationSpace = configspace
        self.expected_size = self.configspace.get_default_configuration().get_array().size

    @abc.abstractmethod
    def sample_config(self, default: bool = False) -> Configuration:
        pass

    def register_result(self, config: Configuration, loss: float, status: StatusType, update_model: bool = True,
                        **kwargs) -> None:
        """
        registers finished runs

        Every time a run has finished, this function should be called to register it with the result logger. If
        overwritten, make sure to call this method from the base class to ensure proper logging.

        :param config:
        :param loss:
        :param status:
        :param update_model: determines whether a model inside the config_generator should be updated
        :return:
        """
        # TODO check if base implementation is really necessary
        pass
        #
        # if status is not StatusType.SUCCESS:
        #     self.logger.warning('job {} failed with {}'.format(job.cid, job.result.status))
