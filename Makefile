gold.ofn: tests/inputs/goldpaths.tsv
	pipenv run python gold_ontology/gold_transform.py  $< -o $@

%.owl: %.ofn
	robot convert -i $< -o $@
