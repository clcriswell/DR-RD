from __future__ import annotations
from typing import List, Dict, Any, Tuple, Iterable, Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class Node:
    id: str
    label: str
    phase: str
    status: str
    dur_ms: int

@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    kind: str  # "seq" | "data"

STATUS_COLOR = {
    "success": "#16a34a",
    "warn":    "#d97706",
    "error":   "#dc2626",
    "cancelled":"#6b7280",
    "timeout": "#9333ea",
    "running": "#0ea5e9",
    "unknown": "#64748b",
}

def build_graph(rows: List[Dict[str, Any]]) -> Tuple[List[Node], List[Edge]]:
    """
    rows: flatten_trace_rows(trace) items with keys:
      i, id?, phase, name, status, duration_ms, parents? (list[str])
    If 'id' missing, synthesize 's{i}'. If 'parents' missing, add sequential edges within each phase.
    """
    nodes: List[Node] = []
    edges: List[Edge] = []
    # Build nodes
    for r in rows:
        sid = str(r.get("id") or f"s{r['i']}")
        status = str(r.get("status") or "unknown")
        nodes.append(Node(
            id=sid,
            label=f"{r.get('name','step')}\\n{int(r.get('duration_ms',0))/1000:.1f}s",
            phase=str(r.get("phase","")),
            status=status,
            dur_ms=int(r.get("duration_ms",0)),
        ))
    # Index by phase for sequential edges
    by_phase: Dict[str, List[Node]] = {}
    for n in nodes:
        by_phase.setdefault(n.phase, []).append(n)
    for ph, L in by_phase.items():
        L.sort(key=lambda n: int(n.id.replace("s","")) if n.id.startswith("s") else 0)
        for a, b in zip(L, L[1:]):
            edges.append(Edge(src=a.id, dst=b.id, kind="seq"))
    # Explicit parents if present
    id_map = {n.id: n for n in nodes}
    for r in rows:
        sid = str(r.get("id") or f"s{r['i']}")
        for p in r.get("parents", []) or []:
            if p in id_map:
                edges.append(Edge(src=p, dst=sid, kind="data"))
    return nodes, edges

def critical_path(nodes: List[Node], edges: List[Edge]) -> List[str]:
    """
    Longest-duration path (ms) in DAG. If cycles exist, ignore offending edges.
    Returns list of node ids on the critical path in order.
    """
    # Topo sort
    adj: Dict[str, List[str]] = {}
    indeg: Dict[str, int] = {n.id: 0 for n in nodes}
    for e in edges:
        adj.setdefault(e.src, []).append(e.dst)
        if e.dst in indeg: indeg[e.dst] += 1
    q = [nid for nid, d in indeg.items() if d == 0]
    order: List[str] = []
    while q:
        u = q.pop(0)
        order.append(u)
        for v in adj.get(u, []):
            indeg[v] -= 1
            if indeg[v] == 0: q.append(v)
    # DP longest path by dur_ms
    dur = {n.id: n.dur_ms for n in nodes}
    best = {nid: (dur.get(nid,0), None) for nid in order}  # (cost, prev)
    for u in order:
        for v in adj.get(u, []):
            cand = best[u][0] + dur.get(v,0)
            if cand > best.get(v,(0,None))[0]:
                best[v] = (cand, u)
    # Pick end with max cost
    end = max(best.items(), key=lambda kv: kv[0] in order and kv[1][0] or 0)[0]
    # Reconstruct
    path = []
    cur = end
    seen = set()
    while cur and cur not in seen:
        path.append(cur); seen.add(cur)
        cur = best.get(cur,(0,None))[1]
    path.reverse()
    return path

def to_dot(nodes: List[Node], edges: List[Edge], *, highlight: Iterable[str] = ()) -> str:
    hi = set(highlight or [])
    lines = ["digraph G {", 'rankdir=LR;', 'node [shape=box, style="rounded,filled", fontname="Inter,Arial"];']
    # clusters by phase
    by_phase: Dict[str, List[Node]] = {}
    for n in nodes: by_phase.setdefault(n.phase or "phase", []).append(n)
    for i,(ph,L) in enumerate(by_phase.items()):
        lines.append(f'subgraph cluster_{i} {{ label="{ph}"; color="#e5e7eb";')
        for n in L:
            col = STATUS_COLOR.get(n.status, STATUS_COLOR["unknown"])
            pen = "#111827" if n.id in hi else "#6b7280"
            lines.append(f'"{n.id}" [label="{n.label}", fillcolor="{col}22", color="{pen}"];')
        lines.append("}")
    for e in edges:
        style = "bold" if e.kind == "data" else "solid"
        color = "#64748b" if e.kind == "seq" else "#0ea5e9"
        lines.append(f'"{e.src}" -> "{e.dst}" [color="{color}", style="{style}"];')
    lines.append("}")
    return "\n".join(lines)
