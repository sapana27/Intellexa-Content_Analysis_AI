"""
EXPERIMENT 2: Content Loading Success Rate + Query Routing Accuracy

FILE NAME : experiment2_content_routing.py
LOCATION  : INTELLEXA-CONTENT_ANALYSI.../experiments/experiment2_content_routing.py

FOLDER STRUCTURE:
    INTELLEXA-CONTENT_ANALYSI.../
    ├── experiments/
    │   ├── experiment1_response_time.py   (already done)
    │   ├── experiment2_content_routing.py ← THIS FILE
    │   ├── generate_graphs.py
    │   └── results/
    │       ├── exp1_results.json
    │       ├── exp1_results.csv
    │       ├── exp2_content_loading.json      (auto-created)
    │       ├── exp2_content_loading.csv       (auto-created)
    │       ├── exp2_routing_accuracy.json     (auto-created)
    │       └── figures/

HOW TO RUN:
    1. Open terminal in your project root
    2. venv\Scripts\activate
    3. $env:GROQ_API_KEY="your_key_here"
    4. cd experiments
    5. python experiment2_content_routing.py
"""

import sys
import os
import time
import json
import csv
from datetime import datetime
from collections import defaultdict

# ── Add parent folder so we can import backend.py ────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import app, content_manager
from langchain_core.messages import HumanMessage

# ── Output folders (auto-created) ────────────────────────────────────────────
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# PART A — Content Loading Success Rate
# Tests 10 web URLs and 10 PDF URLs
# Records: load time, success/fail, error message
# ─────────────────────────────────────────────────────────────────────────────

WEB_URLS = [
    "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
    "https://en.wikipedia.org/wiki/Large_language_model",
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://en.wikipedia.org/wiki/Transformer_(machine_learning_model)",
    "https://en.wikipedia.org/wiki/Vector_database",
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://en.wikipedia.org/wiki/Deep_learning",
    "https://en.wikipedia.org/wiki/Chatbot",
    "https://en.wikipedia.org/wiki/Knowledge_graph",
    "https://en.wikipedia.org/wiki/Machine_learning",
]

PDF_URLS = [
    "https://arxiv.org/pdf/1706.03762",   # Attention is All You Need
    "https://arxiv.org/pdf/1810.04805",   # BERT
    "https://arxiv.org/pdf/2005.11401",   # RAG original paper
    "https://arxiv.org/pdf/2106.09685",   # LoRA
    "https://arxiv.org/pdf/1910.10683",   # T5
    "https://arxiv.org/pdf/2302.13971",   # LLaMA
    "https://arxiv.org/pdf/2307.09288",   # LLaMA 2
    "https://arxiv.org/pdf/2204.02311",   # PaLM
    "https://arxiv.org/pdf/2112.10403",   # WebGPT
    "https://arxiv.org/pdf/2203.02155",   # Chain of Thought
]

def run_content_loading_test():
    print("=" * 65)
    print("PART A: Content Loading Success Rate")
    print("=" * 65)

    all_results = []

    for label, urls in [("Web/Wikipedia", WEB_URLS), ("PDF/ArXiv", PDF_URLS)]:
        print(f"\nTesting {label} ({len(urls)} URLs)...")
        print(f"  {'#':<4} {'Time':>6}  {'Status':<6}  URL")
        print(f"  {'-'*60}")

        for i, url in enumerate(urls, 1):
            start   = time.time()
            success = True
            error   = ""

            try:
                ok, msg = content_manager.load_web_content(url)
                elapsed = round(time.time() - start, 2)
                if not ok:
                    success = False
                    error   = msg
            except Exception as e:
                elapsed = round(time.time() - start, 2)
                success = False
                error   = str(e)[:80]

            all_results.append({
                "index":        i,
                "content_type": label,
                "url":          url,
                "load_time":    elapsed,
                "success":      success,
                "error":        error,
                "timestamp":    datetime.now().isoformat(),
            })

            status = "OK" if success else "FAIL"
            short_url = url.replace("https://", "")[:50]
            print(f"  {i:<4} {elapsed:>5.2f}s  {status:<6}  {short_url}")

            # Small delay to avoid overwhelming servers
            time.sleep(1.0)

    # Summary
    print("\n" + "=" * 65)
    print("PART A SUMMARY")
    print("=" * 65)
    by_type = defaultdict(lambda: {"total": 0, "success": 0, "times": []})
    for r in all_results:
        ct = r["content_type"]
        by_type[ct]["total"] += 1
        if r["success"]:
            by_type[ct]["success"] += 1
            by_type[ct]["times"].append(r["load_time"])

    for ct, data in sorted(by_type.items()):
        rate     = data["success"] / data["total"] * 100
        avg_time = sum(data["times"]) / len(data["times"]) if data["times"] else 0
        print(f"  {ct:<20}  {data['success']}/{data['total']}  success={rate:.0f}%  avg_load={avg_time:.2f}s")

    return all_results

# ─────────────────────────────────────────────────────────────────────────────
# PART B — Query Routing Accuracy
# Sends 15 queries to the router and checks if it routes correctly
# No need for content to be loaded — just tests the routing logic
# ─────────────────────────────────────────────────────────────────────────────

