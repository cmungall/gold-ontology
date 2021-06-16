OBO = http://purl.obolibrary.org/obo
MAPPINGS = mappings/filtered-gold-to-obo.sssom.tsv 

all: gold.owl mappings/gold-to-obo.sssom.tsv mappings/nomatch-gold-to-obo.sssom.tsv $(MAPPINGS)

test:
	pipenv run pytest

CODE = gold_ontology/gold_transform.py
gold.ofn: tests/inputs/goldpaths.tsv $(CODE) config/gold-env-synonyms.tsv $(MAPPINGS)
	pipenv run python $(CODE) -s config/gold-env-synonyms.tsv -m $(MAPPINGS)  $< -o $@

gold.owl: gold.ofn
	robot convert -i $< -o $@

data/gold-biosample-subset.db: data/gold-biosample-subset.tsv
	sqlite3 $@ -cmd ".mode tabs" ".import $< biosample"

.PHONY: requirements-file
requirements-file:
# calls pipenv to generate the requirements.txt and requirements-dev.txt files
	pipenv run pipenv_to_requirements

ONTS = envo uberon po obi pato foodon ncbitaxon
ONTS_OWL = $(patsubst %, downloads/%.owl, $(ONTS))
downloads/%.owl:
	robot merge -I $(OBO)/$*.owl -o $@
downloads/obi.owl:
	robot merge -I $(OBO)/obi/obi-base.owl -o $@
downloads/ncbitaxon.owl:
	curl -L -s $(OBO)/ncbitaxon/subsets/taxslim.obo > $@

# we need to filter axioms e.g 
downloads/obo.owl: $(ONTS_OWL)
	robot merge $(patsubst %, -i downloads/%.owl, $(ONTS)) remove --axioms 'disjoint ObjectPropertyDomain'  -o $@

mappings/filtered-gold-to-%.sssom.tsv: mappings/gold-to-%.sssom.tsv
	python -m sssom.cli dosql -q "SELECT m1.* FROM df1 AS m1 WHERE NOT EXISTS (SELECT * FROM df1 AS m2 WHERE m1.subject_id=m2.subject_id AND m2.confidence > m1.confidence)" $< > $@

mappings/gold-to-%.sssom.tsv: mappings/auto-gold-to-%.sssom.tsv
	python -m sssom.cli dedupe -i $< > $@

mappings/auto-gold-to-%.sssom.tsv: downloads/%.owl  config/prefixes.ttl config/envo_weights.pro
	rdfmatch -p gold.vocab -i $< -i gold.owl -i config/prefixes.ttl -w config/envo_weights.pro match > $@.tmp && mv $@.tmp $@

mappings/nomatch-gold-to-%.sssom.tsv: downloads/%.owl  config/prefixes.ttl config/envo_weights.pro
	rdfmatch -p gold.vocab -i $< -i gold.owl -i config/prefixes.ttl -w config/envo_weights.pro nomatch > $@.tmp && mv $@.tmp $@

mappings/gold-to-%.ptable.tsv: mappings/gold-to-%.sssom.tsv
	python -m sssom.cli ptable -i $< > $@

boomer: mappings/gold-to-obo.ptable.tsv
	boomer -r 5 -w 5 -p config/prefixes.yaml -t $< -a downloads/obo.owl -o $@
