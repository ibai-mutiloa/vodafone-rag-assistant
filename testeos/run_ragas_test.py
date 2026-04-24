"""
RAGAS Test Suite para Vodafone RAG API
Evalúa la calidad del sistema RAG usando métricas de RAGAS
"""

import asyncio
import csv
import json
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from ragas import EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    AnswerRelevancy,
    Faithfulness,
    ContextPrecision,
    ContextRecall,
)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5001")
TEST_DATA_PATH = Path(__file__).parent / "test_data.csv"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Initialize metrics
metrics = [
    AnswerRelevancy(),
    Faithfulness(),
    ContextPrecision(),
    ContextRecall(),
]


def load_test_data(csv_path: str) -> list[dict]:
    """Load test data from CSV file."""
    test_cases = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append({
                "id": int(row["id"]),
                "question": row["question"],
                "ground_truth": row["ground_truth"],
            })
    return test_cases


def call_api(question: str, username: str = "mcorbella") -> dict:
    """Call the Vodafone RAG API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/ask",
            json={
                "question": question,
                "username": username,
                "response_language": "es",
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        return {
            "question": question,
            "answer": "",
            "chunks": [],
            "error": str(e),
        }


def prepare_evaluation_samples(test_cases: list[dict], api_responses: list[dict]) -> list[SingleTurnSample]:
    """Prepare samples for RAGAS evaluation."""
    samples = []
    for test_case, api_response in zip(test_cases, api_responses):
        context = "\n".join(api_response.get("chunks", []))
        
        sample = SingleTurnSample(
            user_input=test_case["question"],
            response=api_response.get("answer", ""),
            reference=test_case["ground_truth"],
            retrieved_contexts=[context] if context else [],
        )
        samples.append(sample)
    
    return samples


async def evaluate_samples(samples: list[SingleTurnSample]) -> dict:
    """Evaluate samples using RAGAS metrics."""
    dataset = EvaluationDataset(samples=samples)
    
    results = await asyncio.gather(
        *[metric.ascore(dataset) for metric in metrics]
    )
    
    metric_scores = {metric.name: score for metric, score in zip(metrics, results)}
    return metric_scores


def run_test_suite():
    """Run the complete RAGAS test suite."""
    print("=" * 80)
    print("RAGAS Test Suite - Vodafone RAG API")
    print("=" * 80)
    
    # Load test data
    print(f"\n📥 Loading test data from {TEST_DATA_PATH}...")
    test_cases = load_test_data(str(TEST_DATA_PATH))
    print(f"✅ Loaded {len(test_cases)} test cases")
    
    # Call API for each test case
    print("\n📞 Calling API for each test case...")
    api_responses = []
    for i, test_case in enumerate(test_cases, start=1):
        print(f"  [{i}/{len(test_cases)}] Processing: {test_case['question'][:60]}...")
        response = call_api(test_case["question"])
        api_responses.append(response)
    
    # Save raw API responses
    raw_results_file = RESULTS_DIR / "raw_api_responses.json"
    with open(raw_results_file, "w", encoding="utf-8") as f:
        json.dump(api_responses, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Raw API responses saved to {raw_results_file}")
    
    # Prepare samples for evaluation
    print("\n🔄 Preparing samples for RAGAS evaluation...")
    samples = prepare_evaluation_samples(test_cases, api_responses)
    
    # Run RAGAS evaluation
    print("\n⏳ Running RAGAS evaluation (this may take a few minutes)...")
    metric_scores = asyncio.run(evaluate_samples(samples))
    
    # Generate detailed results
    print("\n" + "=" * 80)
    print("RAGAS Evaluation Results")
    print("=" * 80)
    
    results_summary = {
        "total_tests": len(test_cases),
        "timestamp": pd.Timestamp.now().isoformat(),
        "metrics": metric_scores,
        "detailed_results": [],
    }
    
    for i, (test_case, api_response, sample) in enumerate(zip(test_cases, api_responses, samples), start=1):
        result = {
            "id": test_case["id"],
            "question": test_case["question"],
            "ground_truth": test_case["ground_truth"],
            "api_answer": api_response.get("answer", ""),
            "retrieved_chunks": api_response.get("chunks", []),
            "chunks_count": len(api_response.get("chunks", [])),
        }
        results_summary["detailed_results"].append(result)
    
    # Save results
    results_file = RESULTS_DIR / "evaluation_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\nMetrics Summary:")
    print("-" * 80)
    for metric_name, score in metric_scores.items():
        print(f"  {metric_name}: {score:.4f}")
    
    print("\n" + "=" * 80)
    print(f"📊 Full results saved to:")
    print(f"   - {raw_results_file}")
    print(f"   - {results_file}")
    print("=" * 80)
    
    return results_summary


if __name__ == "__main__":
    try:
        results = run_test_suite()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
