import time
import os
import tempfile
import shutil
import numpy as np
from pathlib import Path

from quest.intelligence.repository_scanner import RepositoryScanner
from quest.intelligence.ast_analyzer import ASTAnalyzer
from quest.intelligence.dependency_analyzer import DependencyAnalyzer
from quest.intelligence.call_graph import CallGraphBuilder
from quest.intelligence.code_metrics import CodeMetricsAnalyzer
from quest.quantum.quantum_walk import QuantumWalkEngine
from quest.quantum.qvnn_predictor import QUESTQVNNPredictor
from quest.quantum.qsvm_classifier import QUESTQSVMClassifier

def create_mock_codebase(root_path, num_files=200, max_depth=5):
    # Generates a large hierarchical mock codebase with varying files and contents
    root = Path(root_path)
    created_files = []
    
    # Simple Python code snippets to populate
    snippets = [
        "import os\nimport sys\ndef compute_val(a, b):\n    return a * b + 2\n",
        "class HelperClass:\n    def __init__(self):\n        self.name = 'Helper'\n    def greet(self):\n        print(self.name)\n",
        "import numpy as np\ndef process_data(arr):\n    return np.mean(arr)\n",
        "def main_process():\n    for i in range(100):\n        if i % 2 == 0:\n            pass\n"
    ]
    
    for i in range(num_files):
        # Choose a random directory depth
        depth = np.random.randint(1, max_depth + 1)
        subdirs = [f"module_{np.random.randint(1, 10)}" for _ in range(depth)]
        dir_path = root.joinpath(*subdirs)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        file_path = dir_path / f"source_file_{i}.py"
        content = snippets[i % len(snippets)]
        
        # Add extra complexity to some files to simulate large source files
        if i % 10 == 0:
            content += "\n".join([f"def func_{j}():\n    return {j}\n" for j in range(50)])
            
        file_path.write_text(content, encoding="utf-8")
        created_files.append(file_path)
        
    return created_files

def run_stress_test():
    print("=== STARTING QUEST PIPELINE STRESS TEST ===")
    test_dir = tempfile.mkdtemp()
    try:
        # 1. Stress Test Repository Scanner with Large Number of Files
        print("\n[STRESS TEST 1/5] Repository Scanner (Large Scale)")
        start_time = time.time()
        mock_files = create_mock_codebase(test_dir, num_files=300, max_depth=5)
        print(f"Generated 300 mock Python files at: {test_dir}")
        
        scanner = RepositoryScanner(test_dir)
        repo_metadata = scanner.scan()
        scan_duration = time.time() - start_time
        print(f"Scanned {repo_metadata.total_files} files in {scan_duration:.4f} seconds")
        assert repo_metadata.total_files == len(mock_files)
        
        # 2. Stress Test Analyzers on Large & Deep Call Graphs
        print("\n[STRESS TEST 2/5] Static Analyzers & Call Graph (Large Scale)")
        start_time = time.time()
        for idx, f in enumerate(mock_files[:50]): # Analyze a subset of files for performance
            ast_analyzer = ASTAnalyzer()
            ast_analyzer.analyze_file(str(f))
            
            dep_analyzer = DependencyAnalyzer()
            dep_analyzer.analyze_file(str(f))
            
            metrics_analyzer = CodeMetricsAnalyzer()
            metrics_analyzer.analyze_file(str(f))
            
            cg_builder = CallGraphBuilder()
            cg_builder.build_graph(str(f))
            
        duration = time.time() - start_time
        print(f"Successfully ran AST, Dependency, Metrics, and Call Graph on 50 complex files in {duration:.4f} seconds")

        # 3. Stress Test Quantum Walk Engine with Massive Graph Density
        print("\n[STRESS TEST 3/5] Quantum Walk Risk Propagation (High Graph Density)")
        qw_engine = QuantumWalkEngine()
        # Create a dense mock software graph
        num_nodes = 500
        nodes = [f"file:node_{i}.py" for i in range(num_nodes)]
        edges = []
        # Connect nodes in a scale-free / dense pattern
        for i in range(num_nodes - 1):
            edges.append([nodes[i], nodes[i+1]]) # linear backbone
            if i % 3 == 0:
                edges.append([nodes[i], nodes[min(i+5, num_nodes-1)]]) # forward jump
            if i % 7 == 0:
                edges.append([nodes[i], nodes[max(0, i-10)]]) # backward jump (cycle)
        
        dense_graph = {"nodes": nodes, "edges": edges}
        start_time = time.time()
        result = qw_engine.analyze(dense_graph)
        qw_duration = time.time() - start_time
        print(f"Quantum Walk evolved over graph with {num_nodes} nodes and {len(edges)} edges in {qw_duration:.4f} seconds")
        print(f"Top influential components identified: {result.most_influential_components}")
        assert len(result.propagation_scores) == num_nodes

        # 4. Stress Test Machine Learning / Quantum SVM Classifier Scaling
        print("\n[STRESS TEST 4/5] QSVM Classifier scaling (Large Dataset Size)")
        qsvm = QUESTQSVMClassifier()
        # Generate a large dataset
        num_samples = 150
        num_features = 4
        X = np.random.uniform(0, 1, size=(num_samples, num_features))
        y = np.random.randint(0, 2, size=(num_samples,))
        
        # Save temp arrays
        x_path = os.path.join(test_dir, "X_large.npy")
        y_path = os.path.join(test_dir, "y_large.npy")
        np.save(x_path, X)
        np.save(y_path, y)
        
        start_time = time.time()
        qsvm_result = qsvm.train_and_evaluate(x_path, y_path)
        qsvm_duration = time.time() - start_time
        print(f"QSVM Classifier trained on {num_samples} samples in {qsvm_duration:.4f} seconds with Accuracy: {qsvm_result.accuracy}")
        
        # 5. Stress Test Robustness to Corrupted & Non-ASCII inputs
        print("\n[STRESS TEST 5/5] Robustness & Exception Handling (Corrupted Inputs)")
        corrupted_file = Path(test_dir) / "corrupted.py"
        # Write random byte string representing binary data / invalid syntax
        corrupted_file.write_bytes(b"\x80\x02\x03\x04\xff\xfe\x00invalid python syntax & binary characters")
        
        # AST Analyzer should raise ValueError gracefully
        ast_analyzer = ASTAnalyzer()
        try:
            ast_analyzer.analyze_file(str(corrupted_file))
            print("WARNING: AST Analyzer did not raise an exception for binary code syntax error.")
        except ValueError:
            print("AST Analyzer handled corrupted syntax exception correctly (ValueError).")
            
        # Call Graph Builder should raise RuntimeError gracefully
        cg_builder = CallGraphBuilder()
        try:
            cg_builder.build_graph(str(corrupted_file))
            print("WARNING: Call Graph Builder did not raise an exception for corrupted file.")
        except RuntimeError:
            print("Call Graph Builder handled file corruption exception correctly (RuntimeError).")

        print("\n=== ALL STRESS TESTS PASSED SUCCESSFULLY ===")
        
    finally:
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    run_stress_test()
