"""
EXPERIMENT 3 — SCALED: MMR vs Standard Retrieval Comparison

Scale-up from original:
  - Queries: 10 → 20 per content source
  - Sources: 2 → 4 (2 web + 2 PDF)
  - Total comparisons: 20 → 80 query pairs

NO TOKEN COST: This experiment does NOT call the LLM at all.
It only uses the embedding model + ChromaDB locally.
You can run this immediately after experiments 1 and 2 on the same day
without worrying about the 100k token limit.

HOW TO RUN:
    1. Open terminal in your project root
    2. venv\Scripts\activate
    3. cd experiments
    4. python experiment3_mmr_evaluation.py
    (No GROQ_API_KEY needed for this experiment)
"""

import sys
import os
import time
import json
import csv
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import embedding_model, content_manager
from langchain_chroma import Chroma
import uuid

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# ── 4 content sources (2 web + 2 PDF) ────────────────────────────────────────
CONTENT_SOURCES = [
    {
        "url":   "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
        "label": "Web — RAG Wikipedia",
        "type":  "web",
    },
    {
        "url":   "https://en.wikipedia.org/wiki/Large_language_model",
        "label": "Web — LLM Wikipedia",
        "type":  "web",
    },
    {
        "url":   "https://arxiv.org/pdf/1706.03762",
        "label": "PDF — Attention is All You Need",
        "type":  "pdf",
    },
    {
        "url":   "https://arxiv.org/pdf/2005.11401",
        "label": "PDF — RAG Original Paper",
        "type":  "pdf",
    },
]

# ── 20 test queries (varied to stress-test retrieval diversity) ───────────────
TEST_QUERIES = [
    # Conceptual understanding
    "What is the main concept explained here?",
    "What problem does this work solve?",
    "What is the theoretical foundation of this approach?",
    "How is this different from previous methods?",
    # Methodology
    "What methodology or approach is used?",
    "Explain the architecture or system design",
    "What are the key components of this system?",
    "How are the components connected or integrated?",
    # Results and evaluation
    "What are the experimental results?",
    "What evaluation metrics are used?",
    "What datasets or sources are referenced?",
    "How does performance compare to baselines?",
    # Contributions and impact
    "Summarize the key contributions of this work",
    "What is novel about this approach?",
    "What are the practical applications?",
    "What future work is suggested?",
    # Limitations and context
    "What are the limitations mentioned?",
    "What assumptions does this work make?",
    "What background knowledge is assumed?",
    "How does this work fit into the broader field?",
]


# ─────────────────────────────────────────────────────────────────────────────
# Metric functions (pure Python — no LLM, no API calls)
# ─────────────────────────────────────────────────────────────────────────────

