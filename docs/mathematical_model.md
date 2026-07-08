# QUEST: Formal Mathematical Model Specification

This document provides the formal mathematical specification for the **QUEST (Quantum-assisted Unified Evaluation and Scheduling Tool)** framework, covering all computational phases from raw metric normalization to Phase 7 prescriptive decision intelligence.

---

## 1. Phase 1 & 2: Structural Metrics and Trust Vector Space

### A. Graph Representation of Software Repositories
A software repository is modeled as a directed call and import graph $G = (V, E)$, where:
* $V = \{v_1, v_2, \dots, v_N\}$ is the set of $N$ source code components (files/modules).
* $E \subseteq V \times V$ represents the directed dependency edges. An edge $e_{jk} = (v_j, v_k) \in E$ indicates that component $v_j$ imports or calls component $v_k$.

### B. Feature Mapping and Normalization (Phase 2)
For each component $v_j$, we extract a raw structural metric vector $\mathbf{m}_j = [C_j, D_j, S_j, R_j]^T$, where:
* $C_j$: Cyclomatic Complexity (McCabe Complexity).
* $D_j$: Dependency Coupling (out-degree in the dependency graph).
* $S_j$: Security Vulnerabilities (flagged static analysis issues count).
* $R_j$: Local Code Reliability (determined from code coverage and test density).

These raw metrics are mapped to a normalized trust vector $\mathbf{x}_j = [x_{j,1}, x_{j,2}, x_{j,3}, x_{j,4}]^T \in [0, 1]^4$ using min-max scaling boundaries:

$$x_{j,k} = \text{clip}\left(\frac{m_{j,k} - \min(M_k)}{\max(M_k) - \min(M_k)}, 0.0, 1.0\right)$$

The **Composite Trust Score** $T_j$ of the component is then calculated as:

$$T_j = \omega_{\text{rel}} \cdot x_{j,4} + (1 - \omega_{\text{rel}}) \cdot \left( 1 - \frac{0.3 \cdot x_{j,1} + 0.2 \cdot x_{j,2} + 0.3 \cdot x_{j,3}}{0.8} \right)$$

Where $\omega_{\text{rel}} = 0.5$ is the relative weight of the local reliability profile.

---

## 2. Phase 3: Quantum Intelligence Models

### A. Continuous-Time Quantum Walk (CTQW) Risk Propagation
To model the systemic risk propagation through the dependency graph, we define a quantum state space over the vertices of $G$. The Hamiltonian of the walk is defined using the graph Laplacian matrix $L = D - A$, where:
* $A$ is the adjacency matrix ($A_{jk} = 1$ if $(v_j, v_k) \in E$, else $0$).
* $D$ is the diagonal degree matrix ($D_{jj} = \sum_k A_{jk}$).

The time evolution of the state vector $|\psi(t)\rangle$ is governed by the Schrödinger equation ($h = 1$):

$$i \frac{d}{dt} |\psi(t)\rangle = L |\psi(t)\rangle \implies |\psi(t)\rangle = e^{-i L t} |\psi(0)\rangle$$

The unitary transition operator is defined as $U(t) = e^{-i L t}$. If the walk is initialized at a compromised component $v_j$ (i.e., $|\psi(0)\rangle = |j\rangle$), the probability of the risk transferring to component $v_k$ at time $t$ is:

$$P_{j \to k}(t) = \left| \langle k | U(t) | j \rangle \right|^2 = \left| \left( e^{-i L t} \right)_{k,j} \right|^2$$

To evaluate the **Systemic Risk Index** $W_k$ of a component $v_k$ as a risk bottleneck, we integrate the incoming risk propagation probability from all other nodes over a time interval $[0, T_{max}]$:

$$W_k = \frac{1}{T_{max} \cdot (N-1)} \int_{0}^{T_{max}} \sum_{j \neq k} P_{j \to k}(t) \, dt$$

---

### B. Quantum Approximate Optimization Algorithm (QAOA) for Verification Scheduling
QAOA is used to compute an optimal verification schedule by partitioning the repository graph into highly critical test boundaries. This is mapped to a Max-Cut optimization problem on the graph $G$.

The cost Hamiltonian $H_C$ encodes the cut size:

$$H_C = \frac{1}{2} \sum_{(v_j, v_k) \in E} w_{jk} \left( I - \sigma_j^z \otimes \sigma_k^z \right)$$

Where $w_{jk}$ is the edge weight (coupling centrality) and $\sigma^z$ is the Pauli-Z operator. The mixing Hamiltonian $H_B$ is:

$$H_B = \sum_{j=1}^{N} \sigma_j^x$$

For a circuit depth $p$, the parameterized QAOA state is prepared by applying alternating operators:

$$|\gamma, \beta\rangle = \left( \prod_{m=1}^{p} e^{-i \beta_m H_B} e^{-i \gamma_m H_C} \right) |+\rangle^{\otimes N}$$

Classical optimization computes the parameters $(\gamma^*, \beta^*)$ that maximize the expectation value:

$$(\gamma^*, \beta^*) = \arg\max_{\gamma, \beta} \langle \gamma, \beta | H_C | \gamma, \beta \rangle$$

The resulting bitstring output of the measurement in the computational basis defines the optimal verification partition schedule, represented as the **QAOA Resource Rank** $Q_i \in [0, 1]$.

---

### C. Variational Quantum Neural Network (QVNN) for Reliability Prediction
The QVNN predicts local runtime stability. The normalized feature vector $\mathbf{x} \in [0,1]^4$ is encoded into an $n$-qubit state using a non-linear feature map $U_{\Phi}(\mathbf{x})$:

$$|\psi(\mathbf{x})\rangle = U_{\Phi}(\mathbf{x}) |0\rangle^{\otimes n}$$

