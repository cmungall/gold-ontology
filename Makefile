all: gold.owl

CODE = gold_ontology/gold_transform.py
gold.ofn: tests/inputs/goldpaths.tsv $(CODE)
	pipenv run python $(CODE)  $< -o $@

%.owl: %.ofn
	robot convert -i $< -o $@

data/gold-biosample-subset.db: data/gold-biosample-subset.tsv
	sqlite3 $@ -cmd ".mode tabs" ".import $< biosample"