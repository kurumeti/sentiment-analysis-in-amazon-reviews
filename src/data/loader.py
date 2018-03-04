import multiprocessing
import pandas as pd
import dask.dataframe as dd

from dask.multiprocessing import get
import data.preprocessor as preprocessor


def load_and_clean_data(path, options=(), nrows=None):
    print("\n=> Loading dataset...")
    data_frame = pd.read_csv(path, nrows=nrows, header=None)
    data_frame.fillna("", inplace=True)

    print("=> Cleaning dataset...")
    samples, labels = clean_data(data_frame, options)

    return samples, labels


def load_data(path, rows=None):
    print("\n=> Loading dataset...")
    data_frame = pd.read_csv(path, nrows=rows, header=None)
    data_frame.fillna("", inplace=True)
    return data_frame


def clean_data(data_frame, options, parallel=True):
    preprocessor.configure(options)

    # data_frame[1] contains review title
    # data_frame[2] contains review body
    reviews = data_frame[1] + " " + data_frame[2]

    if parallel:
        cpu_cores = multiprocessing.cpu_count()
        dask_df = dd.from_pandas(reviews, npartitions=cpu_cores)

        def clean_review(review):
            return preprocessor.clean(review)

        processed_df = dask_df.map_partitions(
            lambda df: df.apply(clean_review)
        ).compute(get=get)
    else:
        processed_df = reviews.apply(
            lambda review: preprocessor.clean(review)
        )

    return processed_df.values, data_frame.iloc[:, 0].values