We apply a parameterized variational ansatz $V(\theta)$ composed of alternating layers of single-qubit rotations ($R_y, R_z$) and entangling CNOT gates:

$$|\psi(\mathbf{x}, \theta)\rangle = V(\theta) |\psi(\mathbf{x})\rangle$$

The reliability classification probability $V_i$ is determined by measuring the expectation value of the Pauli-Z operator on the readout qubit:

$$V_i = P_{\text{reliability}}(\mathbf{x}) = \frac{1 + \langle \psi(\mathbf{x}, \theta) | Z_0 | \psi(\mathbf{x}, \theta) \rangle}{2} \in [0, 1]$$

The parameters $\theta$ are trained classically to minimize cross-entropy loss relative to historical runtime crash data.

---

## 3. Phase 7: Prescriptive Decision Intelligence Optimization

### A. Context-Aware Adaptive UDPI prioritisation
The Unified Decision Priority Index (UDPI) resolves scheduling priorities by dynamically balancing features based on repository variance and active component context:

$$\text{UDPI}_i = w_T \cdot (1 - T_i) + w_W \cdot W_i + w_Q \cdot Q_i + w_V \cdot (1 - V_i) + w_A \cdot A_i$$

Where:
* $T_i$: Trust Score (Phase 2).
* $W_i$: Quantum Walk Score (Phase 3).
* $Q_i$: QAOA Rank (Phase 3).
* $V_i$: QVNN Probability (Phase 3).
* $A_i$: Verification Agent Average Severity (Phase 4).

The adaptive weight $w_k$ for each parameter is computed dynamically:

$$w_k = \frac{\bar{w}_k}{\sum_m \bar{w}_m}$$

$$\bar{w}_k = \max\left(0.05, \text{var}_k \cdot \text{coverage}_k \cdot \text{confidence}_k \cdot \text{context}_k\right)$$

Where:
* **Metric Variance ($\text{var}_k$)**: Computed over the repository: $\text{var}_k = \text{Variance}(\{f_k(i)\}_{i=1}^N)$. Cyclomatic complexities are scaled using $C_i / \max(1, C_{max})$ to ensure variances are bounded in the same scale.
* **Evidence Coverage ($\text{coverage}_k$)**: Ratio of verified artifacts present in the outputs directory.
* **Context Modifiers ($\text{context}_k$)**:
  * *Security Context ($A_i > 0.5$)*:
    $$\bar{w}_{\text{agents}} \leftarrow \bar{w}_{\text{agents}} + 0.15, \quad \bar{w}_{\text{trust}} \leftarrow \bar{w}_{\text{trust}} + 0.05$$
  * *Complexity Context ($C_i > 0.5$)*:
    $$\bar{w}_{\text{complexity}} \leftarrow \bar{w}_{\text{complexity}} + 0.15, \quad \bar{w}_{\text{qaoa}} \leftarrow \bar{w}_{\text{qaoa}} + 0.05$$
  * *Systemic Context ($W_i > 0.5$)*:
    $$\bar{w}_{\text{quantum\_walk}} \leftarrow \bar{w}_{\text{quantum\_walk}} + 0.15$$

---

### B. Multiplicative Confidence Calibration
Confidence is calculated as the multiplicative geometric mean of five fraction parameters, ensuring that a deficit in any single phase heavily penalizes the overall certainty:

$$\text{Confidence} = \left( C_{\text{Evidence}} \times C_{\text{Reasoning}} \times C_{\text{Prediction}} \times C_{\text{Completeness}} \times C_{\text{Consistency}} \right)^{0.2}$$

Where:
* **Evidence Reliability ($C_{\text{Evidence}}$)**: Fraction of evaluated evidence present in reasoning paths.
* **Reasoning Agreement ($C_{\text{Reasoning}}$)**: Metric representing verification agent consensus. If $M$ is the count of the most common severity rating out of $K$ agents:
  $$C_{\text{Reasoning}} = 0.5 + 0.5 \cdot \left(\frac{M}{K}\right)$$
* **Prediction Stability ($C_{\text{Prediction}}$)**: Variance of QVNN classifier output under noise.
* **Data Completeness ($C_{\text{Completeness}}$)**: Proportion of non-null metrics.
* **Cross-Phase Consistency ($C_{\text{Consistency}}$)**: Correlation distance between inverse trust ranks, quantum walk risk ranks, and final UDPI priority ranks.

**Disagreement Penalty Cap**:
If verification agents exhibit severe disagreement (severity value delta $\ge 3$ steps on a 5-step scale), a Brier-based penalty cap is applied:

$$\text{Confidence} \leftarrow \min(0.30, \text{Confidence})$$

For moderate disagreement (severity value delta $\le 2$ steps), the cap is relaxed to:

$$\text{Confidence} \leftarrow \min(0.55, \text{Confidence})$$

---

### C. Uncertainty Modeling & Robustness
To separate determinism from truth, we define:
1. **Decision Consistency**: The percentage of perturbation trials that yield the identical priority category when the input vector $\mathbf{x}$ is subjected to Gaussian noise:
   $$\mathbf{x}' = \mathbf{x} + \mathbf{\epsilon}, \quad \mathbf{\epsilon} \sim \mathcal{N}(\mathbf{0}, \sigma^2 \mathbf{I}) \text{ with } \sigma = 0.05$$
2. **Decision Reliability**:
   $$\text{Reliability} = \text{Decision Consistency} \times C_{\text{Evidence}}$$

---

### D. Explainability Score
The Explainability Score $X_i$ is computed as the average of four validation criteria:

$$X_i = \frac{\text{Coverage}_{\text{phases}} + \text{Coverage}_{\text{numerical}} + \text{Completeness}_{\text{reasoning}} + \text{Status}_{\text{validation}}}{4} \times 100\%$$
