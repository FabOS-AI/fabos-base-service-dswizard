import warnings
from typing import Optional, Tuple, Union, List

import numpy as np
from ConfigSpace import Configuration
from sklearn import clone
from sklearn.base import is_classifier
from sklearn.model_selection import check_cv
from sklearn.model_selection._validation import _fit_and_predict, _check_is_permutation
from sklearn.utils import indexable
from sklearn.utils.validation import _num_samples

from automl.components.base import EstimatorComponent
from dswizard.components.pipeline import FlexiblePipeline
from dswizard.core.config_cache import ConfigCache
from dswizard.core.logger import ProcessLogger
from dswizard.core.model import CandidateId, Dataset
from dswizard.core.worker import Worker
from dswizard.util import util

warnings.filterwarnings("ignore", category=UserWarning)


class SklearnWorker(Worker):

    def compute(self,
                ds: Dataset,
                config_id: CandidateId,
                config: Optional[Configuration],
                cfg_cache: Optional[ConfigCache],
                cfg_keys: Optional[List[Tuple[float, int]]],
                pipeline: FlexiblePipeline,
                process_logger: ProcessLogger) -> List[float]:
        if config is None:
            # Derive configuration on complete data set. Test performance via CV
            cloned_pipeline = clone(pipeline)
            cloned_pipeline.cfg_cache = cfg_cache
            cloned_pipeline.cfg_keys = cfg_keys
            cloned_pipeline.fit(ds.X, ds.y, logger=process_logger)
            config = process_logger.get_config(cloned_pipeline)

        pipeline.set_hyperparameters(config.get_dictionary())
        score, _, _ = self._score(ds, pipeline)
        return score

    def transform_dataset(self, ds: Dataset, config: Configuration, component: EstimatorComponent) \
            -> Tuple[np.ndarray, Optional[float]]:
        component.set_hyperparameters(config.get_dictionary())
        if is_classifier(component):
            score, y_pred, y_prob = self._score(ds, component)
            try:
                y_pred = y_pred.astype(float)
            except ValueError:
                pass
            X = np.hstack((ds.X, y_prob, np.reshape(y_pred, (-1, 1))))
        else:
            X = component.fit(ds.X, ds.y).transform(ds.X)
            score = None
        return X, score

    def _score(self, ds: Dataset, estimator: Union[EstimatorComponent, FlexiblePipeline], n_folds: int = 4):
        y = ds.y
        y_pred, y_prob = self._cross_val_predict(estimator, ds.X, y, cv=n_folds)

        # Meta-learning only considers f1. Calculate f1 score for structure search
        score = [util.score(y, y_prob, y_pred, ds.metric), util.score(y, y_prob, y_pred, 'f1')]
        return score, y_pred, y_prob

    @staticmethod
    def _cross_val_predict(pipeline, X, y=None, cv=None):
        X, y, groups = indexable(X, y, None)
        cv = check_cv(cv, y, classifier=is_classifier(pipeline))

        prediction_blocks = []
        probability_blocks = []
        for train, test in cv.split(X, y, groups):
            cloned_pipeline = clone(pipeline)
            probability_blocks.append(_fit_and_predict(cloned_pipeline, X, y, train, test, 0, {}, 'predict_proba'))
            prediction_blocks.append(cloned_pipeline.predict(X))

        # Concatenate the predictions
        probabilities = [prob_block_i for prob_block_i, _ in probability_blocks]
        predictions = [pred_block_i for pred_block_i in prediction_blocks]
        test_indices = np.concatenate([indices_i for _, indices_i in probability_blocks])

        if not _check_is_permutation(test_indices, _num_samples(X)):
            raise ValueError('cross_val_predict only works for partitions')

        inv_test_indices = np.empty(len(test_indices), dtype=int)
        inv_test_indices[test_indices] = np.arange(len(test_indices))

        probabilities = np.concatenate(probabilities)
        predictions = np.concatenate(predictions)

        if isinstance(predictions, list):
            return [p[inv_test_indices] for p in predictions], [p[inv_test_indices] for p in probabilities]
        else:
            return predictions[inv_test_indices], probabilities[inv_test_indices]
