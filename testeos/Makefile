.PHONY: help test test-simple test-ragas view results clean install-deps api

# Default target
help:
	@echo "════════════════════════════════════════════════════════════════"
	@echo "🧪 RAGAS Test Suite - Vodafone RAG API"
	@echo "════════════════════════════════════════════════════════════════"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "  make test              - Run simple test (recommended)"
	@echo "  make test-simple       - Run simple test with detailed output"
	@echo "  make test-ragas        - Run full RAGAS evaluation"
	@echo "  make view              - View latest test results"
	@echo "  make view-detailed     - View results with detailed comparison"
	@echo "  make view-interactive  - Interactive result viewer"
	@echo "  make results           - List all saved results"
	@echo "  make install-deps      - Install RAGAS dependencies"
	@echo "  make api               - Start the API server"
	@echo "  make clean             - Remove results directory"
	@echo "  make help              - Show this help message"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make api              # In one terminal"
	@echo "  2. make test             # In another terminal"
	@echo ""

# Run simple test
test: test-simple

test-simple:
	@echo "📞 Running simple test..."
	@python simple_test.py
	@echo ""
	@make view

# Run RAGAS test
test-ragas:
	@echo "⏳ Running RAGAS evaluation (may take several minutes)..."
	@python run_ragas_test.py

# View results
view:
	@python view_results.py

view-detailed:
	@python view_results.py --detailed

view-interactive:
	@python view_results.py --interactive

# List all results
results:
	@echo "📂 Available results:"
	@ls -lh results/ 2>/dev/null || echo "  No results found yet"

# Install dependencies
install-deps:
	@echo "📦 Installing RAGAS dependencies..."
	@pip install -r requirements_ragas.txt
	@echo "✅ Dependencies installed"

# Start API
api:
	@echo "🚀 Starting API server..."
	@cd .. && python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Clean
clean:
	@echo "🧹 Cleaning up results..."
	@rm -rf results/*
	@echo "✅ Cleaned"

# Run all (test + view)
all: test view
