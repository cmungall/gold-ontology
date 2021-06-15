OBO = http://purl.obolibrary.org/obo

all: gold.owl mappings/gold-to-obo.sssom.tsv mappings/nomatch-gold-to-obo.sssom.tsv

test:
	pipenv run pytest

CODE = gold_ontology/gold_transform.py
gold.ofn: tests/inputs/goldpaths.tsv $(CODE) config/gold-env-synonyms.tsv
	pipenv run python $(CODE) -s config/gold-env-synonyms.tsv  $< -o $@

%.owl: %.ofn
	robot convert -i $< -o $@

data/gold-biosample-subset.db: data/gold-biosample-subset.tsv
	sqlite3 $@ -cmd ".mode tabs" ".import $< biosample"

ONTS = envo uberon po obi pato foodon ncbitaxon
ONTS_OWL = $(patsubst %, downloads/%.owl, $(ONTS))
downloads/%.owl:
	robot merge -I $(OBO)/$*.owl -o $@
downloads/ncbitaxon.owl:
	curl -L -s $(OBO)/ncbitaxon/subsets/taxslim.obo

downloads/obo.owl: $(ONTS_OWL)
	robot merge $(patsubst %, -i downloads/%.owl, $(ONTS)) -o $@


mappings/gold-to-%.sssom.tsv: downloads/%.owl gold.owl config/prefixes.ttl config/envo_weights.pro
	rdfmatch -p gold.vocab -i $< -i gold.owl -i config/prefixes.ttl -w config/envo_weights.pro match > $@.tmp && mv $@.tmp $@

mappings/nomatch-gold-to-%.sssom.tsv: downloads/%.owl gold.owl config/prefixes.ttl config/envo_weights.pro
	rdfmatch -p gold.vocab -i $< -i gold.owl -i config/prefixes.ttl -w config/envo_weights.pro nomatch > $@.tmp && mv $@.tmp $@
