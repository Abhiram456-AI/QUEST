import unittest
import numpy as np
import tempfile
import shutil
import json
from pathlib import Path

from quest.quantum.quantum_walk import QuantumWalkEngine, QuantumWalkResult
from quest.quantum.qvnn_predictor import QUESTQVNNPredictor, QVNNPrediction
from quest.quantum.qsvm_classifier import QUESTQSVMClassifier, QSVMResult

class TestQuantumModels(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_quantum_walk_engine(self):
        engine = QuantumWalkEngine()
        graph_data = {
            "nodes": ["A", "B", "C"],
            "edges": [["A", "B"], ["B", "C"]]
        }
        
        # Test adjacency matrix building
        matrix, index_map = engine.build_adjacency_matrix(graph_data["nodes"], graph_data["edges"])
        self.assertEqual(matrix.shape, (3, 3))
        self.assertEqual(matrix[0, 1], 1)
        self.assertEqual(matrix[1, 2], 1)
        self.assertEqual(matrix[0, 2], 0)
        self.assertEqual(index_map, {"A": 0, "B": 1, "C": 2})

        # Test quantum walk evolution
        probs = engine.quantum_walk(matrix, start_index=0, steps=2)
        self.assertEqual(len(probs), 3)
        self.assertAlmostEqual(float(np.sum(probs)), 1.0)

        # Test full analyze call
        result = engine.analyze(graph_data)
        self.assertIsInstance(result, QuantumWalkResult)
        self.assertEqual(result.source_component, "A")
        self.assertIn("A", result.propagation_scores)
        self.assertIn("B", result.propagation_scores)
        self.assertIn("C", result.propagation_scores)

    def test_qvnn_predictor(self):
        predictor = QUESTQVNNPredictor()
        features = [0.1, 0.5, 0.3, 0.8]
        
        # Test variational circuit building
        circuit = predictor.build_variational_circuit(features)
        self.assertEqual(circuit.num_qubits, 4)

        # Test single sample prediction
        prob = predictor.predict_sample(features)
        self.assertTrue(0.0 <= prob <= 1.0)

        # Test batch predict
        X = np.array([features, [0.9, 0.9, 0.9, 0.9]])
        X_path = self.test_dir / "X.npy"
        np.save(X_path, X)

        predictions = predictor.predict(str(X_path))
        self.assertEqual(len(predictions), 2)
        self.assertIsInstance(predictions[0], QVNNPrediction)
        self.assertEqual(predictions[0].sample_id, 0)
        self.assertEqual(predictions[1].sample_id, 1)

    def test_qsvm_classifier(self):
        classifier = QUESTQSVMClassifier()
        
        # We need a small dataset for testing.
        # Let's create a linearly separable (or simple) dataset with 4 samples.
        X = np.array([
            [0.1, 0.1, 0.1, 0.1],
            [0.2, 0.1, 0.2, 0.1],
            [0.8, 0.9, 0.8, 0.9],
            [0.9, 0.8, 0.9, 0.8]
        ])
        y = np.array([0, 0, 1, 1])

        X_path = self.test_dir / "X.npy"
        y_path = self.test_dir / "y.npy"
        np.save(X_path, X)
        np.save(y_path, y)

        result = classifier.train_and_evaluate(str(X_path), str(y_path))
        self.assertIsInstance(result, QSVMResult)
        self.assertEqual(result.feature_dimension, 4)
        self.assertTrue(0.0 <= result.accuracy <= 1.0)
        self.assertIn("accuracy", result.classification_metrics)
