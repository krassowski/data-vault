from random import random, randint, choice, seed

from pandas import DataFrame

from data_vault.memory import optimize_memory


def test_optimize_memory():
    seed(0)
    df = DataFrame([
        {
            'small_int': randint(0, 50),
            'large_int': randint(0, 10000),
            'float': random() * 50,
            'repetitive_text': choice(['cat 1', 'cat 2']),
            'unique_text': chr(_)
        }
        for _ in range(100)
    ])
    df_new = optimize_memory(df, inplace=False)

    assert df_new.small_int.dtype == 'int8'
    assert df_new.large_int.dtype != 'int8'
    assert df_new.float.dtype == 'float'

    assert df_new.repetitive_text.dtype == 'category'
    assert df_new.unique_text.dtype == 'object'
