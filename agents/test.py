import sys
from pathlib import Path

# Add project root to imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Import the same builders used by main.py.
# Replace these imports if your module paths differ.
from parser.repository_parser import RepositoryParser
from reasoning.query_engine import QueryEngine
from context.graph_builder import DependencyGraphBuilder
from context.function_graph_builder import FunctionGraphBuilder
from context.knowledge_graph_builder import KnowledgeGraphBuilder
from features.repository_metrics import RepositoryMetrics
from reasoning.path_engine import PathEngine
from reasoning.impact_engine import ImpactEngine
from reasoning.coupling_engine import CouplingEngine
from reasoning.risk_engine import RiskEngine
from reasoning.execution_engine import ExecutionEngine
from agents.orchestrator import AgentOrchestrator

REPO_PATH = "/Users/abhiramdurbhakula/PythonProjects/AICouncil"

print("Building repository intelligence...")

# Mirror the initialization sequence from main.py.
# Do not create a RepositoryAnalyzer; this project uses RepositoryParser.
parser = RepositoryParser(REPO_PATH)
repository = parser.parse()


builder = DependencyGraphBuilder()
graph = builder.build(repository)

metrics_engine = RepositoryMetrics(graph, repository)
metrics = metrics_engine.compute()

function_builder = FunctionGraphBuilder()
function_graph = function_builder.build(repository)

knowledge_builder = KnowledgeGraphBuilder()
knowledge_graph = knowledge_builder.build(repository)

dependency_path_engine = PathEngine(graph)
function_path_engine = PathEngine(function_graph)
knowledge_path_engine = PathEngine(knowledge_graph)

execution_engine = ExecutionEngine(function_graph)
impact_engine = ImpactEngine(graph)
coupling_engine = CouplingEngine(graph)

risk_engine = RiskEngine(
    metrics=metrics,
    impact_engine=impact_engine,
    coupling_engine=coupling_engine,
)

query_engine = QueryEngine(
    repository=repository,
    dependency_graph=graph,
    function_graph=function_graph,
    knowledge_graph=knowledge_graph,
    metrics=metrics,
    dependency_path_engine=dependency_path_engine,
    function_path_engine=function_path_engine,
    knowledge_path_engine=knowledge_path_engine,
    impact_engine=impact_engine,
    coupling_engine=coupling_engine,
    risk_engine=risk_engine,
    execution_engine=execution_engine,
)

print("Building multi-agent orchestrator...")
orchestrator = AgentOrchestrator(query_engine)

print("Running analysis...\n")
result = orchestrator.analyze("show risk of orchestrator")

print("FINAL RESULT:\n")
print(result)