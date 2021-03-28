import pandas as pd
import numpy as np


def mb(x):
    """Represent as MB"""
    return x / 10**6


def optimize_memory(
    df: pd.DataFrame,
    categorical_threshold=0.2,
    categorise_numbers=False,
    categorise_booleans=False,
    inplace=True,
    report=True
):

    before = df.memory_usage(index=True, deep=True).sum()

    if not inplace:
        df = df.copy()

    for column in df.columns:
        s = df[column]

        if s.dtype.name == 'category':
            continue

        if np.issubdtype(s.dtype, np.integer):
            if s.min() >= -125 and s.max() < 125 and not s.isnull().any():
                df[column] = s.astype('int8')
                continue

        # attempt to categorise
        values = set(s)

        if np.issubdtype(s.dtype, np.number) and not categorise_numbers:
            continue

        if np.issubdtype(s.dtype, np.bool_) and not categorise_booleans:
            continue

        if len(values) / len(s) < categorical_threshold:
            try:
                sorted_categories = sorted([v for v in values if not pd.isnull(v)])
                ordered = True
            except TypeError as e:
                sorted_categories = None
                ordered = False
                print(f'Not sorting categories for {column}: {e}')
            df[column] = pd.Categorical(s, categories=sorted_categories, ordered=ordered)

    after = df.memory_usage(deep=True).sum()

    if report:
        percent = (before - after) / before * 100
        print(
            f'Reduced memory usage by {percent:.2f}%,'
            f' from {mb(before):.2f} MB to {mb(after):.2f} MB.'
        )

    return df
