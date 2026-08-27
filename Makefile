.PHONY: setup lint format typecheck test data sim train backtest serve loadtest smoke report clean

setup:
	uv sync --all-extras

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src

test:
	uv run pytest

data:
	uv run ridepulse data build --months 2023-01..2023-02 --root data

sim:
	@echo "make sim: not implemented yet (lands in Stage 3)"; exit 1

train:
	@echo "make train: not implemented yet (lands in Stage 4)"; exit 1

backtest:
	@echo "make backtest: not implemented yet (lands in Stage 4)"; exit 1

serve:
	@echo "make serve: not implemented yet (lands in Stage 5)"; exit 1

loadtest:
	@echo "make loadtest: not implemented yet (lands in Stage 5)"; exit 1

smoke:
	@echo "make smoke: not implemented yet (lands in Stage 6)"; exit 1

report:
	@echo "make report: not implemented yet"; exit 1

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
