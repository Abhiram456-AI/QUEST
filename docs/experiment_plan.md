# QUEST Academic Experiment Plan

This document outlines the validation plan, experimental configurations, and robustness checks used to evaluate the QUEST framework.

---

## 1. Experimental Objectives

1. **Prioritization Robustness**: Verify that the adaptive Unified Decision Priority Index (UDPI) successfully ranks critical code components under metric perturbations.
2. **Confidence Calibration**: Validate that the multiplicative confidence score accurately penalizes incomplete evidence and agent disagreement.
3. **Counterfactual Prediction Accuracy**: Verify that counterfactual Monte Carlo simulations converge to stable projected repository reliability index improvements.
4. **XAI Completeness**: Evaluate the completeness of synthesized explanations using the Explainability Score metric.

---

## 2. Experimental Configurations

### A. Prioritization Robustness (Schrödinger Perturbation Trials)
* **Process**: Execute 100 perturbation trials for each component in the repository.
* **Perturbation Model**: Introduce $\pm 5\%$ Gaussian noise to the input metrics (trust score, walk score, QVNN probability, complexity, agent average severity).
* **Metric**: **Decision Consistency Index** (percentage of trials where the output priority level remains identical).
* **Success Criteria**: Consistency Index $\ge 90\%$ for top-prioritized components.

### B. Sensitivity Analysis (Kendall's Tau)
* **Process**: Perturb each feature weight individually by $\pm 10\%$ and measure the resulting rank shifts of all components.
* **Metric**: Kendall's Tau Rank Correlation Coefficient ($\tau$):
  $$\tau = \frac{C - D}{\frac{1}{2} n(n-1)}$$
  Where $C$ is the number of concordant pairs and $D$ is the number of discordant pairs.
* **Success Criteria**: Calculate and record weight sensitivity in `outputs/weights_sensitivity_report.json` to identify which metric changes the prioritization ranks the most.

### C. Counterfactual Scenario Simulation (Monte Carlo Trials)
* **Process**: Run 1,000 Monte Carlo counterfactual refactoring trials for targeted files.
* **Refactoring Assumptions**:
  * Lines of Code (LOC) reduction: sampled with mean $40\%$ ($\sigma = 8\%$).
  * Cyclomatic Complexity reduction: sampled with mean $45\%$ ($\sigma = 8\%$).
  * Dependency coupling reduction: sampled with mean $30\%$ ($\sigma = 8\%$).
* **Metrics**:
  * Projected Delta Improvement (counterfactual reliability index delta).
  * Standard Error of the Mean (SEM) of the counterfactual distribution.
  * normality check (Skewness & Kurtosis).
  * $95\%$ Confidence Interval.

### D. Multi-source Agent Consensus Verification
* **Process**: Evaluate Reviewer, Critic, Security, and Quantum agent severity outputs.
* **Thresholds**:
  * **Severe Disagreement**: Severity range $\ge 3$ (e.g. `CRITICAL` vs `LOW/INFO`). Triggers Brier cap of $0.30$.
  * **Moderate Disagreement**: Severity range $\le 2$ (e.g. `HIGH` vs `MEDIUM`). Triggers relaxed cap of $0.55$.
