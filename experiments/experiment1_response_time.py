"""
EXPERIMENT 1 — FINAL: Response Time Benchmarking for Intellexa
45 queries total (15 per content type: 5 short + 5 medium + 5 long)
Safe for Groq free tier 100,000 token/day limit with llama-3.3-70b-versatile + max_tokens=500

Estimated token usage:
  15 web queries     × ~2000 tokens = 30,000
  15 PDF queries     × ~2300 tokens = 34,500
  15 general queries ×  ~700 tokens = 10,500
  Preload overhead                  =  3,000
  TOTAL                             = 78,000  (safely under 100k)

HOW TO RUN:
    1. Open terminal in your project root
    2. venv\Scripts\activate
    3. set GROQ_API_KEY=your_key_here
    4. cd experiments
    5. python experiment1_response_time.py

BEFORE RUNNING — confirm backend.py has:
    llm = ChatGroq(temperature=0.4, model_name='llama-3.3-70b-versatile', max_tokens=500)
"""

import sys
import os
import re
import time
import json
import csv
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import app, content_manager
from langchain_core.messages import HumanMessage

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# ── Content sources (2 sources per type is enough at this scale) ──────────────
WEB_SOURCES = [
    "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
    "https://en.wikipedia.org/wiki/Large_language_model",
]

PDF_SOURCES = [
    "https://arxiv.org/pdf/1706.03762",   # Attention is All You Need
    "https://arxiv.org/pdf/2005.11401",   # RAG original paper
]

# ── 5 queries per length tier ─────────────────────────────────────────────────
SHORT_QUERIES = [
    "What is this about?",
    "What is the main topic?",
    "What problem does this solve?",
    "What is the key idea?",
    "What method is used?",
]

MEDIUM_QUERIES = [
    "Summarize the main points of this content.",
    "What are the key contributions described here?",
    "Explain the approach taken in this work.",
    "What limitations are acknowledged by the authors?",
    "What are the practical applications of this work?",
]

LONG_QUERIES = [
    "Provide a comprehensive analysis of all key concepts discussed, including methodology, results, and implications.",
    "Explain in detail the experimental setup, the results obtained, and what conclusions can be drawn from them.",
    "Describe the full system architecture including all components, how they interact, and why each design choice was made.",
    "Compare and contrast the approach described here with existing methods, highlighting what is novel and what remains.",
    "Summarize the entire document covering motivation, methods, experiments, results, limitations, and future directions.",
]

# ── General queries — genuinely general, no document source needed ────────────
GENERAL_SHORT_QUERIES = [
    "Hello, how are you?",
    "What can you help me with?",
    "Who are you?",
    "What do you do?",
    "Can you help me?",
]

GENERAL_MEDIUM_QUERIES = [
    "What is machine learning and how does it work?",
    "Can you explain what artificial intelligence is?",
    "What is the difference between AI and machine learning?",
    "How does a neural network learn from data?",
    "Explain what a large language model is.",
]

GENERAL_LONG_QUERIES = [
    "Can you give me a detailed explanation of how retrieval-augmented generation works and why it is useful?",
    "Describe in detail what makes transformer-based models effective compared to earlier sequence models like RNNs.",
    "What are the main differences between supervised, unsupervised, and reinforcement learning, with examples of each?",
    "Explain thoroughly how attention mechanisms work in neural networks and what problem they were designed to solve.",
    "Can you explain in detail how vector databases work and why they are important for AI applications?",
]


def build_test_cases():
    """
    45 total: 15 web + 15 PDF + 15 general
    Each group: 5 short + 5 medium + 5 long
    Web/PDF alternate between 2 sources to add variety.
    """
    cases = []

    # Web queries — alternate sources for variety
    for i, q in enumerate(SHORT_QUERIES):
        cases.append((q, "web", "short", WEB_SOURCES[i % len(WEB_SOURCES)]))
    for i, q in enumerate(MEDIUM_QUERIES):
        cases.append((q, "web", "medium", WEB_SOURCES[i % len(WEB_SOURCES)]))
    for i, q in enumerate(LONG_QUERIES):
        cases.append((q, "web", "long", WEB_SOURCES[i % len(WEB_SOURCES)]))

    # PDF queries — alternate sources
    for i, q in enumerate(SHORT_QUERIES):
        cases.append((q, "pdf", "short", PDF_SOURCES[i % len(PDF_SOURCES)]))
    for i, q in enumerate(MEDIUM_QUERIES):
        cases.append((q, "pdf", "medium", PDF_SOURCES[i % len(PDF_SOURCES)]))
    for i, q in enumerate(LONG_QUERIES):
        cases.append((q, "pdf", "long", PDF_SOURCES[i % len(PDF_SOURCES)]))

    # General queries — no source
    for q in GENERAL_SHORT_QUERIES:
        cases.append((q, "general", "short", None))
    for q in GENERAL_MEDIUM_QUERIES:
        cases.append((q, "general", "medium", None))
    for q in GENERAL_LONG_QUERIES:
        cases.append((q, "general", "long", None))

    return cases


def preload_all_sources():
    print("=" * 65)
    print("PRE-LOADING CONTENT SOURCES")
    print("=" * 65)
    for url in WEB_SOURCES + PDF_SOURCES:
        print(f"  Loading: {url[:60]}...")
        ok, msg = content_manager.load_web_content(url)
        print(f"    [{'OK' if ok else 'FAILED'}] {msg[:60]}")
        time.sleep(1.0)
    print()


