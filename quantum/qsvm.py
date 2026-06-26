from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

try:
    from qiskit.circuit.library import ZZFeatureMap
    from qiskit_machine_learning.kernels import FidelityQuantumKernel
    from qiskit.primitives import StatevectorSampler

    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


@dataclass
class QSVMResult:
    predictions: List[int]
    probabilities: List[float]
    labels: List[str]
    support_vectors: int
    quantum_enabled: bool
    metadata: Dict[str, Any]
    repository_confidence: float
    high_risk_modules: int
    critical_modules: int


class QuantumRiskClassifier:
    """
    Quantum-enhanced SVM for repository risk classification.

    Input features per module:
        [
            risk_score,
            fan_in,
            fan_out,
            centrality,
            pagerank,
            blast_radius,
            instability,
            repo_influence,
            propagation_risk,
        ]
    Output:
        0 -> LOW RISK
        1 -> HIGH RISK
    """

    RISK_LABELS = {
        0: "LOW",
        1: "MEDIUM",
        2: "HIGH",
        3: "CRITICAL",
    }

    def __init__(self, reps: int = 2):
        self.reps = reps
        self.scaler = StandardScaler()
        self.model: Optional[SVC] = None
        self.kernel = None
        self.quantum_enabled = QISKIT_AVAILABLE
        self.entanglement = "full"
        self.max_quantum_samples = 128
        self.n_features_ = 0
        self.n_samples_ = 0
        self.classes_: List[int] = []
        self.training_mode = "classical"
        self.kernel_cache: Dict[Any, Any] = {}
        self.max_quantum_features = 16
        self.pca: Optional[PCA] = None

    def clear_cache(self) -> None:
        """Clear cached kernel information and reset transient state."""
        self.kernel_cache.clear()

    def get_model_summary(self) -> Dict[str, Any]:
        """Return runtime metadata for debugging and verification."""
        return {
            "training_mode": self.training_mode,
            "quantum_enabled": self.training_mode == "quantum",
            "n_features": self.n_features_,
            "n_samples": self.n_samples_,
            "classes": self.classes_,
            "entanglement": self.entanglement,
            "pca_enabled": self.pca is not None,
            "kernel_cache_size": len(self.kernel_cache),
            "max_quantum_samples": self.max_quantum_samples,
            "max_quantum_features": self.max_quantum_features,
            "model_fitted": self.model is not None or self.training_mode == "single_class",
            "prediction_ready": self.model is not None or self.training_mode == "single_class",
            "heuristic_available": True,
        }

    def _coerce_feature_matrix(self, X: Any) -> np.ndarray:
        """Convert supported feature container formats into a numeric 2D NumPy array."""
        if isinstance(X, dict):
            rows = []
            for value in X.values():
                if isinstance(value, dict):
                    features = value.get("quantum_features")
                    if features is None:
                        features = value.get("features")
                    if features is None:
                        continue
                    rows.append(features)
                else:
                    rows.append(value)
            if not rows:
                raise ValueError("No feature vectors found in encoded feature mapping.")
            X = rows
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    def _build_kernel(self, n_features: int):
        if not self.quantum_enabled:
            return None

        if n_features <= 10:
            self.entanglement = "full"
        elif n_features <= 20:
            self.entanglement = "linear"
        else:
            self.entanglement = "circular"

        feature_map = ZZFeatureMap(
            feature_dimension=n_features,
            reps=self.reps,
            entanglement=self.entanglement,
        )

        sampler = StatevectorSampler()

        return FidelityQuantumKernel(
            feature_map=feature_map,
            sampler=sampler,
        )

    def generate_labels(
        self,
        risk_scores: np.ndarray,
        propagation_risks: np.ndarray,
        repo_influences: np.ndarray,
    ) -> np.ndarray:
        labels = []

        for risk, prop, influence in zip(
            risk_scores,
            propagation_risks,
            repo_influences,
        ):
            score = (
                0.60 * float(risk)
                + 0.25 * float(prop)
                + 0.15 * float(influence)
            )

            if score < 0.33:
                labels.append(0)
            elif score < 0.66:
                labels.append(1)
            elif score < 0.85:
                labels.append(2)
            else:
                labels.append(3)

        return np.asarray(labels, dtype=int)

    def _heuristic_predict(self, X: np.ndarray) -> QSVMResult:
        """Fallback prediction used when no trained model is available."""
        if X.ndim != 2 or X.shape[1] < 3:
            raise ValueError("Heuristic prediction requires at least 3 feature columns.")
        risk = np.clip(np.nan_to_num(X[:, 0], nan=0.0), 0.0, 1.0)
        propagation = np.clip(np.nan_to_num(X[:, -1], nan=0.0), 0.0, 1.0)
        influence = np.clip(np.nan_to_num(X[:, -2], nan=0.0), 0.0, 1.0)
        labels = self.generate_labels(risk, propagation, influence)
        probabilities = np.clip(0.5 + 0.5 * risk, 0.0, 1.0)
        metadata = self.get_model_summary()
        metadata["prediction_mode"] = "heuristic"
        metadata["prediction_success"] = True
        return QSVMResult(
            predictions=labels.astype(int).tolist(),
            probabilities=probabilities.astype(float).tolist(),
            labels=[self.RISK_LABELS.get(int(v), "UNKNOWN") for v in labels],
            support_vectors=0,
            quantum_enabled=False,
            metadata=metadata,
            repository_confidence=float(np.mean(probabilities)) if len(probabilities) else 0.0,
            high_risk_modules=int(np.sum(labels >= 2)),
            critical_modules=int(np.sum(labels >= 3)),
        )

    def _should_use_quantum(self, X_scaled: np.ndarray) -> bool:
        if not QISKIT_AVAILABLE:
            return False

        n_samples, n_features = X_scaled.shape

        if n_samples > self.max_quantum_samples:
            return False

        if n_features > 32:
            return False

        unique_rows = len(np.unique(X_scaled, axis=0))
        if unique_rows < 2:
            return False

        return True

    def _reduce_features(self, X_scaled: np.ndarray) -> np.ndarray:
        n_features = X_scaled.shape[1]

        if X_scaled.ndim != 2 or X_scaled.shape[0] == 0:
            self.pca = None
            return X_scaled

        if n_features <= self.max_quantum_features:
            self.pca = None
            return X_scaled

        n_components = max(
            1,
            min(
                self.max_quantum_features,
                n_features,
                X_scaled.shape[0],
            ),
        )

        self.pca = PCA(
            n_components=n_components,
            random_state=42,
        )

        try:
            reduced = self.pca.fit_transform(X_scaled)
        except Exception:
            # Gracefully fall back to the original feature space if PCA cannot be fitted.
            self.pca = None
            return np.nan_to_num(
                X_scaled,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )
        return np.nan_to_num(
            reduced,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

    def fit(self, X: np.ndarray, y: np.ndarray):
        X = self._coerce_feature_matrix(X)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        y = np.asarray(y, dtype=int)
        if y.size == 0:
            raise ValueError("QSVM requires at least one training label.")

        if X.ndim == 1:
            X = X.reshape(1, -1)

        if X.ndim != 2:
            raise ValueError(
                "Training features must be a 2D array."
            )

        if len(X) == 0:
            raise ValueError(
                "QSVM requires at least one training sample."
            )

        if len(X) != len(y):
            raise ValueError(
                "Training features and labels must contain the same number of samples."
            )

        self.model = None
        self.kernel = None
        self.pca = None
        self.training_mode = "classical"
        self.classes_ = []
        self.clear_cache()

        X_scaled = self.scaler.fit_transform(X)
        X_scaled = np.nan_to_num(
            X_scaled,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )
        X_scaled = self._reduce_features(X_scaled)

        self.n_features_ = int(X_scaled.shape[1])
        self.n_samples_ = int(len(X_scaled))

        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            self.training_mode = "single_class"
            self.model = None
            self.classes_ = [int(unique_classes[0])]
            self.n_features_ = int(X_scaled.shape[1])
            return self

        if self._should_use_quantum(X_scaled):
            try:
                self.kernel = self._build_kernel(X_scaled.shape[1])
                self.training_mode = "quantum"
                self.model = SVC(
                    kernel=self.kernel.evaluate,
                    probability=True,
                    class_weight="balanced",
                    random_state=42,
                )
            except Exception:
                self.training_mode = "classical"
                self.kernel = None
                self.model = SVC(
                    kernel="rbf",
                    probability=True,
                    gamma="scale",
                    class_weight="balanced",
                    random_state=42,
                )
        else:
            self.training_mode = "classical"
            self.model = SVC(
                kernel="rbf",
                probability=True,
                gamma="scale",
                class_weight="balanced",
                random_state=42,
            )

        try:
            self.model.fit(X_scaled, y)
        except Exception as exc:
            self.model = None
            self.kernel = None
            self.training_mode = "classical"
            raise RuntimeError("QSVM training failed.") from exc

        self.classes_ = [int(c) for c in self.model.classes_]
        self.n_features_ = int(X_scaled.shape[1])
        self.n_samples_ = int(len(X_scaled))
        return self

    def predict(self, X: np.ndarray) -> QSVMResult:
        X = self._coerce_feature_matrix(X)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        if X.size == 0:
            raise ValueError(
                "QSVM requires at least one prediction sample."
            )
        if X.ndim == 1:
            X = X.reshape(1, -1)

        if X.ndim != 2:
            raise ValueError(
                "Prediction features must be a 2D array."
            )

        if self.training_mode == "single_class":
            label = self.RISK_LABELS.get(
                self.classes_[0],
                "UNKNOWN",
            )
            n = int(len(X))
            return QSVMResult(
                predictions=[self.classes_[0]] * n,
                probabilities=[1.0] * n,
                labels=[label] * n,
                support_vectors=0,
                quantum_enabled=False,
                metadata=self.get_model_summary(),
                repository_confidence=1.0,
                high_risk_modules=int(self.classes_[0] >= 2) * n,
                critical_modules=int(self.classes_[0] >= 3) * n,
            )

        if self.model is None:
            return self._heuristic_predict(X)

        if X.shape[1] != self.scaler.n_features_in_:
            raise ValueError(
                f"Expected {self.scaler.n_features_in_} features but received {X.shape[1]}."
            )

        X_scaled = self.scaler.transform(X)
        X_scaled = np.nan_to_num(
            X_scaled,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )
        if self.pca is not None:
            try:
                X_scaled = self.pca.transform(X_scaled)
            except Exception as exc:
                raise RuntimeError(
                    "Failed to apply PCA transformation during prediction."
                ) from exc
            X_scaled = np.nan_to_num(
                X_scaled,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )
            if X_scaled.shape[1] != self.pca.n_components_:
                raise RuntimeError(
                    f"Unexpected feature dimension after PCA transform: expected {self.pca.n_components_}, got {X_scaled.shape[1]}"
                )
        else:
            if X_scaled.shape[1] != self.n_features_:
                raise RuntimeError(
                    f"Unexpected feature dimension after scaling: expected {self.n_features_}, got {X_scaled.shape[1]}"
                )

        try:
            predictions = self.model.predict(X_scaled)
            probability_matrix = self.model.predict_proba(X_scaled)
        except Exception as exc:
            raise RuntimeError("QSVM prediction failed.") from exc
        probabilities = np.nan_to_num(
            probability_matrix.max(axis=1),
            nan=0.0,
            posinf=1.0,
            neginf=0.0,
        )
        probabilities = np.clip(probabilities, 0.0, 1.0)

        if not (
            len(predictions)
            == len(probabilities)
            == len(probability_matrix)
        ):
            raise RuntimeError(
                "QSVM produced inconsistent prediction outputs."
            )

        repository_confidence = float(np.mean(probabilities))
        high_risk_modules = int(np.sum(predictions >= 2))
        critical_modules = int(np.sum(predictions >= 3))

        metadata = self.get_model_summary()
        metadata["prediction_samples"] = int(len(predictions))
        metadata["prediction_features"] = int(X_scaled.shape[1])
        metadata["probability_range"] = {
            "min": float(np.min(probabilities)),
            "max": float(np.max(probabilities)),
        }
        metadata["prediction_mode"] = self.training_mode
        metadata["prediction_success"] = True
        metadata["class_count"] = len(self.classes_)
        metadata["support_vectors"] = int(len(self.model.support_)) if self.model is not None else 0
        metadata["prediction_ready"] = True
        return QSVMResult(
            predictions=predictions.astype(int).tolist(),
            probabilities=probabilities.astype(float).tolist(),
            labels=[
                self.RISK_LABELS.get(int(p), "UNKNOWN")
                for p in predictions
            ],
            support_vectors=int(len(self.model.support_)),
            quantum_enabled=self.training_mode == "quantum",
            metadata=metadata,
            repository_confidence=repository_confidence,
            high_risk_modules=high_risk_modules,
            critical_modules=critical_modules,
        )

    def classify_modules(
        self,
        module_names: List[str],
        X: np.ndarray,
    ) -> Dict[str, Dict]:
        if len(module_names) == 0:
            raise ValueError("module_names cannot be empty.")
        if isinstance(X, dict):
            ordered_names = list(X.keys())
            if not module_names:
                module_names = ordered_names
            X = self._coerce_feature_matrix(X)
        else:
            X = self._coerce_feature_matrix(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        if len(module_names) != len(X):
            raise ValueError(
                "module_names and feature matrix must contain the same number of samples."
            )
        if len(set(module_names)) != len(module_names):
            raise ValueError(
                "module_names must be unique."
            )
        result = self.predict(X)
        if result is None:
            raise RuntimeError("QSVM prediction produced no result.")

        output: Dict[str, Dict[str, Any]] = {}
        for name, pred, label, prob in zip(
            module_names,
            result.predictions,
            result.labels,
            result.probabilities,
        ):
            output[name] = {
                "predicted_class": label,
                "risk_probability": round(prob, 4),
                "predicted_class_id": int(pred),
                "confidence": round(prob, 4),
                "support_vectors": result.support_vectors,
                "quantum_enabled": result.quantum_enabled,
                "training_mode": result.metadata.get("training_mode"),
                "prediction_mode": result.metadata.get("prediction_mode"),
                "prediction_success": result.metadata.get("prediction_success"),
                "entanglement": result.metadata.get("entanglement"),
                "n_features": result.metadata.get("n_features"),
                "n_samples": result.metadata.get("n_samples"),
                "classes": result.metadata.get("classes"),
                "pca_enabled": result.metadata.get("pca_enabled"),
                "kernel_cache_size": result.metadata.get("kernel_cache_size"),
                "repository_confidence": round(result.repository_confidence, 4),
                "high_risk_modules": result.high_risk_modules,
                "critical_modules": result.critical_modules,
            }

        return output