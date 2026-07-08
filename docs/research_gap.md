# QUEST Research Gap Analysis

This document outlines the specific research gap addressed by QUEST, contrasting it with existing academic literature and industrial implementations in software engineering and automated program repair.

---

## 1. Traditional Software Risk Analysis (Prior Art)

Prior art in software repository analytics relies on classical statistical models (e.g., linear regressions, random forests) trained on historical commit metadata, cyclomatic complexity, and code churn. 

```
[Repository Source Code] 
        │
        ▼
[Static Metrics: LOC, Complexity] ──► [Linear Regression] ──► [Uncalibrated Priority Score]
```

* **Limitations**:
  * **Graph Topology Ignoring**: Classical regressions do not compute transitive dependency closures, missing hidden risk bottlenecks.
  * **Static Weights**: Prior models apply static heuristic coefficients that fail to adapt to varying repository contexts (e.g. security-heavy vs. complexity-heavy codebases).
  * **Lack of Counterfactual Reasoning**: Existing systems cannot simulate the projected overall repository health gains of hypothetical refactorings without physical code changes.

---

## 2. QUEST Innovation (The Research Gap Filled)

QUEST bridges the gap between quantum computation simulations and automated software engineering decision intelligence.

```
                  ┌──► Quantum Walk (CTQW) Systemic Risk
                  │
[Source Code] ───┼──► QAOA Scheduling Optimization
                  │
                  └──► QVNN Classifier Local Reliability
                          │
                          ▼
                 [Adaptive Weighting] ──► [Decision Consistency & Reliability]
```

### Key Contributions:
1. **Quantum Graph Walks for Propagation Mapping**: QUEST introduces Continuous-Time Quantum Walks (CTQW) to compute risk transfer probabilities over software dependency graphs, modeling transitive propagation behavior that classical centrality metrics miss.
2. **Context-Aware Adaptive Priority Indexing**: The priority ranker computes component rankings using dynamically adjusted weights derived from metric variance and active file context, eliminating static heuristics.
3. **Calibrated Confidence & Schrödinger Uncertainty Perturbations**: Rather than claiming absolute certainty, QUEST introduces geometric mean confidence calibration (with disagreement penalties) and perturbation trials ($\pm 5\%$ Gaussian noise) to measure decision stability under uncertainty.
4. **Contrastive Explanations and Decision Memory**: QUEST incorporates contrastive XAI explanations (justifying chosen classifications over adjacent boundaries) and loops prior decisions back into the reasoning flow via a historical feedback loop.