def invoke_with_retry(query, source_url, config, max_retries=3):
    """
    Calls app.invoke() with automatic retry on Groq 429 rate limit.
    Parses the wait time from the error message so it waits exactly
    as long as Groq asks, rather than a fixed delay.
    Returns: (elapsed_seconds, success_bool, error_string)
    """
    for attempt in range(1, max_retries + 1):
        start = time.time()
        try:
            app.invoke(
                {
                    "messages":       [HumanMessage(content=query)],
                    "current_source": source_url,
                    "generate_audio": False,
                },
                config=config
            )
            elapsed = round(time.time() - start, 2)
            return elapsed, True, ""

        except Exception as e:
            elapsed = round(time.time() - start, 2)
            err_str = str(e)

            if "rate_limit_exceeded" in err_str or "429" in err_str:
                wait_seconds = 90  # safe default if parsing fails
                # Try to parse exact wait time: "try again in 24m34.848s"
                match = re.search(r'try again in (?:(\d+)h)?(?:(\d+)m)?([\d.]+)s', err_str)
                if match:
                    hours   = int(match.group(1) or 0)
                    minutes = int(match.group(2) or 0)
                    seconds = float(match.group(3) or 0)
                    wait_seconds = hours * 3600 + minutes * 60 + seconds + 10
                    wait_seconds = min(wait_seconds, 600)  # cap at 10 minutes

                print(f"\n  [RATE LIMIT] Attempt {attempt}/{max_retries}.")
                print(f"  Waiting {wait_seconds:.0f}s as requested by Groq...")
                time.sleep(wait_seconds)
                continue
            else:
                return elapsed, False, err_str[:120]

    return 0.0, False, "Rate limit — all retries exhausted"


def run_experiment():
    test_cases = build_test_cases()
    results    = []

    print("=" * 65)
    print(f"EXPERIMENT 1: {len(test_cases)} queries  "
          f"(15 web + 15 PDF + 15 general)")
    print(f"Model: llama-3.3-70b-versatile  |  max_tokens: 500")
    print("=" * 65)
    print(f"\n{'#':<5} {'Type':<10} {'Length':<8} {'Time':>7}  {'Status'}  Query")
    print("-" * 72)

    for i, (query, content_type, query_len, source_url) in enumerate(test_cases, 1):
        config  = {"configurable": {"thread_id": f"exp1_{i}"}}
        elapsed, success, error = invoke_with_retry(query, source_url, config)

        results.append({
            "query_no":      i,
            "query":         query[:60] + "..." if len(query) > 60 else query,
            "content_type":  content_type,
            "query_length":  query_len,
            "source_url":    source_url or "N/A",
            "response_time": elapsed,
            "success":       success,
            "error":         error,
            "timestamp":     datetime.now().isoformat(),
        })

        status = "OK" if success else "FAIL"
        print(f"{i:<5} {content_type:<10} {query_len:<8} "
              f"{elapsed:>6.2f}s  {status:<6}  {query[:32]}")

        # Incremental save every 10 queries — no data lost on Ctrl+C
        if i % 10 == 0:
            _save_incremental(results)

        time.sleep(3.0)  # 3s gap keeps token rate well within per-minute limits

    return results


def _save_incremental(results):
    path = os.path.join(RESULTS_DIR, "exp1_partial.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  [Saved {len(results)} results so far → exp1_partial.json]")


def save_and_summarize(results):
    # Exclude sub-0.5s successes — these are silent backend error catches,
    # not genuine LLM responses (real responses always take >0.5s with network)
    valid     = [r for r in results if r["success"] and r["response_time"] >= 0.5]
    anomalous = [r for r in results if r["success"] and r["response_time"] < 0.5]
    failed    = [r for r in results if not r["success"]]

    # ── Save full results ─────────────────────────────────────────────────────
    json_path = os.path.join(RESULTS_DIR, "exp1_results.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    csv_path = os.path.join(RESULTS_DIR, "exp1_results.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # ── Print summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("RESULTS SUMMARY")
    print("=" * 65)

    if anomalous:
        print(f"\n  Excluded {len(anomalous)} anomalous results (<0.5s success)")
        print(f"  These are rate-limit errors silently caught by backend.\n")
    if failed:
        print(f"  {len(failed)} outright failures (see CSV for error details).\n")

    print(f"  {'Content Type':<12} {'n':>4}  {'Avg':>7}  {'Std':>7}  "
          f"{'Min':>7}  {'Max':>7}")
    print(f"  {'-'*52}")

    by_type = defaultdict(list)
    for r in valid:
        by_type[r["content_type"]].append(r["response_time"])

    for ct in ["web", "pdf", "general"]:
        times = by_type.get(ct, [])
        if not times:
            print(f"  {ct:<12}  No valid results")
            continue
        avg = sum(times) / len(times)
        std = (sum((t - avg) ** 2 for t in times) / len(times)) ** 0.5
        print(f"  {ct:<12} {len(times):>4}  {avg:>6.2f}s  {std:>6.2f}s  "
              f"{min(times):>6.2f}s  {max(times):>6.2f}s")

    print(f"\n  {'Query Length':<12} {'n':>4}  {'Avg':>7}")
    print(f"  {'-'*28}")
    by_len = defaultdict(list)
    for r in valid:
        by_len[r["query_length"]].append(r["response_time"])
    for ql in ["short", "medium", "long"]:
        times = by_len[ql]
        if times:
            avg = sum(times) / len(times)
            print(f"  {ql:<12} {len(times):>4}  {avg:>6.2f}s")

    total_ok = sum(1 for r in results if r["success"])
    print(f"\n  Overall success : {total_ok}/{len(results)}")
    print(f"  Valid for paper : {len(valid)}/{len(results)}")
    print(f"\n  Saved → {json_path}")
    print(f"          {csv_path}")
    print("\n  Next step: run generate_graphs.py")


if __name__ == "__main__":
    preload_all_sources()
    results = run_experiment()
    save_and_summarize(results)