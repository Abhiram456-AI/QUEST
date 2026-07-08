import json
from pathlib import Path
from typing import Dict, List, Set, Any

class ImpactAnalyzer:
    """
    Analyzes the structural dependency blast radius and change impact of repository components.
    Computes direct/indirect dependents, critical path length, and average dependency depth.
    """

    def __init__(self, outputs_dir: str = "outputs"):
        self.outputs_dir = Path(outputs_dir)

    def load_json(self, path: Path) -> Any:
        if path.exists():
            with open(path, "r") as f:
                try:
                    return json.load(f)
                except Exception:
                    return None
        return None

    def resolve_import_to_component(self, import_name: str, all_components: List[str]) -> str:
        import_name_clean = import_name.replace(".", "/")
        for comp in all_components:
            comp_no_ext = str(Path(comp).with_suffix(""))
            if comp_no_ext.endswith(import_name_clean) or import_name_clean.endswith(comp_no_ext) or import_name_clean in comp_no_ext:
                return comp
        return None

    def get_max_path_length(self, node: str, graph: Dict[str, List[str]], memo: Dict[str, int], visited: Set[str] = None) -> int:
        if visited is None:
            visited = set()
        if node in memo:
            return memo[node]
        if node in visited:
            return 0
        
        visited.add(node)
        neighbors = graph.get(node, [])
        if not neighbors:
            visited.remove(node)
            return 0
        max_len = 0
        for n in neighbors:
            max_len = max(max_len, 1 + self.get_max_path_length(n, graph, memo, visited))
        visited.remove(node)
        memo[node] = max_len
        return max_len

    def get_average_depth(self, node: str, graph: Dict[str, List[str]]) -> float:
        visited = {node: 0}
        queue = [node]
        while queue:
            curr = queue.pop(0)
            dist = visited[curr]
            for neighbor in graph.get(curr, []):
                if neighbor not in visited:
                    visited[neighbor] = dist + 1
                    queue.append(neighbor)
        distances = [d for k, d in visited.items() if k != node]
        return sum(distances) / len(distances) if distances else 0.0

    def analyze_impact(self, target_component: str = None) -> Dict[str, Any]:
        intelligence = self.load_json(self.outputs_dir / "repository_intelligence.json") or {}
        files_data = intelligence.get("files", [])
        
        all_components = [file_report.get("file", "") for file_report in files_data if file_report.get("file")]
        total_files = len(all_components) or 1

        # Build dependency graphs
        imports_graph = {}
        dependents_graph = {comp: list() for comp in all_components}

        for file_report in files_data:
            comp = file_report.get("file", "")
            if not comp:
                continue
            
            dependencies = file_report.get("dependencies", {})
            imports_list = dependencies.get("imports", [])
            
            resolved_imports = []
            for imp in imports_list:
                resolved = self.resolve_import_to_component(imp, all_components)
                if resolved and resolved != comp:
                    resolved_imports.append(resolved)
                    if comp not in dependents_graph[resolved]:
                        dependents_graph[resolved].append(comp)
            
            imports_graph[comp] = resolved_imports

        # Helper to compute transitive dependents
        def get_transitive_dependents(start_node: str) -> Set[str]:
            visited = set()
            queue = [start_node]
            while queue:
                current = queue.pop(0)
                for neighbor in dependents_graph.get(current, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            return visited

        # If a specific component is requested
        if target_component:
            target_clean = target_component.strip()
            if target_clean.startswith("file:"):
                target_clean = target_clean[5:]
            
            if target_clean not in dependents_graph:
                target_clean_lower = target_clean.replace("\\", "/").lower()
                matches = []
                for p in all_components:
                    p_lower = p.replace("\\", "/").lower()
                    p_filename = p_lower.split("/")[-1]
                    target_filename = target_clean_lower.split("/")[-1]
                    if p_filename == target_filename:
                        is_test = "test_" in p_lower or "/tests/" in p_lower
                        matches.append((0 if not is_test else 1, len(p_lower), p))
                    elif target_clean_lower in p_lower:
                        is_test = "test_" in p_lower or "/tests/" in p_lower
                        matches.append((2 if not is_test else 3, len(p_lower), p))
                    elif p_lower in target_clean_lower:
                        is_test = "test_" in p_lower or "/tests/" in p_lower
                        matches.append((4 if not is_test else 5, len(p_lower), p))
                if matches:
                    matches.sort(key=lambda x: (x[0], x[1]))
                    target_clean = matches[0][2]

            if target_clean in dependents_graph:
                direct = sorted(dependents_graph[target_clean])
                transitive = sorted(list(get_transitive_dependents(target_clean)))
                indirect = sorted(list(set(transitive) - set(direct)))
                
                # Compute critical path and avg depth
                memo = {}
                crit_path_len = self.get_max_path_length(target_clean, dependents_graph, memo)
                avg_depth = self.get_average_depth(target_clean, dependents_graph)

                transitive_count = len(transitive)
                if transitive_count > 12:
                    rating = "CRITICAL"
                elif transitive_count > 6:
                    rating = "HIGH"
                elif transitive_count > 1:
                    rating = "MEDIUM"
                else:
                    rating = "LOW"

                return {
                    "component": target_clean,
                    "direct_dependents": direct,
                    "direct_count": len(direct),
                    "indirect_dependents": indirect,
                    "indirect_count": len(indirect),
                    "transitive_dependents": transitive,
                    "transitive_count": transitive_count,
                    "critical_path_length": crit_path_len,
                    "average_dependency_depth": round(avg_depth, 2),
                    "impact_rating": rating,
                    "impact_score": round((len(direct) * 0.4 + transitive_count * 0.6) / total_files, 4)
                }
            else:
                return {
                    "error": f"Component {target_component} not found in analyzed repository."
                }

        # Otherwise, run impact analysis for all components and save report
        impact_reports = {}
        for comp in all_components:
            direct = sorted(dependents_graph[comp])
            transitive = sorted(list(get_transitive_dependents(comp)))
            indirect = sorted(list(set(transitive) - set(direct)))
            
            memo = {}
            crit_path_len = self.get_max_path_length(comp, dependents_graph, memo)
            avg_depth = self.get_average_depth(comp, dependents_graph)

            transitive_count = len(transitive)
            if transitive_count > 12:
                rating = "CRITICAL"
            elif transitive_count > 6:
                rating = "HIGH"
            elif transitive_count > 1:
                rating = "MEDIUM"
            else:
                rating = "LOW"

            impact_reports[comp] = {
                "direct_dependents": direct,
                "direct_count": len(direct),
                "indirect_dependents": indirect,
                "indirect_count": len(indirect),
                "transitive_dependents": transitive,
                "transitive_count": transitive_count,
                "critical_path_length": crit_path_len,
                "average_dependency_depth": round(avg_depth, 2),
                "impact_rating": rating,
                "impact_score": round((len(direct) * 0.4 + transitive_count * 0.6) / total_files, 4)
            }

        # Save to file
        output_file = self.outputs_dir / "impact_analysis.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(impact_reports, f, indent=4)

        return impact_reports