# (query, expected_route, description)
ROUTING_TEST_QUERIES = [
    # General queries — should route to general_query
    ("Hello how are you",                                       "general_query",  "greeting"),
    ("What can you do?",                                        "general_query",  "capability question"),
    ("Tell me about yourself",                                  "general_query",  "identity question"),
    ("Good morning",                                            "general_query",  "greeting"),
    ("What is artificial intelligence?",                        "general_query",  "general knowledge"),

    # Video queries — should route to video_qa
    ("What is this YouTube video about?",                       "video_qa",       "video topic"),
    ("Summarize the YouTube video for me",                      "video_qa",       "video summary"),
    ("What did the speaker say at minute 5?",                   "video_qa",       "timestamp query"),
    ("Give me timestamps from the video",                       "video_qa",       "timestamp request"),
    ("Explain the main points in this video tutorial",          "video_qa",       "video content"),

    # Web content queries — should route to web_content
    ("Summarize this research paper",                           "web_content",    "paper summary"),
    ("What are the key findings of this article?",              "web_content",    "article analysis"),
    ("Explain the methodology in this PDF",                     "web_content",    "pdf analysis"),
    ("What does this document say about neural networks?",      "web_content",    "document query"),
    ("Give me the abstract of this research",                   "web_content",    "abstract request"),
]

def run_routing_accuracy_test():
    print("\n" + "=" * 65)
    print("PART B: Query Routing Accuracy")
    print("=" * 65)
    print(f"\nTesting {len(ROUTING_TEST_QUERIES)} queries across 3 route types...\n")
    print(f"  {'#':<4} {'Expected':<16} {'Got':<16} {'OK?':<5}  Query")
    print(f"  {'-'*70}")

    config  = {"configurable": {"thread_id": "exp2_routing_thread"}}
    results = []
    correct = 0

    for i, (query, expected, description) in enumerate(ROUTING_TEST_QUERIES, 1):
        start = time.time()

        try:
            # We invoke the app and check which handler ran
            # For routing test: no current_source so router decides purely on query
            response = app.invoke(
                {
                    "messages":       [HumanMessage(content=query)],
                    "current_source": None,
                    "generate_audio": False,
                },
                config={"configurable": {"thread_id": f"routing_test_{i}"}}
            )
            elapsed = round(time.time() - start, 2)

            # Check the state decision
            # We infer actual route from response content patterns
            response_text = response["messages"][-1].content.lower()

            # Heuristic: if response mentions video/timestamp → video_qa
            # if response mentions loading content/url → web_content
            # otherwise → general_query
            if any(w in response_text for w in ["transcript", "timestamp", "video", "minute", "youtube"]):
                actual = "video_qa"
            elif any(w in response_text for w in ["load", "url", "source", "document", "article", "paper", "pdf"]):
                actual = "web_content"
            else:
                actual = "general_query"

            is_correct = actual == expected
            if is_correct:
                correct += 1

        except Exception as e:
            elapsed    = round(time.time() - start, 2)
            actual     = "error"
            is_correct = False

        results.append({
            "index":       i,
            "query":       query,
            "description": description,
            "expected":    expected,
            "actual":      actual,
            "correct":     is_correct,
            "time":        elapsed,
            "timestamp":   datetime.now().isoformat(),
        })

        status   = "✓" if is_correct else "✗"
        actual_s = actual[:14]
        print(f"  {i:<4} {expected:<16} {actual_s:<16} {status:<5}  {query[:40]}")

        time.sleep(0.5)

    accuracy = correct / len(ROUTING_TEST_QUERIES) * 100
    print(f"\n  Routing Accuracy: {correct}/{len(ROUTING_TEST_QUERIES)} = {accuracy:.1f}%")

    # Per-route accuracy
    print("\n  Per-route breakdown:")
    by_route = defaultdict(lambda: {"total": 0, "correct": 0})
    for r in results:
        by_route[r["expected"]]["total"] += 1
        if r["correct"]:
            by_route[r["expected"]]["correct"] += 1

    for route, data in sorted(by_route.items()):
        rate = data["correct"] / data["total"] * 100
        print(f"    {route:<20}  {data['correct']}/{data['total']}  = {rate:.0f}%")

    return results, accuracy

# ─────────────────────────────────────────────────────────────────────────────
# SAVE ALL RESULTS
# ─────────────────────────────────────────────────────────────────────────────

def save_results(content_results, routing_results, routing_accuracy):
    # Save content loading JSON
    path = os.path.join(RESULTS_DIR, "exp2_content_loading.json")
    with open(path, "w") as f:
        json.dump(content_results, f, indent=2)
    print(f"\n  Saved: {path}")

    # Save content loading CSV
    path = os.path.join(RESULTS_DIR, "exp2_content_loading.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=content_results[0].keys())
        writer.writeheader()
        writer.writerows(content_results)
    print(f"  Saved: {path}")

    # Save routing results JSON
    path = os.path.join(RESULTS_DIR, "exp2_routing_accuracy.json")
    with open(path, "w") as f:
        json.dump({
            "accuracy_percent": routing_accuracy,
            "total_queries":    len(routing_results),
            "results":          routing_results,
        }, f, indent=2)
    print(f"  Saved: {path}")

    # Save routing CSV
    path = os.path.join(RESULTS_DIR, "exp2_routing_accuracy.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=routing_results[0].keys())
        writer.writeheader()
        writer.writerows(routing_results)
    print(f"  Saved: {path}")

    print("\n" + "="*65)
    print("EXPERIMENT 2 COMPLETE")
    print("="*65)
    print(f"  Content loading results → exp2_content_loading.json/.csv")
    print(f"  Routing accuracy results → exp2_routing_accuracy.json/.csv")
    print(f"\nNext step: run experiment3_mmr_evaluation.py")

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nEXPERIMENT 2: Content Loading Success Rate + Query Routing Accuracy\n")
    content_results                  = run_content_loading_test()
    routing_results, routing_accuracy = run_routing_accuracy_test()
    save_results(content_results, routing_results, routing_accuracy)