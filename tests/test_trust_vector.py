import unittest
import tempfile
import shutil
import json
from pathlib import Path
from quest.trust.trust_vector import TrustVectorBuilder, TrustVector

class TestTrustVector(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.builder = TrustVectorBuilder()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_calculate_trust_score(self):
        # score = reliability * 0.5 + (1 - (complexity*0.3 + dependency*0.2 + security*0.3)) * 0.5
        # If everything is 0: reliability=0 -> 0.5 * 0 + (1 - 0) * 0.5 = 0.5
        score = self.builder.calculate_trust_score(0, 0, 0, 0)
        self.assertEqual(score, 0.5)

        # High reliability, low risk: reliability=1.0, complexity=0, dependency=0, security=0 -> 1.0 * 0.5 + 1.0 * 0.5 = 1.0
        score = self.builder.calculate_trust_score(0, 0, 0, 1.0)
        self.assertEqual(score, 1.0)

        # Low reliability, high risk: reliability=0.0, complexity=1.0, dependency=1.0, security=1.0 -> 0 + (1 - 0.8)*0.5 = 0.1
        score = self.builder.calculate_trust_score(1.0, 1.0, 1.0, 0.0)
        self.assertEqual(score, 0.1)

    def test_classify(self):
        self.assertEqual(self.builder.classify(0.85), "HIGH_TRUST")
        self.assertEqual(self.builder.classify(0.55), "MODERATE_TRUST")
        self.assertEqual(self.builder.classify(0.45), "LOW_TRUST")

    def test_build_vector(self):
        feature = {
            "file_path": "test.py",
            "complexity": 0.2,
            "dependency_influence": 0.4,
            "security_risk": 0.1,
            "reliability": 0.8
        }
        trust_vector = self.builder.build_vector(feature)
        self.assertIsInstance(trust_vector, TrustVector)
        self.assertEqual(trust_vector.file_path, "test.py")
        self.assertEqual(trust_vector.vector, [0.2, 0.4, 0.1, 0.8])
        # Expected score:
        # risk_component = 0.2*0.3 + 0.4*0.2 + 0.1*0.3 = 0.06 + 0.08 + 0.03 = 0.17
        # trust = 0.8*0.5 + (1 - 0.17)*0.5 = 0.4 + 0.415 = 0.815 -> classified as HIGH_TRUST
        self.assertEqual(trust_vector.trust_score, 0.815)
        self.assertEqual(trust_vector.trust_category, "HIGH_TRUST")

    def test_build_from_file(self):
        features = [
            {
                "file_path": "test.py",
                "complexity": 0.2,
                "dependency_influence": 0.4,
                "security_risk": 0.1,
                "reliability": 0.8
            }
        ]
        feature_file = self.test_dir / "trust_features.json"
        with open(feature_file, "w", encoding="utf-8") as f:
            json.dump(features, f)

        vectors = self.builder.build_from_file(str(feature_file))
        self.assertEqual(len(vectors), 1)
        self.assertEqual(vectors[0].file_path, "test.py")
        self.assertEqual(vectors[0].trust_category, "HIGH_TRUST")
