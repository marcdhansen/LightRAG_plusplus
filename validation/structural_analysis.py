"""
Structural Analysis Module for Graph Validation

Provides advanced graph structure analysis including connectivity,
path analysis, and structural integrity checks.
"""

import statistics
from dataclasses import dataclass
from typing import Any

import networkx as nx

from lightrag.utils import logger


@dataclass
class StructuralMetrics:
    """Comprehensive graph structural metrics"""

    # Basic metrics
    node_count: int
    edge_count: int
    density: float

    # Connectivity metrics
    is_connected: bool
    connected_components: int
    largest_component_size: int

    # Path metrics
    diameter: int | None
    average_path_length: float | None
    max_path_length: int | None

    # Centrality metrics
    average_degree: float
    max_degree: int
    min_degree: int

    # Clustering metrics
    clustering_coefficient: float
    transitivity: float

    # Structural issues
    isolated_nodes: list[str]
    weakly_connected_components: int
    bridges: list[tuple[str, str]]
    articulation_points: list[str]


class StructuralAnalyzer:
    """
    Advanced structural analysis for knowledge graphs

    Provides comprehensive analysis of graph structure, connectivity,
    and structural integrity for validation purposes.
    """

    def __init__(self):
        """Initialize the structural analyzer"""
        self.metrics_cache = {}

    def create_graph(
        self, entities: list[dict[str, Any]], relationships: list[dict[str, Any]]
    ) -> nx.DiGraph:
        """
        Create NetworkX graph from entities and relationships

        Args:
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries

        Returns:
            NetworkX directed graph
        """
        G = nx.DiGraph()

        # Add nodes with attributes
        for entity in entities:
            entity_id = entity.get("id", entity.get("entity_name", ""))
            if entity_id:
                G.add_node(entity_id, **entity)

        # Add edges with attributes
        for rel in relationships:
            src_id = rel.get("src_id", "")
            tgt_id = rel.get("tgt_id", "")
            if src_id and tgt_id and G.has_node(src_id) and G.has_node(tgt_id):
                G.add_edge(src_id, tgt_id, **rel)

        return G

    def calculate_basic_metrics(self, G: nx.Graph) -> dict[str, Any]:
        """Calculate basic graph metrics"""
        return {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": nx.density(G),
            "average_degree": statistics.mean([d for _, d in G.degree()])
            if G.number_of_nodes() > 0
            else 0,
            "max_degree": max([d for _, d in G.degree()], default=0),
            "min_degree": min([d for _, d in G.degree()], default=0),
        }

    def calculate_connectivity_metrics(self, G: nx.DiGraph) -> dict[str, Any]:
        """Calculate connectivity metrics"""
        # Convert to undirected for connectivity analysis
        U = G.to_undirected()

        if G.number_of_nodes() == 0:
            return {
                "is_connected": False,
                "connected_components": 0,
                "largest_component_size": 0,
                "weakly_connected_components": 0,
                "strongly_connected_components": 0,
            }

        # Undirected connectivity
        is_connected = nx.is_connected(U)
        connected_components = nx.number_connected_components(U)

        # Find largest component
        components = list(nx.connected_components(U))
        largest_component_size = max(len(c) for c in components) if components else 0

        # Directed connectivity
        weakly_connected = nx.number_weakly_connected_components(G)
        strongly_connected = nx.number_strongly_connected_components(G)

        return {
            "is_connected": is_connected,
            "connected_components": connected_components,
            "largest_component_size": largest_component_size,
            "weakly_connected_components": weakly_connected,
            "strongly_connected_components": strongly_connected,
        }

    def calculate_path_metrics(self, G: nx.DiGraph) -> dict[str, Any]:
        """Calculate path-related metrics"""
        if G.number_of_nodes() == 0:
            return {
                "diameter": None,
                "average_path_length": None,
                "max_path_length": None,
                "shortest_paths": {},
            }

        # Use undirected graph for path calculations
        U = G.to_undirected()

        # Only calculate if the graph is connected
        if not nx.is_connected(U):
            # Calculate for largest component
            components = list(nx.connected_components(U))
            largest_component = max(components, key=len)
            U = U.subgraph(largest_component).copy()

        if U.number_of_nodes() <= 1:
            return {
                "diameter": 0,
                "average_path_length": 0,
                "max_path_length": 0,
                "shortest_paths": {},
            }

        try:
            # Calculate diameter
            diameter = nx.diameter(U)

            # Calculate average path length
            avg_path_length = nx.average_shortest_path_length(U)

            # Calculate all shortest paths (sample for performance)
            sample_nodes = list(U.nodes())[: min(10, len(U.nodes()))]
            shortest_paths = {}
            for source in sample_nodes:
                for target in sample_nodes:
                    if source != target:
                        try:
                            path = nx.shortest_path(U, source, target)
                            shortest_paths[f"{source}->{target}"] = path
                        except nx.NetworkXNoPath:
                            continue

            max_path_length = diameter

            return {
                "diameter": diameter,
                "average_path_length": avg_path_length,
                "max_path_length": max_path_length,
                "shortest_paths": shortest_paths,
            }

        except Exception:
            # Fallback for cases where path calculation fails
            return {
                "diameter": None,
                "average_path_length": None,
                "max_path_length": None,
                "shortest_paths": {},
            }

    def calculate_centrality_metrics(self, G: nx.DiGraph) -> dict[str, Any]:
        """Calculate centrality metrics"""
        if G.number_of_nodes() == 0:
            return {
                "degree_centrality": {},
                "betweenness_centrality": {},
                "closeness_centrality": {},
                "eigenvector_centrality": {},
                "pagerank": {},
            }

        try:
            # Calculate various centrality measures
            degree_cent = nx.degree_centrality(G)
            betweenness_cent = nx.betweenness_centrality(G)
            closeness_cent = nx.closeness_centrality(G)

            # Eigenvector centrality (may not converge)
            try:
                eigen_cent = nx.eigenvector_centrality(G, max_iter=1000)
            except Exception as e:
                logger.warning(f"Eigenvector centrality calculation failed: {e}")
                eigen_cent = {}

            # PageRank
            try:
                pagerank = nx.pagerank(G)
            except Exception as e:
                logger.warning(f"PageRank calculation failed: {e}")
                pagerank = {}

            return {
                "degree_centrality": degree_cent,
                "betweenness_centrality": betweenness_cent,
                "closeness_centrality": closeness_cent,
                "eigenvector_centrality": eigen_cent,
                "pagerank": pagerank,
            }

        except Exception:
            return {
                "degree_centrality": {},
                "betweenness_centrality": {},
                "closeness_centrality": {},
                "eigenvector_centrality": {},
                "pagerank": {},
            }

    def calculate_clustering_metrics(self, G: nx.DiGraph) -> dict[str, Any]:
        """Calculate clustering metrics"""
        if G.number_of_nodes() == 0:
            return {
                "clustering_coefficient": 0,
                "transitivity": 0,
                "average_clustering": 0,
            }

        # Use undirected graph for clustering
        U = G.to_undirected()

        try:
            clustering_coeff = nx.average_clustering(U)
            transitivity = nx.transitivity(U)

            return {
                "clustering_coefficient": clustering_coeff,
                "transitivity": transitivity,
                "average_clustering": clustering_coeff,
            }

        except Exception:
            return {
                "clustering_coefficient": 0,
                "transitivity": 0,
                "average_clustering": 0,
            }

    def identify_structural_issues(self, G: nx.DiGraph) -> dict[str, Any]:
        """Identify structural issues and vulnerabilities"""
        issues = {
            "isolated_nodes": [],
            "bridges": [],
            "articulation_points": [],
            "cycles": [],
            "self_loops": [],
        }

        if G.number_of_nodes() == 0:
            return issues

        # Use undirected graph for most structural analysis
        U = G.to_undirected()

        # Isolated nodes
        isolated = list(nx.isolates(U))
        issues["isolated_nodes"] = isolated

        # Bridges (edges whose removal disconnects the graph)
        try:
            bridges = list(nx.bridges(U))
            issues["bridges"] = bridges
        except Exception as e:
            logger.warning(f"Bridge analysis failed: {e}")
            issues["bridges"] = []

        # Articulation points (nodes whose removal disconnects the graph)
        try:
            articulation_points = list(nx.articulation_points(U))
            issues["articulation_points"] = articulation_points
        except Exception as e:
            logger.warning(f"Articulation points analysis failed: {e}")
            issues["articulation_points"] = []

        # Cycles in directed graph
        try:
            cycles = list(nx.simple_cycles(G))
            issues["cycles"] = cycles[:10]  # Limit to first 10 cycles
        except Exception as e:
            logger.warning(f"Cycle analysis failed: {e}")
            issues["cycles"] = []

        # Self-loops
        self_loops = list(nx.selfloop_edges(G))
        issues["self_loops"] = self_loops

        return issues

    def analyze_comprehensive(
        self, entities: list[dict[str, Any]], relationships: list[dict[str, Any]]
    ) -> StructuralMetrics:
        """
        Perform comprehensive structural analysis

        Args:
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries

        Returns:
            Comprehensive structural metrics
        """
        # Create graph
        G = self.create_graph(entities, relationships)

        # Calculate all metrics
        basic_metrics = self.calculate_basic_metrics(G)
        connectivity_metrics = self.calculate_connectivity_metrics(G)
        path_metrics = self.calculate_path_metrics(G)
        clustering_metrics = self.calculate_clustering_metrics(G)

        # Identify structural issues
        issues = self.identify_structural_issues(G)

        return StructuralMetrics(
            # Basic metrics
            node_count=basic_metrics["node_count"],
            edge_count=basic_metrics["edge_count"],
            density=basic_metrics["density"],
            # Connectivity metrics
            is_connected=connectivity_metrics["is_connected"],
            connected_components=connectivity_metrics["connected_components"],
            largest_component_size=connectivity_metrics["largest_component_size"],
            # Path metrics
            diameter=path_metrics["diameter"],
            average_path_length=path_metrics["average_path_length"],
            max_path_length=path_metrics["max_path_length"],
            # Centrality metrics
            average_degree=basic_metrics["average_degree"],
            max_degree=basic_metrics["max_degree"],
            min_degree=basic_metrics["min_degree"],
            # Clustering metrics
            clustering_coefficient=clustering_metrics["clustering_coefficient"],
            transitivity=clustering_metrics["transitivity"],
            # Structural issues
            isolated_nodes=issues["isolated_nodes"],
            weakly_connected_components=connectivity_metrics[
                "weakly_connected_components"
            ],
            bridges=issues["bridges"],
            articulation_points=issues["articulation_points"],
        )

    def validate_structure_requirements(
        self, metrics: StructuralMetrics, requirements: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Validate structure against specific requirements

        Args:
            metrics: Structural metrics to validate
            requirements: Requirements dictionary

        Returns:
            Tuple of (passed, issues_list)
        """
        issues = []
        passed = True

        # Check minimum node count
        min_nodes = requirements.get("min_entities", 0)
        if metrics.node_count < min_nodes:
            issues.append(f"Insufficient entities: {metrics.node_count} < {min_nodes}")
            passed = False

        # Check minimum edge count
        min_edges = requirements.get("min_relationships", 0)
        if metrics.edge_count < min_edges:
            issues.append(
                f"Insufficient relationships: {metrics.edge_count} < {min_edges}"
            )
            passed = False

        # Check connectivity requirement
        if requirements.get("graph_connectivity", False):
            if not metrics.is_connected:
                issues.append(
                    f"Graph not connected: {metrics.connected_components} components"
                )
                passed = False

        # Check maximum path length
        max_path = requirements.get("max_path_length")
        if max_path is not None and metrics.max_path_length is not None:
            if metrics.max_path_length > max_path:
                issues.append(f"Path too long: {metrics.max_path_length} > {max_path}")
                passed = False

        # Check density requirements
        min_density = requirements.get("min_density")
        if min_density is not None:
            if metrics.density < min_density:
                issues.append(f"Density too low: {metrics.density:.3f} < {min_density}")
                passed = False

        # Check for isolated nodes
        if not requirements.get("allow_isolated_nodes", True):
            if metrics.isolated_nodes:
                issues.append(f"Isolated nodes found: {len(metrics.isolated_nodes)}")
                passed = False

        return passed, issues

    def compare_structures(
        self,
        baseline_metrics: StructuralMetrics,
        current_metrics: StructuralMetrics,
        tolerance: float = 0.1,
    ) -> dict[str, Any]:
        """
        Compare two graph structures and identify changes

        Args:
            baseline_metrics: Baseline structural metrics
            current_metrics: Current structural metrics
            tolerance: Relative change tolerance

        Returns:
            Comparison results
        """
        changes = {
            "node_changes": current_metrics.node_count - baseline_metrics.node_count,
            "edge_changes": current_metrics.edge_count - baseline_metrics.edge_count,
            "density_change": current_metrics.density - baseline_metrics.density,
            "connectivity_changed": baseline_metrics.is_connected
            != current_metrics.is_connected,
            "component_changes": current_metrics.connected_components
            - baseline_metrics.connected_components,
            "isolated_nodes_added": len(
                set(current_metrics.isolated_nodes)
                - set(baseline_metrics.isolated_nodes)
            ),
            "isolated_nodes_removed": len(
                set(baseline_metrics.isolated_nodes)
                - set(current_metrics.isolated_nodes)
            ),
        }

        # Calculate significant changes (beyond tolerance)
        significant_changes = {}

        # Node count change
        node_rel_change = abs(changes["node_changes"]) / max(
            baseline_metrics.node_count, 1
        )
        if node_rel_change > tolerance:
            significant_changes["nodes"] = (
                f"Node count changed by {changes['node_changes']} ({node_rel_change:.1%})"
            )

        # Edge count change
        edge_rel_change = abs(changes["edge_changes"]) / max(
            baseline_metrics.edge_count, 1
        )
        if edge_rel_change > tolerance:
            significant_changes["edges"] = (
                f"Edge count changed by {changes['edge_changes']} ({edge_rel_change:.1%})"
            )

        # Density change
        if abs(changes["density_change"]) > tolerance:
            significant_changes["density"] = (
                f"Density changed by {changes['density_change']:.3f}"
            )

        # Connectivity change
        if changes["connectivity_changed"]:
            significant_changes["connectivity"] = (
                f"Connectivity changed from {baseline_metrics.is_connected} to {current_metrics.is_connected}"
            )

        return {
            "changes": changes,
            "significant_changes": significant_changes,
            "stability_score": 1.0 - len(significant_changes) * 0.1,  # Simple scoring
        }
