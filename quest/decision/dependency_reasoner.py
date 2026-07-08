import json
from pathlib import Path
from typing import Dict, List, Set, Any

class DependencyReasoner:
    """
    Constructs lineage paths explaining the import relationships and incoming flows of components.
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

    def build_import_graphs(self) -> tuple:
        intelligence = self.load_json(self.outputs_dir / "repository_intelligence.json") or {}
        files_data = intelligence.get("files", [])
        
        all_components = [file_report.get("file", "") for file_report in files_data if file_report.get("file")]
        
        imports_graph = {comp: [] for comp in all_components}
        dependents_graph = {comp: [] for comp in all_components}

        for file_report in files_data:
            comp = file_report.get("file", "")
            if not comp:
                continue
            
            dependencies = file_report.get("dependencies", {})
            imports_list = dependencies.get("imports", [])
            
            for imp in imports_list:
                resolved = self.resolve_import_to_component(imp, all_components)
                if resolved and resolved != comp:
                    imports_graph[comp].append(resolved)
                    dependents_graph[resolved].append(comp)
                    
        return imports_graph, dependents_graph, all_components

    def get_shortest_path(self, start: str, end: str, graph: Dict[str, List[str]]) -> List[str]:
        """
        Finds the shortest path of imports from start node to end node.
        """
        if start == end:
            return [start]
        visited = {start}
        queue = [[start]]
        while queue:
            path = queue.pop(0)
            node = path[-1]
            for neighbor in graph.get(node, []):
                if neighbor == end:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return []

    def reason_dependencies(self, target_component: str) -> Dict[str, Any]:
        imports_graph, dependents_graph, all_components = self.build_import_graphs()
        
        target_clean = target_component.strip()
        if target_clean.startswith("file:"):
            target_clean = target_clean[5:]
            
        if target_clean not in all_components:
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

        if target_clean not in all_components:
            return {"error": f"Component {target_component} not found."}

        # 1. Incoming Flow: How is this file reached from main.py or top-level tests?
        paths_from_main = []
        if "main.py" in all_components and target_clean != "main.py":
            # Search path in dependents graph (going backwards from main.py or forwards in imports_graph)
            # A path in imports_graph from main.py to target_clean
            path = self.get_shortest_path("main.py", target_clean, imports_graph)
            if path:
                paths_from_main = path

        # 2. Find any test files that import this component
        test_entries = []
        for comp in all_components:
            if "test_" in comp.lower() and comp != target_clean:
                path = self.get_shortest_path(comp, target_clean, imports_graph)
                if path:
                    test_entries.append(path)

        # 3. Direct incoming dependencies (what directly imports this)
        direct_inputs = dependents_graph.get(target_clean, [])

        # 4. Direct outgoing dependencies (what this directly imports)
        direct_outputs = imports_graph.get(target_clean, [])

        # Formulate explanation sentence
        if paths_from_main:
            flow_desc = " -> ".join(paths_from_main)
            explanation = f"Component {target_clean} is integrated into the core execution pipeline via: {flow_desc}."
        elif direct_inputs:
            explanation = f"Component {target_clean} is imported directly by: {', '.join(direct_inputs)}."
        else:
            explanation = f"Component {target_clean} has no incoming repository imports (isolated entry point or standalone script)."

        return {
            "component": target_clean,
            "lineage_explanation": explanation,
            "shortest_path_from_main": paths_from_main,
            "direct_incoming_imports": direct_inputs,
            "direct_outgoing_imports": direct_outputs,
            "test_coverage_paths": test_entries[:3] # Show up to 3 test linkages
        }
