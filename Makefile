OBO = http://purl.obolibrary.org/obo
MAPPED_ONTS = envo po uberon obi
#MAPPINGS = mappings/gold-to-envo.curated.sssom.tsv 

CURATED_MAPPING_FILES = $(patsubst %,mappings/gold-to-%.curated.sssom.tsv,$(MAPPED_ONTS))

all: gold.owl mappings/gold-to-obo.sssom.tsv mappings/nomatch-gold-to-obo.sssom.tsv $(MAPPINGS)

test:
	pipenv run pytest

CODE = gold_ontology/gold_transform.py
gold.ofn: tests/inputs/goldpaths.tsv $(CODE) config/gold-env-synonyms.tsv $(CURATED_MAPPING_FILES)
	pipenv run python $(CODE) -s config/gold-env-synonyms.tsv $(patsubst %,-m %,$(CURATED_MAPPING_FILES))  $< -o $@
gold-no-mappings.ofn: tests/inputs/goldpaths.tsv $(CODE) config/gold-env-synonyms.tsv 
	pipenv run python $(CODE) -s config/gold-env-synonyms.tsv   $< -o $@
.PRECIOUS: gold.ofn

gold.owl: gold.ofn
	robot relax -i $< reason -r elk -o $@
.PRECIOUS: gold.owl

gold.json: gold.owl
	robot convert -i $< -o $@

# makes OWL as side-effect
gold.db: gold.owl
	runoak -i sqlite:$< statistics

data/gold-biosample-subset.db: data/gold-biosample-subset.tsv
	sqlite3 $@ -cmd ".mode tabs" ".import $< biosample"

.PHONY: requirements-file
requirements-file:
# calls pipenv to generate the requirements.txt and requirements-dev.txt files
	pipenv run pipenv_to_requirements

DB = ../semantic-sql/db
mappings/gold-to-envo.sssom.tsv:
	runoak -i $(DB)/goldterms.db -a sqlite:obo:envo lexmatch -R conf/lexmatch-config.yaml i^GOLD @ i^ENVO: > $@.tmp && mv $@.tmp $@

mappings/gold-to-po.sssom.tsv:
	runoak -i $(DB)/goldterms.db -a sqlite:obo:po lexmatch -R conf/lexmatch-config.yaml i^GOLD @ i^PO: > $@.tmp && mv $@.tmp $@

mappings/gold-to-uberon.sssom.tsv:
	runoak -i $(DB)/goldterms.db -a sqlite:obo:uberon lexmatch -R conf/lexmatch-config.yaml i^GOLD @ i^UBERON: > $@.tmp && mv $@.tmp $@

mappings/gold-to-ncbitaxon.sssom.tsv:
	runoak -i $(DB)/goldterms.db -a sqlite:obo:ncbitaxon lexmatch -R conf/lexmatch-config.yaml i^GOLD @ i^NCBITaxon: > $@.tmp && mv $@.tmp $@

mappings/gold-to-obi.sssom.tsv:
	runoak -i $(DB)/goldterms.db -a sqlite:obo:obi lexmatch -R conf/lexmatch-config.yaml i^GOLD @ i^OBI: > $@.tmp && mv $@.tmp $@

#mappings/gold-to-mixs-packages.sssom.tsv:
#	runoak -i $(DB)/goldterms.db -a sqlite:obo:envo lexmatch -R conf/lexmatch-config.yaml i^ENVO: @ i^GOLD > $@.tmp && mv $@.tmp $@
