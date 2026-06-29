"""
Generate MapNode data and precompute shortest-path distances.

What it does:
1) Creates N random map nodes (default: 3000).
2) Connects each node to its K nearest neighbors (sparse undirected graph).
3) Runs Dijkstra from every node to compute shortest distances.
4) Inserts pairwise shortest distances into PrecalculatedPath.

Notes:
- To reduce storage, this script stores only node_a_id < node_b_id pairs.
- Distances are computed in a 2D coordinate plane (Euclidean edge weights).
- requires_sea_transport is True if any edge in the chosen shortest path
  touches a sea-zone node.

Usage example:
    python generate_nodes_and_paths.py --nodes 3000 --k 8 --seed 42
"""

import argparse
import heapq
import math
import os
import random
import time
from dataclasses import dataclass
from typing import List, Tuple

import psycopg2
from psycopg2.extras import execute_values


@dataclass
class Node:
    node_id: int
    name: str
    terrain: str
    is_sea_zone: bool
    x: float
    y: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate map nodes and precomputed shortest paths.")
    parser.add_argument("--host", default=os.getenv("DB_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "5432")))
    parser.add_argument("--database", default=os.getenv("DB_NAME", "world_economy"))
    parser.add_argument("--user", default=os.getenv("DB_USER", "postgres"))
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD", "password"))
    parser.add_argument("--nodes", type=int, default=3000, help="Number of nodes to generate.")
    parser.add_argument("--k", type=int, default=8, help="Nearest neighbors per node.")
    parser.add_argument("--sea-prob", type=float, default=0.18, help="Probability that a node is sea zone.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation.")
    parser.add_argument(
        "--delete-existing-paths",
        action="store_true",
        help="Delete all rows from PrecalculatedPath before inserting new rows.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10000,
        help="Batch size for bulk inserts into PrecalculatedPath.",
    )
    return parser.parse_args()


def build_nodes(start_id: int, n: int, sea_prob: float) -> List[Node]:
    terrains_land = ["Plains", "Forest", "Hills", "Mountain", "Desert", "Urban"]
    terrains_sea = ["Sea"]
    nodes: List[Node] = []
    for i in range(n):
        node_id = start_id + i
        is_sea = random.random() < sea_prob
        terrain = random.choice(terrains_sea if is_sea else terrains_land)
        nodes.append(
            Node(
                node_id=node_id,
                name=f"Node-{node_id}",
                terrain=terrain,
                is_sea_zone=is_sea,
                x=random.random() * 10000.0,
                y=random.random() * 10000.0,
            )
        )
    return nodes


def euclidean(a: Node, b: Node) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def build_knn_graph(nodes: List[Node], k: int) -> List[List[Tuple[int, float, bool]]]:
    """
    Build sparse undirected graph by connecting each node to k nearest neighbors.
    Returns adjacency list by local index:
      adj[u] -> list of (v, weight, edge_requires_sea_transport)
    """
    n = len(nodes)
    adj: List[List[Tuple[int, float, bool]]] = [[] for _ in range(n)]
    for i in range(n):
        distances: List[Tuple[float, int]] = []
        ni = nodes[i]
        for j in range(n):
            if i == j:
                continue
            distances.append((euclidean(ni, nodes[j]), j))
        distances.sort(key=lambda x: x[0])
        for dist, j in distances[:k]:
            sea_edge = nodes[i].is_sea_zone or nodes[j].is_sea_zone
            adj[i].append((j, dist, sea_edge))
            adj[j].append((i, dist, sea_edge))
    return adj


def all_pairs_dijkstra(nodes: List[Node], adj: List[List[Tuple[int, float, bool]]], batch_size: int):
    """
    Yield batched rows for PrecalculatedPath:
      (node_a_id, node_b_id, total_distance, requires_sea_transport)
    Only yields rows where node_a_id < node_b_id.
    """
    n = len(nodes)
    row_batch: List[Tuple[int, int, float, bool]] = []
    inf = float("inf")

    for source in range(n):
        dist = [inf] * n
        sea_used = [True] * n
        dist[source] = 0.0
        sea_used[source] = False

        heap: List[Tuple[float, int, bool]] = [(0.0, source, False)]
        while heap:
            d, u, used_sea = heapq.heappop(heap)
            if d > dist[u]:
                continue
            if d == dist[u] and used_sea and not sea_used[u]:
                continue
            for v, w, edge_sea in adj[u]:
                nd = d + w
                nsea = used_sea or edge_sea
                better = nd < dist[v] or (math.isclose(nd, dist[v]) and (not nsea) and sea_used[v])
                if better:
                    dist[v] = nd
                    sea_used[v] = nsea
                    heapq.heappush(heap, (nd, v, nsea))

        src_id = nodes[source].node_id
        for target in range(source + 1, n):
            if dist[target] == inf:
                continue
            row_batch.append(
                (
                    src_id,
                    nodes[target].node_id,
                    round(dist[target], 2),
                    sea_used[target],
                )
            )
            if len(row_batch) >= batch_size:
                yield row_batch
                row_batch = []

        if (source + 1) % 100 == 0:
            print(f"Computed shortest paths from {source + 1}/{n} nodes...")

    if row_batch:
        yield row_batch


def main() -> None:
    args = parse_args()
    random.seed(args.seed)

    if args.k < 1:
        raise ValueError("--k must be >= 1")
    if args.nodes < 2:
        raise ValueError("--nodes must be >= 2")

    t0 = time.time()
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
    )
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            # Start node IDs after current max so we do not break existing references.
            cur.execute("SELECT COALESCE(MAX(node_id), 0) FROM MapNode;")
            max_node_id = int(cur.fetchone()[0])
            start_id = max_node_id + 1

            nodes = build_nodes(start_id=start_id, n=args.nodes, sea_prob=args.sea_prob)
            print(f"Generated {len(nodes)} nodes with IDs {start_id}..{start_id + len(nodes) - 1}")

            execute_values(
                cur,
                """
                INSERT INTO MapNode (node_id, node_name, terrain_type, is_sea_zone)
                VALUES %s
                """,
                [(n.node_id, n.name, n.terrain, n.is_sea_zone) for n in nodes],
                page_size=5000,
            )
            print("Inserted MapNode rows.")

            if args.delete_existing_paths:
                cur.execute("DELETE FROM PrecalculatedPath;")
                print("Deleted existing PrecalculatedPath rows.")

            print("Building k-nearest-neighbor graph...")
            adj = build_knn_graph(nodes, args.k)
            edge_count = sum(len(lst) for lst in adj) // 2
            print(f"Graph built with ~{edge_count} undirected edges.")

            print("Running all-pairs Dijkstra and inserting PrecalculatedPath in batches...")
            inserted = 0
            for batch in all_pairs_dijkstra(nodes, adj, args.batch_size):
                execute_values(
                    cur,
                    """
                    INSERT INTO PrecalculatedPath (node_a_id, node_b_id, total_distance, requires_sea_transport)
                    VALUES %s
                    ON CONFLICT (node_a_id, node_b_id) DO UPDATE
                    SET total_distance = EXCLUDED.total_distance,
                        requires_sea_transport = EXCLUDED.requires_sea_transport
                    """,
                    batch,
                    page_size=args.batch_size,
                )
                inserted += len(batch)
                if inserted % 500000 < len(batch):
                    print(f"Inserted {inserted} precomputed path rows so far...")

        conn.commit()
        elapsed = time.time() - t0
        print(f"Done. Inserted {inserted} PrecalculatedPath rows in {elapsed:.1f}s.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()

#python generate_nodes_and_paths.py --nodes 3000 --k 8 --seed 42 --delete-existing-paths --batch-size 10000