"""
Visualization and Analysis Tool for RAGAS Test Results
Permite visualizar y analizar los resultados de los tests de manera amigable
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def load_latest_results(results_dir: Path):
    """Load the latest test results."""
    json_files = sorted(results_dir.glob("test_results_*.json"), reverse=True)
    
    if not json_files:
        print("❌ No test results found in results/")
        return None
    
    latest = json_files[0]
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)


def print_comparison(result: dict):
    """Print side-by-side comparison of ground truth vs API answer."""
    print("\n" + "=" * 150)
    print(f"Test #{result['id']}: {result['question']}")
    print("=" * 150)
    
    print("\n📎 GROUND TRUTH (Expected):")
    print("-" * 150)
    print(result['ground_truth'])
    
    print("\n🤖 API ANSWER (Generated):")
    print("-" * 150)
    print(result['api_answer'] if result['api_answer'] else "[Sin respuesta]")
    
    print("\n📊 METRICS:")
    print(f"   • Chunks Retrieved: {result['chunks_count']}")
    if result['error']:
        print(f"   • ❌ Error: {result['error']}")
    else:
        print(f"   • ✅ Success")


def calculate_similarity_score(text1: str, text2: str) -> float:
    """Simple similarity check based on common words."""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def generate_summary_report(results: list[dict]):
    """Generate a summary report of all tests."""
    print("\n" + "=" * 150)
    print("📊 SUMMARY REPORT")
    print("=" * 150)
    
    total = len(results)
    successful = len([r for r in results if not r['error']])
    failed = total - successful
    avg_chunks = sum(r['chunks_count'] for r in results) / total if total > 0 else 0
    
    print(f"\n📈 Test Statistics:")
    print(f"   • Total Tests: {total}")
    print(f"   • ✅ Successful: {successful} ({100*successful/total:.1f}%)")
    print(f"   • ❌ Failed: {failed} ({100*failed/total:.1f}%)")
    print(f"   • 📚 Average Chunks Retrieved: {avg_chunks:.1f}")
    
    # Calculate similarity scores
    similarities = []
    for r in results:
        if r['api_answer'] and not r['error']:
            score = calculate_similarity_score(r['ground_truth'], r['api_answer'])
            similarities.append(score)
    
    if similarities:
        avg_similarity = sum(similarities) / len(similarities)
        print(f"   • 🎯 Average Similarity Score: {avg_similarity:.2%}")
        print(f"      (Based on word overlap between ground truth and API answer)")
    
    # Test-by-test quick view
    print(f"\n📋 Test-by-Test Overview:")
    print("-" * 150)
    print(f"{'#':<3} {'Status':<8} {'Question':<80} {'Chunks':<8} {'Similarity':<12}")
    print("-" * 150)
    
    for i, r in enumerate(results, start=1):
        status = "❌ ERROR" if r['error'] else "✅ OK"
        question = r['question'][:76] + "..." if len(r['question']) > 76 else r['question']
        
        similarity = ""
        if r['api_answer'] and not r['error']:
            score = calculate_similarity_score(r['ground_truth'], r['api_answer'])
            similarity = f"{score:.1%}"
        
        print(f"{i:<3} {status:<8} {question:<80} {r['chunks_count']:<8} {similarity:<12}")
    
    print("-" * 150)


def view_results(interactive: bool = False):
    """View test results."""
    results_dir = Path(__file__).parent / "results"
    
    if not results_dir.exists():
        print("❌ Results directory not found")
        return
    
    results = load_latest_results(results_dir)
    
    if not results:
        return
    
    # Show summary
    generate_summary_report(results)
    
    # Show detailed comparisons if requested
    if interactive:
        print("\n" + "=" * 150)
        print("📖 DETAILED RESULTS")
        print("=" * 150)
        
        for result in results:
            print_comparison(result)
            input("\nPress Enter to continue to next result...")


def main():
    """Main function."""
    results_dir = Path(__file__).parent / "results"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--detailed":
            view_results(interactive=False)
        elif sys.argv[1] == "--interactive":
            view_results(interactive=True)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("\nUsage:")
            print("  python view_results.py          # Show summary")
            print("  python view_results.py --detailed  # Show all detailed results")
            print("  python view_results.py --interactive  # Interactive mode")
    else:
        view_results(interactive=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✋ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
