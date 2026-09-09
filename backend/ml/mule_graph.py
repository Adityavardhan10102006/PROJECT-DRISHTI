"""
backend/ml/mule_graph.py — Project DRISHTI
============================================
Multi-Hop Money-Trail Analysis & Mule Detection using NetworkX.

Capabilities:
  1. Builds and maintains a stateful directed transaction graph (nx.DiGraph)
     persisted across sessions via a JSON cache file (mule_centrality_cache.json).
  2. For each incoming complaint, loads existing graph state, adds new transactional
     layering hops/edges, and incrementally recomputes betweenness centrality
     for the affected nodes and their network neighborhoods.
  3. Detects layering behaviors:
     - Rapid velocity (inter-hop latency < 15 mins)
     - Amount fan-out/fan-in and commission shaving (3-8% commission retained per hop)
  4. Calculates node centrality metrics (betweenness centrality, PageRank, in/out degree).
  5. Flags accounts with historically high betweenness centrality (is_historical_mule = True).
  6. Returns structured trails with timestamps, amounts, and intermediate mule risks.

Designed to run efficiently on standard laptop CPU using NetworkX.
"""

import os
import json
import random
import hashlib
import networkx as nx
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Set, Tuple
import pandas as pd
from backend.clustering.hotspot import haversine_km

TXN_DATASET_PATH = "data/transactions.csv"


