all: gold.owl

CODE = gold_ontology/gold_transform.py
gold.ofn: tests/inputs/goldpaths.tsv $(CODE)
	pipenv run python $(CODE)  $< -o $@

%.owl: %.ofn
	robot convert -i $< -o $@
