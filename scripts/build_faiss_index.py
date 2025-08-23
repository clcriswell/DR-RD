#!/usr/bin/env python3
import argparse, os, json, re, sys
import numpy as np
import faiss

def _embed(text: str, dim: int = 128) -> np.ndarray:
    vec = np.zeros(dim, dtype="float32")
    for i, token in enumerate(text.split()):
        vec[i % dim] += (hash(token) % 1000) / 1000.0
    return vec

def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception:
        return ""

def _collect_docs(root: str) -> tuple[list[str], list[str]]:
    paths: list[str] = []
    readme = os.path.join(root, "README.md")
    if os.path.exists(readme):
        paths.append(readme)
    doc_root = os.path.join(root, "docs")
    for base, _, files in os.walk(doc_root):
        for f in files:
            if f.lower().endswith((".md", ".txt", ".rst")):
                paths.append(os.path.join(base, f))
    texts, sources = [], []
    for p in paths:
        t = _read_text(p)
        if t.strip():
            texts.append(t)
            sources.append(os.path.relpath(p, root))
    return texts, sources

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", "--src", dest="root", default=".", help="repo/corpus root")
    ap.add_argument("--out", "--dst", dest="out", default="memory", help="output dir")
    args = ap.parse_args()

    texts, sources = _collect_docs(args.root)
    if not texts:
        print("No docs found under README.md or ./docs", file=sys.stderr)
        raise SystemExit(1)

    xb = np.vstack([_embed(t) for t in texts])
    index = faiss.IndexFlatL2(xb.shape[1])
    index.add(xb)

    os.makedirs(args.out, exist_ok=True)
    faiss.write_index(index, os.path.join(args.out, "index.faiss"))
    docs = [{"text": t, "source": s} for t, s in zip(texts, sources)]
    with open(os.path.join(args.out, "docs.json"), "w", encoding="utf-8") as fh:
        json.dump(docs, fh)

    print(
        f"Wrote {len(docs)} docs to {args.out}/index.faiss and {args.out}/docs.json (root={args.root})"
    )

if __name__ == "__main__":
    main()