def word_overlap_similarity(text1: str, text2: str) -> float:
    """Jaccard similarity on word sets. Range 0.0–1.0."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    return len(words1 & words2) / len(words1 | words2)


def measure_diversity(chunks: list) -> float:
    """
    Average pairwise dissimilarity between all chunk pairs.
    Higher = more diverse = better.
    Range: 0.0 to 1.0
    """
    if len(chunks) < 2:
        return 1.0
    total, pairs = 0.0, 0
    for i in range(len(chunks)):
        for j in range(i + 1, len(chunks)):
            total += 1.0 - word_overlap_similarity(chunks[i], chunks[j])
            pairs += 1
    return round(total / pairs, 4) if pairs > 0 else 0.0


def measure_redundancy(chunks: list, threshold: float = 0.7) -> float:
    """
    Fraction of chunk pairs that are near-duplicates (similarity > threshold).
    Lower = less redundancy = better.
    Range: 0.0 to 1.0
    """
    if len(chunks) < 2:
        return 0.0
    redundant, pairs = 0, 0
    for i in range(len(chunks)):
        for j in range(i + 1, len(chunks)):
            if word_overlap_similarity(chunks[i], chunks[j]) > threshold:
                redundant += 1
            pairs += 1
    return round(redundant / pairs, 4) if pairs > 0 else 0.0


def measure_coverage(chunks: list, query: str) -> float:
    """
    Fraction of query terms that appear somewhere across all chunks.
    Higher = better query coverage.
    Range: 0.0 to 1.0
    """
    # Filter common stop words so coverage is meaningful
    stop_words = {
        "what", "is", "the", "this", "how", "are", "does", "do",
        "a", "an", "of", "in", "for", "to", "and", "or", "it",
        "here", "used", "mentioned", "suggested", "explained"
    }
    query_words = {
        w for w in query.lower().split() if w not in stop_words
    }
    if not query_words:
        return 1.0
    all_text = " ".join(chunks).lower()
    covered  = sum(1 for w in query_words if w in all_text)
    return round(covered / len(query_words), 4)


# ─────────────────────────────────────────────────────────────────────────────
# Core experiment function
# ─────────────────────────────────────────────────────────────────────────────

def run_mmr_vs_standard(source: dict):
    url   = source["url"]
    label = source["label"]

    print(f"\n  Source: {label}")
    print(f"  URL   : {url}")

    # Load and chunk the document
    from backend import WebContentProcessor
    processor = WebContentProcessor()
    documents = processor.process_url(url)
    print(f"  Chunks: {len(documents)}")

    if not documents:
        print(f"  [SKIPPED] No documents loaded.")
        return []

    # Build MMR retriever
    mmr_store = Chroma(
        collection_name=f"mmr_{str(uuid.uuid4())[:8]}",
        embedding_function=embedding_model
    )
    mmr_store.add_documents(documents)
    mmr_retriever = mmr_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "lambda_mult": 0.3}
    )

    # Build Standard similarity retriever
    std_store = Chroma(
        collection_name=f"std_{str(uuid.uuid4())[:8]}",
        embedding_function=embedding_model
    )
    std_store.add_documents(documents)
    std_retriever = std_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6}
    )

    results = []

    print(f"\n  {'Query':<42} {'MMRDiv':>7} {'StdDiv':>7} "
          f"{'MMRRed':>7} {'StdRed':>7} {'MMRCov':>7} {'StdCov':>7}")
    print(f"  {'-'*87}")

    for query in TEST_QUERIES:
        mmr_chunks = [d.page_content for d in mmr_retriever.invoke(query)]
        std_chunks = [d.page_content for d in std_retriever.invoke(query)]

        mmr_div = measure_diversity(mmr_chunks)
        std_div = measure_diversity(std_chunks)
        mmr_red = measure_redundancy(mmr_chunks)
        std_red = measure_redundancy(std_chunks)
        mmr_cov = measure_coverage(mmr_chunks, query)
        std_cov = measure_coverage(std_chunks, query)

        results.append({
            "source_label":   label,
            "source_type":    source["type"],
            "url":            url,
            "query":          query,
            "mmr_diversity":  mmr_div,
            "std_diversity":  std_div,
            "mmr_redundancy": mmr_red,
            "std_redundancy": std_red,
            "mmr_coverage":   mmr_cov,
            "std_coverage":   std_cov,
            "mmr_chunks_retrieved": len(mmr_chunks),
            "std_chunks_retrieved": len(std_chunks),
            "timestamp":      datetime.now().isoformat(),
        })

        short_q = query[:40] + ".." if len(query) > 40 else query
        print(f"  {short_q:<42} {mmr_div:>7.4f} {std_div:>7.4f} "
              f"{mmr_red:>7.4f} {std_red:>7.4f} {mmr_cov:>7.4f} {std_cov:>7.4f}")

    return results


def print_summary(all_results):
    print("\n" + "=" * 65)
    print("EXPERIMENT 3 — FULL SUMMARY")
    print("=" * 65)

    def avg(key):
        return sum(r[key] for r in all_results) / len(all_results)

    mmr_div = avg("mmr_diversity")
    std_div = avg("std_diversity")
    mmr_red = avg("mmr_redundancy")
    std_red = avg("std_redundancy")
    mmr_cov = avg("mmr_coverage")
    std_cov = avg("std_coverage")

    div_imp = (mmr_div - std_div) / std_div * 100 if std_div > 0 else 0
    red_imp = (std_red - mmr_red) / std_red * 100 if std_red > 0 else 0
    cov_imp = (mmr_cov - std_cov) / std_cov * 100 if std_cov > 0 else 0

    print(f"\n  Overall ({len(all_results)} query pairs across {len(CONTENT_SOURCES)} sources)")
    print(f"\n  {'Metric':<22} {'MMR (λ=0.3)':>12} {'Standard':>12} {'Change':>12}")
    print(f"  {'-'*60}")
    print(f"  {'Diversity Score':<22} {mmr_div:>12.4f} {std_div:>12.4f}  "
          f"{'+' if div_imp >= 0 else ''}{div_imp:.2f}%")
    print(f"  {'Redundancy Score':<22} {mmr_red:>12.4f} {std_red:>12.4f}  "
          f"{'+' if red_imp >= 0 else ''}{red_imp:.2f}% (↓ better)")
    print(f"  {'Coverage Score':<22} {mmr_cov:>12.4f} {std_cov:>12.4f}  "
          f"{'+' if cov_imp >= 0 else ''}{cov_imp:.2f}%")

    # Per content type breakdown
    print(f"\n  Breakdown by content type:")
    for ctype in ["web", "pdf"]:
        subset = [r for r in all_results if r["source_type"] == ctype]
        if not subset:
            continue
        s_div = sum(r["mmr_diversity"]  for r in subset) / len(subset)
        s_red = sum(r["mmr_redundancy"] for r in subset) / len(subset)
        s_cov = sum(r["mmr_coverage"]   for r in subset) / len(subset)
        b_div = sum(r["std_diversity"]  for r in subset) / len(subset)
        b_red = sum(r["std_redundancy"] for r in subset) / len(subset)
        b_cov = sum(r["std_coverage"]   for r in subset) / len(subset)
        print(f"\n    {ctype.upper()} ({len(subset)} queries):")
        print(f"      Diversity : MMR={s_div:.4f}  Std={b_div:.4f}  "
              f"Δ={'+' if s_div>=b_div else ''}{(s_div-b_div)/b_div*100:.2f}%")
        print(f"      Redundancy: MMR={s_red:.4f}  Std={b_red:.4f}  "
              f"Δ={'+' if s_red<=b_red else ''}{(b_red-s_red)/b_red*100 if b_red>0 else 0:.2f}% (↓ better)")
        print(f"      Coverage  : MMR={s_cov:.4f}  Std={b_cov:.4f}  "
              f"Δ={'+' if s_cov>=b_cov else ''}{(s_cov-b_cov)/b_cov*100:.2f}%")

    return {
        "total_query_pairs":        len(all_results),
        "sources_tested":           len(CONTENT_SOURCES),
        "mmr_diversity_avg":        mmr_div,
        "std_diversity_avg":        std_div,
        "diversity_improvement_pct": div_imp,
        "mmr_redundancy_avg":       mmr_red,
        "std_redundancy_avg":       std_red,
        "redundancy_reduction_pct": red_imp,
        "mmr_coverage_avg":         mmr_cov,
        "std_coverage_avg":         std_cov,
        "coverage_improvement_pct": cov_imp,
    }


def save_results(all_results, summary):
    path = os.path.join(RESULTS_DIR, "exp3_mmr_results.json")
    with open(path, "w") as f:
        json.dump({"summary": summary, "results": all_results}, f, indent=2)
    print(f"\n  Saved: {path}")

    path = os.path.join(RESULTS_DIR, "exp3_mmr_results.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
        writer.writeheader()
        writer.writerows(all_results)
    print(f"  Saved: {path}")

    print("\n" + "=" * 65)
    print("EXPERIMENT 3 COMPLETE")
    print("=" * 65)
    print("All 3 experiments done. Next: run generate_graphs.py")


if __name__ == "__main__":
    print("\nEXPERIMENT 3 (SCALED): MMR vs Standard Retrieval")
    print(f"Testing {len(TEST_QUERIES)} queries × {len(CONTENT_SOURCES)} sources "
          f"= {len(TEST_QUERIES) * len(CONTENT_SOURCES)} total comparisons\n")

    all_results = []
    for source in CONTENT_SOURCES:
        print("=" * 65)
        results = run_mmr_vs_standard(source)
        all_results.extend(results)

    if all_results:
        summary = print_summary(all_results)
        save_results(all_results, summary)
    else:
        print("No results collected — check content loading.")