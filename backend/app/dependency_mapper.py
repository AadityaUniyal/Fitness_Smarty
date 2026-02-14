"""
DependencyMapper class for tracking file relationships and dependencies.
Validates Requirements 1.1, 1.2, 1.5
"""

from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import networkx as nx

from .file_analyzer import FileInfo, FileType


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between two files"""
    source: Path
    target: Path
    import_statement: str
    dependency_type: str  # 'import', 'relative_import', 'module_import'


@dataclass
class DependencyCluster:
    """A cluster of related files that should be organized together"""
    files: Set[Path]
    cluster_type: str  # 'frontend', 'backend', 'shared'
    internal_dependencies: List[DependencyEdge]
    external_dependencies: List[DependencyEdge]


class DependencyMapper:
    """Maps and analyzes file dependencies for safe reorganization"""
    
    def __init__(self, project_root: Path):
        """Initialize DependencyMapper with project root directory"""
        self.project_root = Path(project_root)
        self.dependency_graph = nx.DiGraph()
        self.file_infos: Dict[Path, FileInfo] = {}
        self.dependency_edges: List[DependencyEdge] = []
        self.clusters: List[DependencyCluster] = []

    def build_dependency_graph(self, file_infos: List[FileInfo]) -> nx.DiGraph:
        """Build a directed graph of file dependencies"""
        self.file_infos = {info.path: info for info in file_infos}
        self.dependency_graph.clear()
        self.dependency_edges.clear()
        
        # Add all files as nodes
        for file_info in file_infos:
            self.dependency_graph.add_node(
                file_info.path,
                file_type=file_info.file_type,
                size=file_info.size_bytes,
                is_config=file_info.is_config,
                is_test=file_info.is_test
            )
        
        # Add dependency edges
        for file_info in file_infos:
            self._add_file_dependencies(file_info)
        
        return self.dependency_graph

    def _add_file_dependencies(self, file_info: FileInfo):
        """Add dependencies for a single file to the graph"""
        for import_stmt in file_info.imports:
            target_files = self._resolve_import_to_files(import_stmt, file_info)
            
            for target_file in target_files:
                if target_file in self.file_infos:
                    # Determine dependency type
                    dep_type = self._classify_dependency_type(import_stmt, file_info, target_file)
                    
                    # Add edge to graph
                    self.dependency_graph.add_edge(
                        file_info.path,
                        target_file,
                        import_statement=import_stmt,
                        dependency_type=dep_type
                    )
                    
                    # Store dependency edge
                    edge = DependencyEdge(
                        source=file_info.path,
                        target=target_file,
                        import_statement=import_stmt,
                        dependency_type=dep_type
                    )
                    self.dependency_edges.append(edge)

    def _resolve_import_to_files(self, import_stmt: str, file_info: FileInfo) -> List[Path]:
        """Resolve an import statement to actual file paths"""
        resolved_files = []
        
        # Handle different types of imports based on file type
        if file_info.file_type == FileType.BACKEND_PYTHON:
            resolved_files.extend(self._resolve_python_import(import_stmt, file_info.path))
        elif file_info.file_type in [FileType.FRONTEND_REACT, FileType.FRONTEND_TYPESCRIPT, FileType.FRONTEND_JAVASCRIPT]:
            resolved_files.extend(self._resolve_js_import(import_stmt, file_info.path))
        
        return resolved_files

    def _resolve_python_import(self, import_stmt: str, source_file: Path) -> List[Path]:
        """Resolve Python import to file paths"""
        resolved = []
        
        # Handle relative imports
        if import_stmt.startswith('.'):
            base_dir = source_file.parent
            # Remove leading dots and convert to path
            relative_path = import_stmt.lstrip('.')
            if relative_path:
                target_path = base_dir / f"{relative_path.replace('.', '/')}.py"
                if target_path.exists():
                    resolved.append(target_path)
                # Also check for __init__.py
                init_path = base_dir / relative_path.replace('.', '/') / "__init__.py"
                if init_path.exists():
                    resolved.append(init_path)
        else:
            # Absolute import - look in project root
            module_path = self.project_root / f"{import_stmt.replace('.', '/')}.py"
            if module_path.exists():
                resolved.append(module_path)
            # Also check for package __init__.py
            init_path = self.project_root / import_stmt.replace('.', '/') / "__init__.py"
            if init_path.exists():
                resolved.append(init_path)
        
        return resolved

    def _resolve_js_import(self, import_stmt: str, source_file: Path) -> List[Path]:
        """Resolve JavaScript/TypeScript import to file paths"""
        resolved = []
        
        # Skip node_modules and absolute imports
        if not import_stmt.startswith('.'):
            return resolved
        
        # Resolve relative import
        base_dir = source_file.parent
        target_path = (base_dir / import_stmt).resolve()
        
        # Try different extensions
        extensions = ['.ts', '.tsx', '.js', '.jsx', '.json']
        
        # Check exact path first
        if target_path.exists():
            resolved.append(target_path)
        else:
            # Try with extensions
            for ext in extensions:
                ext_path = target_path.with_suffix(ext)
                if ext_path.exists():
                    resolved.append(ext_path)
                    break
            
            # Try index files
            if not resolved:
                for ext in extensions:
                    index_path = target_path / f"index{ext}"
                    if index_path.exists():
                        resolved.append(index_path)
                        break
        
        return resolved

    def _classify_dependency_type(self, import_stmt: str, source_info: FileInfo, target_file: Path) -> str:
        """Classify the type of dependency"""
        if import_stmt.startswith('.'):
            return 'relative_import'
        elif source_info.file_type == FileType.BACKEND_PYTHON and not import_stmt.startswith('.'):
            return 'module_import'
        else:
            return 'import'

    def analyze_dependency_clusters(self) -> List[DependencyCluster]:
        """Analyze the dependency graph to identify clusters of related files"""
        self.clusters.clear()
        
        # Find strongly connected components
        strongly_connected = list(nx.strongly_connected_components(self.dependency_graph))
        
        # Find weakly connected components for broader clustering
        weakly_connected = list(nx.weakly_connected_components(self.dependency_graph))
        
        # Create clusters based on file types and dependencies
        frontend_files = set()
        backend_files = set()
        shared_files = set()
        
        for file_path, file_info in self.file_infos.items():
            if file_info.file_type in [FileType.FRONTEND_REACT, FileType.FRONTEND_TYPESCRIPT, 
                                     FileType.FRONTEND_JAVASCRIPT, FileType.FRONTEND_CSS, 
                                     FileType.FRONTEND_HTML, FileType.CONFIG_FRONTEND]:
                frontend_files.add(file_path)
            elif file_info.file_type in [FileType.BACKEND_PYTHON, FileType.CONFIG_BACKEND]:
                backend_files.add(file_path)
            else:
                shared_files.add(file_path)
        
        # Create clusters
        if frontend_files:
            self.clusters.append(self._create_cluster(frontend_files, 'frontend'))
        if backend_files:
            self.clusters.append(self._create_cluster(backend_files, 'backend'))
        if shared_files:
            self.clusters.append(self._create_cluster(shared_files, 'shared'))
        
        return self.clusters

    def _create_cluster(self, files: Set[Path], cluster_type: str) -> DependencyCluster:
        """Create a dependency cluster from a set of files"""
        internal_deps = []
        external_deps = []
        
        for edge in self.dependency_edges:
            if edge.source in files and edge.target in files:
                internal_deps.append(edge)
            elif edge.source in files and edge.target not in files:
                external_deps.append(edge)
        
        return DependencyCluster(
            files=files,
            cluster_type=cluster_type,
            internal_dependencies=internal_deps,
            external_dependencies=external_deps
        )

    def find_circular_dependencies(self) -> List[List[Path]]:
        """Find circular dependencies in the graph"""
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            return cycles
        except nx.NetworkXError:
            return []

    def get_dependency_order(self) -> List[Path]:
        """Get topological order of files based on dependencies"""
        try:
            return list(nx.topological_sort(self.dependency_graph))
        except nx.NetworkXError:
            # Graph has cycles, return best effort ordering
            return list(self.dependency_graph.nodes())

    def validate_reorganization_safety(self, path_mappings: Dict[Path, Path]) -> Dict[str, List[str]]:
        """Validate that a proposed reorganization won't break dependencies"""
        issues = {
            'broken_dependencies': [],
            'circular_dependencies': [],
            'cross_boundary_dependencies': [],
            'warnings': []
        }
        
        # Check for broken dependencies
        for edge in self.dependency_edges:
            source_new = path_mappings.get(edge.source, edge.source)
            target_new = path_mappings.get(edge.target, edge.target)
            
            # Check if the dependency can still be resolved
            if not self._can_resolve_dependency(source_new, target_new, edge.dependency_type):
                issues['broken_dependencies'].append(
                    f"{edge.source} -> {edge.target} (import: {edge.import_statement})"
                )
        
        # Check for circular dependencies
        cycles = self.find_circular_dependencies()
        for cycle in cycles:
            cycle_str = " -> ".join(str(p) for p in cycle)
            issues['circular_dependencies'].append(cycle_str)
        
        # Check for cross-boundary dependencies
        for edge in self.dependency_edges:
            source_info = self.file_infos[edge.source]
            target_info = self.file_infos[edge.target]
            
            if self._is_cross_boundary_dependency(source_info, target_info):
                issues['cross_boundary_dependencies'].append(
                    f"{edge.source} ({source_info.file_type}) -> {edge.target} ({target_info.file_type})"
                )
        
        return issues

    def _can_resolve_dependency(self, source_path: Path, target_path: Path, dep_type: str) -> bool:
        """Check if a dependency can still be resolved after reorganization"""
        # This is a simplified check - in practice, you'd want more sophisticated logic
        if dep_type == 'relative_import':
            # Check if files are still in reasonable relative positions
            try:
                target_path.relative_to(source_path.parent)
                return True
            except ValueError:
                # Check if they're in the same directory tree
                common_parts = len(Path(*source_path.parts).parts & Path(*target_path.parts).parts)
                return common_parts > 1  # At least project root in common
        
        return True  # Assume other imports can be resolved

    def _is_cross_boundary_dependency(self, source_info: FileInfo, target_info: FileInfo) -> bool:
        """Check if this is a cross-boundary dependency that might cause issues"""
        frontend_types = {FileType.FRONTEND_REACT, FileType.FRONTEND_TYPESCRIPT, 
                         FileType.FRONTEND_JAVASCRIPT, FileType.FRONTEND_CSS, FileType.FRONTEND_HTML}
        backend_types = {FileType.BACKEND_PYTHON}
        
        source_is_frontend = source_info.file_type in frontend_types
        target_is_frontend = target_info.file_type in frontend_types
        source_is_backend = source_info.file_type in backend_types
        target_is_backend = target_info.file_type in backend_types
        
        # Cross-boundary if frontend imports backend or vice versa
        return (source_is_frontend and target_is_backend) or (source_is_backend and target_is_frontend)

    def get_dependency_statistics(self) -> Dict[str, any]:
        """Get statistics about the dependency graph"""
        stats = {
            'total_files': len(self.file_infos),
            'total_dependencies': len(self.dependency_edges),
            'circular_dependencies': len(self.find_circular_dependencies()),
            'strongly_connected_components': len(list(nx.strongly_connected_components(self.dependency_graph))),
            'weakly_connected_components': len(list(nx.weakly_connected_components(self.dependency_graph))),
            'file_type_distribution': defaultdict(int),
            'dependency_type_distribution': defaultdict(int),
            'average_dependencies_per_file': 0,
            'max_dependencies': 0,
            'isolated_files': 0
        }
        
        # File type distribution
        for file_info in self.file_infos.values():
            stats['file_type_distribution'][file_info.file_type.value] += 1
        
        # Dependency type distribution
        for edge in self.dependency_edges:
            stats['dependency_type_distribution'][edge.dependency_type] += 1
        
        # Dependency statistics
        if self.file_infos:
            stats['average_dependencies_per_file'] = len(self.dependency_edges) / len(self.file_infos)
        
        # Find max dependencies and isolated files
        dependency_counts = defaultdict(int)
        for edge in self.dependency_edges:
            dependency_counts[edge.source] += 1
        
        if dependency_counts:
            stats['max_dependencies'] = max(dependency_counts.values())
        
        stats['isolated_files'] = len([f for f in self.file_infos.keys() if f not in dependency_counts])
        
        return dict(stats)