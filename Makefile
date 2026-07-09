.PHONY: test eval feature

test:
	pytest -q

eval:
	python -m eval.run_eval

feature:
	python scripts/new_feature.py $(name)
