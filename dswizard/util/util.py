import importlib
import logging
import os
from typing import Optional

from sklearn.metrics import roc_auc_score, log_loss
from sklearn.preprocessing import LabelBinarizer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

valid_metrics = {'accuracy', 'precision', 'recall', 'f1', 'logloss', 'rocauc'}


def setup_logging(log_file: str):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(name)-20s %(message)s')

    fh = logging.FileHandler(log_file, mode='w')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def score(y, y_pred, metric: str):
    if metric == 'accuracy':
        score = accuracy_score(y, y_pred)
    elif metric == 'precision':
        score = precision_score(y, y_pred, average='weighted')
    elif metric == 'recall':
        score = recall_score(y, y_pred, average='weighted')
    elif metric == 'f1':
        score = f1_score(y, y_pred, average='weighted')
    elif metric == 'logloss':
        # TODO not working
        score = logloss(y, y_pred)
    elif metric == 'rocauc':
        score = multiclass_roc_auc_score(y, y_pred, average='weighted')
    else:
        raise ValueError

    # Always compute minimization problem
    if metric != 'logloss':
        score = -1 * score
    return score


def openml_mapping(task: int = None, ds: int = None):
    tasks = {3: 3, 12: 12, 18: 18, 31: 31, 53: 54, 3549: 458, 3560: 469, 3567: 478, 3896: 1043, 3913: 1063, 7592: 1590,
             9952: 1489, 9961: 1498, 9977: 1486, 9983: 1471, 9986: 1476, 10101: 1464, 14965: 1461, 146195: 40668,
             146212: 40685, 146606: 23512, 146818: 40981, 146821: 40975, 146822: 40984, 167119: 41027,
             167120: 23517, 168329: 41169, 168330: 41168, 168911: 41143, 168912: 41146}
    datasets = dict(map(reversed, tasks.items()))

    if (task is None and ds is None) or (task is not None and ds is not None):
        raise ValueError('Provide either task or ds id')
    if task is not None:
        return tasks[task]
    return datasets[ds]


def multiclass_roc_auc_score(y_test, y_pred, average="macro"):
    """
    from https://medium.com/@plog397/auc-roc-curve-scoring-function-for-multi-class-classification-9822871a6659
    """
    lb = LabelBinarizer()
    lb.fit(y_test)

    y_test = lb.transform(y_test)
    y_pred = lb.transform(y_pred)

    return roc_auc_score(y_test, y_pred, average=average)


def logloss(y_test, y_pred):
    """
    from https://medium.com/@plog397/auc-roc-curve-scoring-function-for-multi-class-classification-9822871a6659
    """
    lb = LabelBinarizer()
    lb.fit(y_test)

    y_test = lb.transform(y_test)
    y_pred = lb.transform(y_pred)

    return log_loss(y_test, y_pred)


def prefixed_name(prefix: Optional[str], name: str) -> str:
    """
    Returns the potentially prefixed name name.
    """
    return name if prefix is None else '{}:{}'.format(prefix, name)


def get_type(clazz: str) -> type:
    module_name = clazz.rpartition(".")[0]
    class_name = clazz.split(".")[-1]

    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)
    return class_


def get_object(clazz: str, kwargs=None):
    if kwargs is None:
        kwargs = {}

    return get_type(clazz)(**kwargs)
