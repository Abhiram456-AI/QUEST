

"""
QUEST: Quantum Evaluation of Software Trust

Phase 2:
Trust Representation Engine

Module:
Dataset Builder

Purpose:
Converts QUEST Trust Vectors into machine learning ready datasets.

Produces:

X -> Trust feature matrix
Y -> Trust reliability labels

This dataset becomes the experimental input for:
- QSVM Trust Classification
- QVNN Reliability Prediction
- Classical ML baseline comparisons
"""


import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

import numpy as np


@dataclass
class QUESTDataset:
    samples: int
    features: int
    X: List[List[float]]
    y: List[int]
    labels: List[str]


class DatasetBuilder:
    """
    Builds quantum/classical ML compatible datasets
    from QUEST trust vectors.
    """

    LABEL_MAPPING = {
        "LOW_TRUST": 0,
        "MODERATE_TRUST": 1,
        "HIGH_TRUST": 2
    }


    def build(
        self,
        trust_vector_path: str
    ) -> QUESTDataset:

        path = Path(
            trust_vector_path
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Trust vector file missing: {path}"
            )

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            vectors = json.load(file)


        X = []
        y = []
        labels = []


        for item in vectors:

            vector = item.get(
                "vector"
            )

            category = item.get(
                "trust_category"
            )


            if vector is None or category is None:
                continue


            X.append(
                vector
            )

            y.append(
                self.LABEL_MAPPING.get(
                    category,
                    0
                )
            )

            labels.append(
                category
            )


        return QUESTDataset(
            samples=len(X),
            features=len(X[0]) if X else 0,
            X=X,
            y=y,
            labels=labels
        )


    def export_numpy(
        self,
        dataset: QUESTDataset,
        output_directory: str
    ):
        """
        Exports dataset into NumPy arrays for
        quantum and classical experiments.
        """

        directory = Path(
            output_directory
        )

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        np.save(
            directory / "X.npy",
            np.array(dataset.X)
        )

        np.save(
            directory / "y.npy",
            np.array(dataset.y)
        )


    def save_json(
        self,
        dataset: QUESTDataset,
        output_path: str
    ):

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                asdict(dataset),
                file,
                indent=4
            )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="QUEST Dataset Builder"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="trust_vectors.json path"
    )

    parser.add_argument(
        "--output",
        default="outputs/quest_dataset.json"
    )

    parser.add_argument(
        "--numpy",
        default="datasets"
    )


    args = parser.parse_args()


    builder = DatasetBuilder()

    dataset = builder.build(
        args.input
    )


    builder.save_json(
        dataset,
        args.output
    )

    builder.export_numpy(
        dataset,
        args.numpy
    )


    print(
        f"QUEST Dataset Created: {dataset.samples} samples, {dataset.features} features"
    )