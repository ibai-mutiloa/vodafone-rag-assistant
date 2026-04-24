"""
Simple Test Runner - Prueba básica sin dependencias complejas
Ejecuta las 10 preguntas contra la API y genera un reporte CSV
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

import requests

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5001")
TEST_DATA_PATH = Path(__file__).parent / "test_data.csv"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


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


def run_simple_test():
    """Run simple test suite."""
    print("=" * 100)
    print("Simple Test Suite - Vodafone RAG API")
    print("=" * 100)
    
    # Load test data
    print(f"\n📥 Loading test data from {TEST_DATA_PATH}...")
    test_cases = load_test_data(str(TEST_DATA_PATH))
    print(f"✅ Loaded {len(test_cases)} test cases\n")
    
    # Prepare results storage
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Call API for each test case
    print("📞 Calling API for each test case...\n")
    for i, test_case in enumerate(test_cases, start=1):
        question = test_case["question"]
        print(f"[{i:2d}/10] Processing: {question[:70]}...")
        
        api_response = call_api(question)
        
        result = {
            "id": test_case["id"],
            "question": question,
            "ground_truth": test_case["ground_truth"],
            "api_answer": api_response.get("answer", ""),
            "chunks_count": len(api_response.get("chunks", [])),
            "error": api_response.get("error", ""),
        }
        results.append(result)
    
    # Save detailed JSON results
    json_file = RESULTS_DIR / f"test_results_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 JSON results saved to: {json_file}")
    
    # Save CSV results
    csv_file = RESULTS_DIR / f"test_results_{timestamp}.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "question", "ground_truth", "api_answer", "chunks_count", "error"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"📊 CSV results saved to: {csv_file}")
    
    # Generate summary report
    print("\n" + "=" * 100)
    print("Test Summary Report")
    print("=" * 100)
    
    successful = len([r for r in results if not r["error"]])
    failed = len([r for r in results if r["error"]])
    avg_chunks = sum(r["chunks_count"] for r in results) / len(results) if results else 0
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📚 Average chunks retrieved: {avg_chunks:.1f}")
    
    print("\n" + "-" * 100)
    print("Detailed Results:")
    print("-" * 100)
    
    for i, result in enumerate(results, start=1):
        print(f"\n[Test {i}] {result['question'][:80]}")
        print(f"  Ground Truth: {result['ground_truth'][:100]}...")
        print(f"  API Answer:   {result['api_answer'][:100]}...")
        print(f"  Chunks:       {result['chunks_count']}")
        if result["error"]:
            print(f"  ❌ Error: {result['error']}")
    
    print("\n" + "=" * 100)
    print("✅ Test execution completed!")
    print("=" * 100)


if __name__ == "__main__":
    try:
        run_simple_test()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
