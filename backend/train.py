import sys

import pandas as pd

from .scoring.model import train_model


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: uv run python -m backend.train path/to/account_data.csv"
        )

    train_model(
        pd.read_csv(
            sys.argv[1],
            keep_default_na=False,
            na_values=[""],
            ))