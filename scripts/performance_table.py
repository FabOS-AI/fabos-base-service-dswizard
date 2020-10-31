import warnings

import pandas as pd
import numpy as np
from scipy.stats import wilcoxon

warnings.filterwarnings("ignore", category=UserWarning)


def impute_missing(df: pd.DataFrame):
    def fill(row):
        if np.isnan(row['result']):
            if row['metric'] == 'auc':
                res = 0
            elif row['metric'] == 'logloss':
                res = 4
            else:
                raise ValueError('Unknown metric {}'.format(row['metric']))
        else:
            res = row['result']
        return res

    df['result'] = df.apply(fill, axis=1)


def compute_statistics(df: pd.DataFrame):
    count = df[(df['result'] == 0) | (df['result'] == 4)].groupby('task').agg({'id': 'count'})
    stats = df.groupby('task').agg({'result': [np.mean, np.std], 'metric': 'max'})
    result = pd.concat([stats, count], axis=1, join='outer').fillna(0)
    result.columns = ['mean', 'std', 'metric', 'missing']
    return result


def get_raw(idx: int):
    return raw[idx][raw[idx]['task'] == ds]['result']


tpot = pd.read_excel('results.xlsx', sheet_name=0)
autosklearn = pd.read_excel('results.xlsx', sheet_name=1)
dswizard = pd.read_excel('results.xlsx', sheet_name=2)

impute_missing(tpot)
impute_missing(autosklearn)
impute_missing(dswizard)

tpot2 = compute_statistics(tpot)
autosklearn2 = compute_statistics(autosklearn)
dswizard2 = compute_statistics(dswizard)

raw = [autosklearn, tpot, dswizard]
raw2 = [autosklearn2, tpot2, dswizard2]

for ds in dswizard2.index:
    metric = tpot2.loc[ds]['metric']
    mean = np.array([df.loc[ds]['mean'] for df in raw2])
    std = np.array([df.loc[ds]['std'] for df in raw2])
    best, argbest = (np.max, np.argmax) if metric == 'auc' else (np.min, np.argmin)

    significance_ref = get_raw(argbest(mean))

    print('{:40s}\t& '.format(str(ds) + ('*' if metric == 'auc' else '')), end='')

    columns = []
    for idx in range(len(mean)):
        if mean[idx] in {0, 4}:
            columns.append('       ---                  ')
        else:
            entry = []
            if mean[idx] == best(mean):
                entry.append('\\B ')
                significant = False
            else:
                entry.append('   ')
                res = wilcoxon(significance_ref, get_raw(idx))
                significant = res.pvalue < 0.05
            if significant:
                entry.append('\\ul{')
            else:
                entry.append('    ')
            entry.append('{:.4f} \\(\\pm\\) {:.4f}'.format(mean[idx], std[idx]))
            if significant:
                entry.append('}')
            columns.append(''.join(entry))
    print('\t& '.join(columns), end='')
    print('\t\\\\')

a = 0