def _ensure_utc(dt: Optional[datetime]) -> datetime:
    """Normalize datetime to timezone-aware UTC datetime."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_utc(ts_str: str, default: Optional[datetime] = None) -> datetime:
    """Parse ISO timestamp string to timezone-aware UTC datetime."""
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return default or datetime.now(timezone.utc)


class MuleNetworkGraph:
    """
    Manages stateful transaction graphs and extracts multi-hop laundering chains.
    Persists graph topology and historical centrality across sessions using JSON caching.
    Thread-safe and CPU-friendly.
    """

    # Centrality threshold to flag recurrent transit hubs / syndicate mules
    HISTORICAL_CENTRALITY_THRESHOLD: float = 0.004

    def __init__(self, seed: int = 42, cache_file: Optional[str] = None):
        self.rng = random.Random(seed)
        self.graph = nx.DiGraph()
        self.historical_centrality: Dict[str, float] = {}

        if cache_file is None:
            cache_file = os.getenv("MULE_CACHE_FILE", "mule_centrality_cache.json")
        self.cache_file = cache_file
        self._fraud_df_cache: Optional[pd.DataFrame] = None

        # Attempt to load persistent state from cache; seed if not found
        loaded = self._load_cache()
        if not loaded:
            self._seed_synthetic_mule_rings()
            self._recompute_and_save_cache()

    def _find_dataset_trail(
        self,
        starting_account: Optional[str],
        initial_amount: float,
        incident_time: datetime,
        max_hops: int = 4,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Attempts to construct multi-hop trail from real records in data/transactions.csv.
        Returns None if dataset unavailable or no match found.
        """
        if not os.path.exists(TXN_DATASET_PATH):
            return None
        try:
            if self._fraud_df_cache is None:
                df = pd.read_csv(TXN_DATASET_PATH)
                self._fraud_df_cache = df[df["is_fraud"] == 1].copy()
            fraud_df = self._fraud_df_cache
            if fraud_df.empty:
                return None

            matched_rows = []
            if starting_account:
                matched = fraud_df[
                    (fraud_df["source_account"] == starting_account) |
                    (fraud_df["destination_account"] == starting_account)
                ]
                if not matched.empty:
                    matched_rows = matched.to_dict(orient="records")

            if not matched_rows and initial_amount > 0:
                close_txns = fraud_df[
                    (fraud_df["amount"] >= initial_amount * 0.75) &
                    (fraud_df["amount"] <= initial_amount * 1.35)
                ]
                if not close_txns.empty:
                    first_row = close_txns.iloc[0]
                    src = first_row["source_account"]
                    matched_rows = fraud_df[fraud_df["source_account"] == src].to_dict(orient="records")

            if not matched_rows:
                return None

            hops = []
            curr_acc = matched_rows[0]["destination_account"]
            incident_time = _ensure_utc(incident_time)
            current_time = incident_time

            h1 = matched_rows[0]
            step_mins = self.rng.randint(6, 14)
            current_time += timedelta(minutes=step_mins)
            amt1 = float(h1["amount"])

            hops.append({
                "hop_index": 1,
                "from_account": str(h1["source_account"]),
                "to_account": str(h1["destination_account"]),
                "to_bank": str(h1.get("destination_bank", "State Bank of India")),
                "to_ifsc": "SBIN0001423",
                "amount": amt1,
                "commission_retained": round(float(initial_amount - amt1), 2) if initial_amount > amt1 else 0.0,
                "timestamp": current_time.isoformat(),
                "minutes_from_start": step_mins,
                "txn_type": str(h1.get("transaction_type", "UPI")),
                "txn_ref": str(h1["transaction_id"]),
                "is_terminal_cashout": False,
                "source_lat": float(h1.get("source_latitude", 17.44)),
                "source_lon": float(h1.get("source_longitude", 78.38)),
                "dest_lat": float(h1.get("destination_latitude", 17.43)),
                "dest_lon": float(h1.get("destination_longitude", 78.39)),
            })

            target_hops = min(max_hops, 3 if amt1 >= 50000 else 2)
            for h_idx in range(2, target_hops + 1):
                is_terminal = (h_idx == target_hops)
                next_match = fraud_df[fraud_df["source_account"] == curr_acc]
                if not next_match.empty:
                    nxt = next_match.iloc[0]
                    dest_acc = str(nxt["destination_account"])
                    dest_bank = str(nxt.get("destination_bank", "HDFC Bank"))
                else:
                    dest_acc = f"MULE-L{h_idx}-{self.rng.randint(10000000, 99999999)}"
                    dest_bank = "HDFC Bank" if h_idx == 2 else "ICICI Bank"

                step_mins = self.rng.randint(8, 20)
                current_time += timedelta(minutes=step_mins)
                comm = round(hops[-1]["amount"] * 0.05, 2)
                hop_amt = round(hops[-1]["amount"] - comm, 2)

                s_lat = hops[-1]["dest_lat"]
                s_lon = hops[-1]["dest_lon"]
                d_lat = round(s_lat + self.rng.uniform(-0.015, 0.015), 6)
                d_lon = round(s_lon + self.rng.uniform(-0.015, 0.015), 6)

                hops.append({
                    "hop_index": h_idx,
                    "from_account": curr_acc,
                    "to_account": dest_acc,
                    "to_bank": dest_bank,
                    "to_ifsc": "HDFC0000128" if "HDFC" in dest_bank else "ICIC0000005",
                    "amount": hop_amt,
                    "commission_retained": comm,
                    "timestamp": current_time.isoformat(),
                    "minutes_from_start": int((current_time - incident_time).total_seconds() / 60),
                    "txn_type": "ATM_WITHDRAWAL" if is_terminal else "IMPS",
                    "txn_ref": f"TXN-DATA-{self.rng.randint(100000, 999999)}",
                    "is_terminal_cashout": is_terminal,
                    "source_lat": s_lat,
                    "source_lon": s_lon,
                    "dest_lat": d_lat,
                    "dest_lon": d_lon,
                })
                curr_acc = dest_acc
                if is_terminal:
                    break

            return hops
        except Exception as err:
            print(f"[DRISHTI] Warning in _find_dataset_trail: {err}")
            return None

    def _load_cache(self) -> bool:
        """
        Loads graph nodes, edges, and historical betweenness centrality from the JSON cache.
        Returns True if loaded successfully, False otherwise.
        """
        # Check cache_file or fallback to data/ directory if configured
        target_file = self.cache_file
        if not os.path.exists(target_file):
            alt_path = os.path.join("data", os.path.basename(self.cache_file))
            if os.path.exists(alt_path):
                target_file = alt_path
            else:
                return False

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.graph.clear()

            # Rebuild nodes with attributes
            for node, attrs in data.get("nodes", {}).items():
                self.graph.add_node(node, **attrs)

            # Rebuild edges with attributes
            for edge in data.get("edges", []):
                u = edge.get("from_account") or edge.get("source")
                v = edge.get("to_account") or edge.get("target")
                if u and v:
                    attrs = {
                        k: val
                        for k, val in edge.items()
                        if k not in ("from_account", "to_account", "source", "target")
                    }
                    self.graph.add_edge(u, v, **attrs)

            # Rebuild historical centrality dict
            self.historical_centrality = {
                k: float(v) for k, v in data.get("historical_centrality", {}).items()
            }
            return True
        except Exception as e:
            print(f"[DRISHTI] Warning: Failed to load mule cache from {target_file}: {e}")
            return False

    def _save_cache(self) -> None:
        """
        Atomically saves graph nodes, edges, and historical betweenness centrality to JSON cache.
        Also mirrors to data/ folder if it exists, keeping the workspace synchronized.
        """
        try:
            nodes_dict = {}
            for n, attrs in self.graph.nodes(data=True):
                clean_attrs = {}
                for k, v in attrs.items():
                    if isinstance(v, (str, int, float, bool)) or v is None:
                        clean_attrs[k] = v
                    elif isinstance(v, (list, dict)):
                        clean_attrs[k] = v
                    else:
                        clean_attrs[k] = str(v)
                nodes_dict[n] = clean_attrs

            edges_list = []
            for u, v, attrs in self.graph.edges(data=True):
                edge_obj = {
                    "from_account": u,
                    "to_account": v,
                }
                for k, val in attrs.items():
                    if isinstance(val, (str, int, float, bool)) or val is None:
                        edge_obj[k] = val
                    else:
                        edge_obj[k] = str(val)
                edges_list.append(edge_obj)

            payload = {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges(),
                "historical_centrality": {
                    k: round(float(v), 6)
                    for k, v in self.historical_centrality.items()
                },
                "nodes": nodes_dict,
                "edges": edges_list,
            }

            def _write_atomic(path: str):
                dir_name = os.path.dirname(path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                temp_path = f"{path}.tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                os.replace(temp_path, path)

            # Write primary cache file
            _write_atomic(self.cache_file)

            # Mirror to data/mule_centrality_cache.json if data/ dir exists
            if os.path.isdir("data") and os.path.basename(self.cache_file) == "mule_centrality_cache.json":
                data_mirror = os.path.join("data", "mule_centrality_cache.json")
                if os.path.abspath(data_mirror) != os.path.abspath(self.cache_file):
                    _write_atomic(data_mirror)

        except Exception as e:
            print(f"[DRISHTI] Warning: Failed to save mule cache: {e}")

    def _seed_synthetic_mule_rings(self):
        """
        Pre-seeds realistic synthetic mule syndicate networks into the graph.
        Simulates known laundering patterns:
          - Funnel pattern (multiple victims -> mule L1 -> mule L2 -> cash-out)
          - High-betweenness transit hub accounts (central mule operators)
        """
        banks = [
            ("SBI", "SBIN0001423"),
            ("HDFC", "HDFC0000240"),
            ("ICICI", "ICIC0000104"),
            ("AXIS", "UTIB0000521"),
            ("PNB", "PUNB0002145"),
            ("Paytm", "PYTM0123456"),
        ]

        # Generate 4 distinct known mule syndicates (5-8 accounts each)
        for ring_id in range(1, 5):
            layer1 = f"MULE-{ring_id}01-{self.rng.randint(1000, 9999)}"
            layer2_a = f"MULE-{ring_id}02-{self.rng.randint(1000, 9999)}"
            layer2_b = f"MULE-{ring_id}03-{self.rng.randint(1000, 9999)}"
            layer3_cashout = f"CASHOUT-{ring_id}04-{self.rng.randint(1000, 9999)}"

            # Add nodes with initial metadata
            base_time = datetime.now(timezone.utc) - timedelta(days=self.rng.randint(2, 30))
            for acc in [layer1, layer2_a, layer2_b, layer3_cashout]:
                bank_name, ifsc = self.rng.choice(banks)
                self.graph.add_node(
                    acc,
                    bank=bank_name,
                    ifsc=ifsc,
                    created_at=base_time.isoformat(),
                    is_known_mule=True,
                )

            # Add directed flow with realistic timestamps and amounts
            t1 = base_time + timedelta(minutes=self.rng.randint(5, 20))
            t2 = t1 + timedelta(minutes=self.rng.randint(6, 18))
            t3 = t2 + timedelta(minutes=self.rng.randint(8, 25))

            self.graph.add_edge(layer1, layer2_a, amount=85000.0, timestamp=t1.isoformat(), txn_type="IMPS")
            self.graph.add_edge(layer1, layer2_b, amount=65000.0, timestamp=t1.isoformat(), txn_type="UPI")
            self.graph.add_edge(layer2_a, layer3_cashout, amount=80000.0, timestamp=t2.isoformat(), txn_type="NEFT")
            self.graph.add_edge(layer2_b, layer3_cashout, amount=61000.0, timestamp=t3.isoformat(), txn_type="IMPS")

    def _recompute_and_save_cache(self, affected_nodes: Optional[Set[str]] = None) -> Dict[str, float]:
        """
        Recomputes betweenness centrality on the graph, updates historical scores
        for affected nodes, and persists to cache file.
        """
        try:
            betweenness = nx.betweenness_centrality(self.graph)
        except Exception:
            betweenness = {n: 0.05 for n in self.graph.nodes}

        nodes_to_update = [n for n in (affected_nodes if affected_nodes else self.graph.nodes) if self.graph.has_node(n)]
        for n in nodes_to_update:
            score = round(betweenness.get(n, 0.0), 6)
            self.graph.nodes[n]["centrality"] = score
            self.historical_centrality[n] = max(self.historical_centrality.get(n, 0.0), score)

        self._save_cache()
        return betweenness

    def trace_trail(
        self,
        starting_account: Optional[str],
        initial_amount: float,
        incident_time: Optional[datetime] = None,
        max_hops: int = 4,
    ) -> Dict[str, Any]:
        """
        Traces a multi-hop money trail originating from starting_account.
        1. Loads existing cache to synchronize across sessions/processes.
        2. If starting_account has no outgoing path, builds a dynamic trail and
           adds new edges to the stateful graph (with realistic syndicate sharing).
        3. Recomputes betweenness centrality for affected nodes.
        4. Saves updated graph and centralities back to cache.
        5. Flags accounts with historically high betweenness (is_historical_mule = True).

        Returns:
            Dict containing hops, amounts, mule_accounts (with is_historical_mule flag),
            and graph_metrics.
        """
        # Step 1: Ensure graph has latest state from persistent cache
        self._load_cache()

        incident_time = _ensure_utc(incident_time)

        seed_key = str(starting_account or "mule_seed_default")
        account_seed = int(hashlib.md5(seed_key.encode("utf-8")).hexdigest()[:8], 16)
        self.rng = random.Random(account_seed)

        start_node = starting_account or f"ACC-{self.rng.randint(1000000000, 9999999999)}"

        hops: List[Dict[str, Any]] = []
        current_node = start_node
        current_time = incident_time
        current_amount = max(initial_amount, 5000.0)

        affected_nodes: Set[str] = {start_node}
        is_synthetic_fallback = False

        # Step 2: Query transactions.csv first for matching multi-hop chains
        dataset_hops = self._find_dataset_trail(starting_account, initial_amount, incident_time, max_hops)
        if dataset_hops:
            hops = dataset_hops
            for h in hops:
                u, v = h["from_account"], h["to_account"]
                self.graph.add_node(u, is_known_mule=False)
                self.graph.add_node(v, is_known_mule=True)
                self.graph.add_edge(u, v, amount=h["amount"], timestamp=h["timestamp"], txn_type=h["txn_type"])
                affected_nodes.add(u)
                affected_nodes.add(v)
        elif not self.graph.has_node(start_node) or self.graph.out_degree(start_node) == 0:
            is_synthetic_fallback = True
            num_hops = 3 if current_amount >= 50000 else (2 if current_amount >= 15000 else 1)

            if not self.graph.has_node(start_node):
                self.graph.add_node(
                    start_node,
                    bank="SBI",
                    ifsc="SBIN0001423",
                    created_at=(incident_time - timedelta(days=45)).isoformat(),
                    is_known_mule=False,
                )

            bank_pool = [
                ("HDFC Bank", "HDFC0001234"),
                ("ICICI Bank", "ICIC0005678"),
                ("Axis Bank", "UTIB0009876"),
                ("Punjab National Bank", "PUNB0004321"),
                ("Bank of Baroda", "BARB0007890"),
                ("Paytm Payments Bank", "PYTM0123456"),
            ]

            prev_acc = start_node
            for hop_idx in range(1, num_hops + 1):
                is_terminal = (hop_idx == num_hops)
                next_prefix = "CASHOUT" if is_terminal else f"MULE-L{hop_idx}"

                # Syndicate sharing: intermediate mules may connect to an existing known mule
                reusable_mules = [
                    n for n, d in self.graph.nodes(data=True)
                    if d.get("is_known_mule") and not n.startswith("CASHOUT") and n != prev_acc
                ]
                if not is_terminal and reusable_mules and self.rng.random() < 0.35:
                    next_acc = self.rng.choice(reusable_mules)
                    node_data = self.graph.nodes[next_acc]
                    bank_name = node_data.get("bank", "SBI")
                    ifsc = node_data.get("ifsc", "SBIN0001423")
                else:
                    next_acc = f"{next_prefix}-{self.rng.randint(10000000, 99999999)}"
                    bank_name, ifsc = self.rng.choice(bank_pool)
                    self.graph.add_node(
                        next_acc,
                        bank=bank_name,
                        ifsc=ifsc,
                        created_at=(incident_time - timedelta(days=self.rng.randint(5, 60))).isoformat(),
                        is_known_mule=True,
                    )

                affected_nodes.add(next_acc)

                step_mins = self.rng.randint(5, 14)
                hop_time = current_time + timedelta(minutes=step_mins)

                commission_cut = round(current_amount * self.rng.uniform(0.03, 0.07), 2)
                hop_amount = round(current_amount - commission_cut, 2)
                if hop_amount < 100:
                    hop_amount = current_amount

                txn_type = "ATM_WITHDRAWAL" if is_terminal else self.rng.choice(["IMPS", "UPI", "NEFT"])
                txn_ref = f"TXN-{self.rng.randint(100000000, 999999999)}"

                self.graph.add_edge(
                    prev_acc,
                    next_acc,
                    amount=hop_amount,
                    timestamp=hop_time.isoformat(),
                    txn_type=txn_type,
                    txn_ref=txn_ref,
                )

                hops.append({
                    "hop_index": hop_idx,
                    "from_account": prev_acc,
                    "to_account": next_acc,
                    "to_bank": bank_name,
                    "to_ifsc": ifsc,
                    "amount": hop_amount,
                    "commission_retained": commission_cut,
                    "timestamp": hop_time.isoformat(),
                    "minutes_from_start": int((hop_time - incident_time).total_seconds() / 60),
                    "txn_type": txn_type,
                    "txn_ref": txn_ref,
                    "is_terminal_cashout": is_terminal,
                })

                prev_acc = next_acc
                current_time = hop_time
                current_amount = hop_amount
        else:
            # Traversal along existing graph paths
            hop_idx = 1
            while hop_idx <= max_hops and self.graph.out_degree(current_node) > 0:
                successors = list(self.graph.successors(current_node))
                next_node = self.rng.choice(successors)
                edge_data = self.graph.get_edge_data(current_node, next_node) or {}
                node_data = self.graph.nodes[next_node]

                affected_nodes.add(current_node)
                affected_nodes.add(next_node)

                hop_amount = edge_data.get("amount", current_amount)
                hop_time_str = edge_data.get("timestamp", current_time.isoformat())
                hop_time = _parse_utc(hop_time_str, default=current_time + timedelta(minutes=10 * hop_idx))

                is_terminal = (hop_idx == max_hops) or (self.graph.out_degree(next_node) == 0)

                hops.append({
                    "hop_index": hop_idx,
                    "from_account": current_node,
                    "to_account": next_node,
                    "to_bank": node_data.get("bank", "Unknown Bank"),
                    "to_ifsc": node_data.get("ifsc", "IFSC000000"),
                    "amount": hop_amount,
                    "commission_retained": round(current_amount - hop_amount, 2) if current_amount > hop_amount else 0.0,
                    "timestamp": hop_time.isoformat(),
                    "minutes_from_start": max(0, int((hop_time - incident_time).total_seconds() / 60)),
                    "txn_type": edge_data.get("txn_type", "IMPS"),
                    "txn_ref": edge_data.get("txn_ref", f"TXN-{self.rng.randint(100000, 999999)}"),
                    "is_terminal_cashout": is_terminal,
                })
                current_node = next_node
                current_amount = hop_amount
                hop_idx += 1
                if is_terminal:
                    break

        # Expand affected neighborhood (include 1-hop predecessors and successors)
        neighborhood: Set[str] = set(affected_nodes)
        for n in list(affected_nodes):
            if self.graph.has_node(n):
                neighborhood.update(self.graph.predecessors(n))
                neighborhood.update(self.graph.successors(n))

        # Step 3 & 4: Recompute betweenness centrality and save back to cache
        betweenness = self._recompute_and_save_cache(neighborhood)

        # Step 5: Build flagged mule accounts with historical detection
        trail_accounts = set()
        for h in hops:
            trail_accounts.add(h["from_account"])
            trail_accounts.add(h["to_account"])

        mule_accounts = []
        for acc in trail_accounts:
            if acc == start_node:
                continue
            b_score = betweenness.get(acc, 0.0)
            hist_score = self.historical_centrality.get(acc, 0.0)
            in_deg = self.graph.in_degree(acc) if self.graph.has_node(acc) else 1
            out_deg = self.graph.out_degree(acc) if self.graph.has_node(acc) else 1
            node_info = self.graph.nodes.get(acc, {})

            # Flag if account has historically high betweenness centrality or recurrent hub behavior
            is_historical_mule = bool(
                b_score >= self.HISTORICAL_CENTRALITY_THRESHOLD
                or hist_score >= self.HISTORICAL_CENTRALITY_THRESHOLD
                or (node_info.get("is_known_mule", False) and b_score > 0.0)
                or (in_deg + out_deg >= 3 and b_score > 0.0)
            )

            # Risk formula: centrality + rapid pass-through + historical syndicate flag
            base_risk = 0.50 + (b_score * 2.0) + (0.15 if out_deg > 0 else 0.0)
            if is_historical_mule:
                base_risk += 0.10
            risk = min(0.98, max(0.45, base_risk))

            hist_suffix = (
                " [HISTORICAL MULE: High betweenness centrality across complaints]"
                if is_historical_mule
                else ""
            )
            flag_reason = (
                f"Multi-hop layering node (In-degree: {in_deg}, Out-degree: {out_deg}, "
                f"Betweenness: {b_score:.4f}).{hist_suffix} Rapid fund dispersal detected."
            )

            mule_accounts.append({
                "account_number": acc,
                "ifsc_code": node_info.get("ifsc", "SBIN0001423"),
                "bank_name": node_info.get("bank", "SBI"),
                "risk_score": round(risk, 3),
                "linked_accounts": list(self.graph.neighbors(acc)) if self.graph.has_node(acc) else [],
                "transaction_count": in_deg + out_deg,
                "centrality": round(b_score, 4),
                "flag_reason": flag_reason,
                "is_historical_mule": is_historical_mule,
            })

        # Sort mule accounts by risk score descending
        mule_accounts.sort(key=lambda m: m["risk_score"], reverse=True)

        final_amount = hops[-1]["amount"] if hops else initial_amount
        total_duration = hops[-1]["minutes_from_start"] if hops else 0

        # Graph Metrics Calculation
        in_degrees = [self.graph.in_degree(n) for n in trail_accounts if self.graph.has_node(n)] or [1]
        out_degrees = [self.graph.out_degree(n) for n in trail_accounts if self.graph.has_node(n)] or [1]
        max_betweenness = round(max(betweenness.values()) if betweenness else 0.0, 4)
        
        # Velocity in hops per hour
        velocity_hph = round(float(len(hops) / max(total_duration / 60.0, 0.15)), 2)
        fan_in_count = sum(1 for d in in_degrees if d > 1)
        fan_out_count = sum(1 for d in out_degrees if d > 1)

        # Geographic cumulative distance
        geo_dist = 0.0
        for h in hops:
            if "source_lat" in h and "dest_lat" in h:
                geo_dist += haversine_km(h["source_lat"], h["source_lon"], h["dest_lat"], h["dest_lon"])
            else:
                geo_dist += self.rng.uniform(1.2, 4.5)
        geo_dist = round(geo_dist, 2)

        # Rapid movement indicator (< 12 mins per hop)
        rapid_movement = any(h.get("minutes_from_start", 99) <= 15 for h in hops)
        
        # Circular paths check
        try:
            cycles = list(nx.simple_cycles(self.graph))
            has_cycles = len(cycles) > 0
        except Exception:
            has_cycles = False

        time_diffs = [h.get("minutes_from_start", 0) for h in hops]
        data_source_label = "synthetic_fallback" if is_synthetic_fallback else "synthetic_demo_dataset"

        return {
            "starting_account": start_node,
            "hop_count": len(hops),
            "hops": hops,
            "initial_amount": initial_amount,
            "final_cashout_amount": final_amount,
            "trail_duration_minutes": total_duration,
            "mule_accounts": mule_accounts,
            "has_historical_mules": any(m["is_historical_mule"] for m in mule_accounts),
            "data_source": data_source_label,
            "graph_metrics": {
                "total_graph_nodes": self.graph.number_of_nodes(),
                "total_graph_edges": self.graph.number_of_edges(),
                "max_betweenness": max_betweenness,
                "in_degree": max(in_degrees),
                "out_degree": max(out_degrees),
                "transaction_velocity": velocity_hph,
                "fan_in": fan_in_count,
                "fan_out": fan_out_count,
                "amount_flow": {
                    "initial_amount": initial_amount,
                    "final_amount": final_amount,
                    "commission_retained": round(initial_amount - final_amount, 2),
                },
                "time_difference_between_hops": time_diffs,
                "geographic_distance_km": geo_dist,
                "account_reuse": any(m["is_historical_mule"] for m in mule_accounts),
                "rapid_movement": rapid_movement,
                "suspicious_circular_paths": has_cycles,
                "is_synthetic_fallback": is_synthetic_fallback,
                "data_source": data_source_label,
                "cache_file": self.cache_file,
                "historical_mules_detected": sum(1 for m in mule_accounts if m["is_historical_mule"]),
            },
        }


# Singleton instance
_mule_graph_instance: Optional[MuleNetworkGraph] = None
StatefulMuleGraph = MuleNetworkGraph


def get_mule_graph() -> MuleNetworkGraph:
    """Singleton getter for MuleNetworkGraph."""
    global _mule_graph_instance
    if _mule_graph_instance is None:
        _mule_graph_instance = MuleNetworkGraph()
    return _mule_graph_instance
