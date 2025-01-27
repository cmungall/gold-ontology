RUN = poetry run
OBO = http://purl.obolibrary.org/obo
MAPPED_ONTS = envo po uberon obi foodon ncbitaxon fao mixs pato chebi
#MAPPINGS = mappings/gold-to-envo.curated.sssom.tsv 
CODE = gold_ontology/gold_transform.py

CURATED_MAPPING_FILES = $(patsubst %,mappings/gold-to-%.curated.sssom.tsv,$(MAPPED_ONTS))

all: gold.owl gold.obo gold_definitions.yaml gold_definitions_propagated.csv gold_definitions_propagated.yaml gold_definitions_merged.owl

test: pytest doctest

pytest:
	$(RUN) pytest

DOCTEST_DIR = gold_ontology
doctest:
	find $(DOCTEST_DIR) -type f \( -name "*.rst" -o -name "*.md" -o -name "*.py" \) -print0 | xargs -0 $(RUN) python -m doctest --option ELLIPSIS --option NORMALIZE_WHITESPACE

rebuild:
	rm gold-core.obo
	touch tests/inputs/goldpaths.tsv
	make all

## Ontology Build ##
# TODO: fix circularity in dependencies


# Main product:
#
# 1. gold hierarchy
# 2. mappings as annotations and pointers to dangling ENVO classes
#
# note this contains no imports, to avoid cluttering ontology displays
# 
# 1 is made from gold_transform.py (via gold_pre)
# 2 is made from create-template
gold.owl: gold_pre.ofn gold_mappings_as_annotations.owl
	robot merge -i $< -i gold_mappings_as_annotations.owl relax reason -r elk -o $@
.PRECIOUS: gold.owl

gold_pre.ofn: tests/inputs/goldpaths.tsv $(CODE) config/gold-env-synonyms.tsv $(CURATED_MAPPING_FILES)
	$(RUN) python $(CODE) -s config/gold-env-synonyms.tsv $(patsubst %,-m %,$(CURATED_MAPPING_FILES))  $< -o $@.tmp && mv $@.tmp $@
gold-no-mappings.ofn: tests/inputs/goldpaths.tsv $(CODE) config/gold-env-synonyms.tsv 
	$(RUN) python $(CODE) -s config/gold-env-synonyms.tsv   $< -o $@
.PRECIOUS: gold_pre.ofn


gold.json: gold.owl
	robot convert -i $< -o $@

gold.obo: gold.owl
	robot convert -i $< -o $@.tmp.obo --check false && perl -npe 's@property_value: skos:\S+Match@xref:@;s@idspace: oboInOwl.*\n@@' $@.tmp.obo > $@

# makes OWL as side-effect
gold.db: gold.owl
	runoak -i sqlite:$< statistics

data/gold-biosample-subset.db: data/gold-biosample-subset.tsv
	sqlite3 $@ -cmd ".mode tabs" ".import $< biosample"

# TODO:
gold-core.obo:
	cp gold.obo gold-core.obo


## Derived Mappings and ROBOT templates ##
#
# Assumes that mappings are present as xrefs in gold.obo
#
# These are used to provide derived COMPLEX mappings;
# e.g. GOLD:A>B>C <==> foo=A,bar=B,...

gold_definitions.yaml gold_definitions.csv: gold-core.obo
	$(RUN) create-template simpleobo:$< -t gold_definitions.csv  > $@.tmp && mv $@.tmp $@

gold_definitions_propagated.yaml: gold-core.obo
	$(RUN) create-template simpleobo:$<  --propagate > $@.tmp && mv $@.tmp $@

gold_definitions_propagated.csv: gold-core.obo
	$(RUN) create-template simpleobo:$<  --propagate -f csv > $@.tmp && mv $@.tmp $@

gold_mappings_as_annotations.csv: gold-core.obo
	$(RUN) create-template simpleobo:$<  --propagate -f simple-robot > $@.tmp && mv $@.tmp $@

#gold_mappings_as_axioms.csv: gold_mappings_as_axioms.owl
#	perl -npe 's@

# use the robot template to create a simple ontology;
# this is a flat ontology with simple annotation assertions for each mapping
gold_mappings_as_annotations.owl: gold_mappings_as_annotations.csv
	robot template -t $< -o $@ -p "GOLDTERMS: https://w3id.org/gold.path/" -p "MIXS: https://w3id.org/mixs/"

# note that the CSV already has the ROBOT template
gold_definitions.owl: gold_definitions.csv
	robot template -t gold_definitions.csv -o $@ -p "GOLDTERMS: https://w3id.org/gold.path/" -p "MIXS: $(OBO)/MIXS_"


gold-full.owl: gold_definitions.owl
	robot merge -i $< -i

## Base Mappings ##


# Atomated mappings.
# Note that the curated versions of these have file pattern X.curated.csv;
# these get incorporated into gold.obo, and hence are excluded when we ask for *new* mappings
# (via --exclude-mapped)
all_mappings: $(patsubst %,mappings/gold-to-%.sssom.tsv,$(MAPPED_ONTS))


LEX_ARGS =  -R conf/lexmatch-config.yaml --exclude-mapped --add-pipeline-step WordOrderNormalization
DB = ../semantic-sql/db
mappings/gold-to-envo.sssom.tsv: gold-core.obo
	runoak --stacktrace -i simpleobo:$< -a sqlite:obo:envo lexmatch $(LEX_ARGS) i^GOLD @ i^ENVO: > $@.tmp && mv $@.tmp $@

mappings/gold-to-po.sssom.tsv: gold-core.obo
	runoak -i simpleobo:$< -a sqlite:obo:po lexmatch $(LEX_ARGS) i^GOLD @ i^PO: > $@.tmp && mv $@.tmp $@

mappings/gold-to-uberon.sssom.tsv: gold-core.obo
	runoak -i simpleobo:$< -a sqlite:obo:uberon lexmatch $(LEX_ARGS) i^GOLD @ i^UBERON: > $@.tmp && mv $@.tmp $@

mappings/gold-to-fao.sssom.tsv: gold-core.obo
	runoak -i simpleobo:$< -a sqlite:obo:fao lexmatch $(LEX_ARGS) i^GOLD @ i^FAO: > $@.tmp && mv $@.tmp $@

mappings/gold-to-ncbitaxon.sssom.tsv: gold-core.obo
	runoak -i simpleobo:$< -a sqlite:obo:taxslim lexmatch $(LEX_ARGS) i^GOLD @ i^NCBITaxon: > $@.tmp && mv $@.tmp $@

mappings/gold-to-obi.sssom.tsv: gold-core.obo
	runoak -i simpleobo:$< -a sqlite:obo:obi lexmatch $(LEX_ARGS) i^GOLD @ i^OBI: > $@.tmp && mv $@.tmp $@

mappings/gold-to-foodon.sssom.tsv: gold-core.obo
	runoak -i simpleobo:$< -a sqlite:obo:foodon lexmatch $(LEX_ARGS) i^GOLD @ i^FOODON: > $@.tmp && mv $@.tmp $@

mappings/gold-to-pato.sssom.tsv: gold-core.obo
	runoak -i simpleobo:$< -a sqlite:obo:pato lexmatch $(LEX_ARGS) i^GOLD @ i^PATO: > $@.tmp && mv $@.tmp $@

mappings/gold-to-chebi.sssom.tsv: gold-core.obo
	runoak -i simpleobo:$< -a sqlite:obo:chebi lexmatch $(LEX_ARGS) i^GOLD @ i^CHEBI: > $@.tmp && mv $@.tmp $@

mappings/gold-to-mixs.sssom.tsv: gold-core.obo
	runoak -i simpleobo:$< -a simpleobo:data/mixs-extensions.obo lexmatch $(LEX_ARGS) i^GOLD @ i^MIXS: > $@.tmp && mv $@.tmp $@

#mappings/gold-to-mixs-packages.sssom.tsv:
#	runoak -i $(DB)/goldterms.db -a sqlite:obo:envo lexmatch $(LEX_ARGS) i^ENVO: @ i^GOLD > $@.tmp && mv $@.tmp $@


all_mirror: $(patsubst %,mirror/%.owl,$(MAPPED_ONTS))
mirror/%.owl:
	curl -L -s $(OBO)/$*.owl > $@.tmp && mv $@.tmp $@

mirror/ncbitaxon.owl:
	curl -L -s $(OBO)/ncbitaxon/subsets/taxslim.obo > $@.tmp && mv $@.tmp $@

mirror/foodon.owl:
	robot remove -I $(OBO)/foodon.owl --base-iri FOODON  --axioms external -p false  -o $@

imports/seed.txt: gold_definitions.owl
	robot query -f tsv -i $< --query sparql/seed.rq $@.tmp && perl -npe 's@"@@g' $@.tmp > $@

imports/%_import.owl: mirror/%.owl imports/seed.txt
	robot extract -m BOT -i $< --term-file imports/seed.txt -o $@

gold_definitions_merged.owl: gold_definitions.owl $(patsubst %,imports/%_import.owl,$(MAPPED_ONTS))
#	robot merge $(patsubst %,--input %, $^) relax -o $@
	robot merge $(patsubst %,--input %, $^) reason -r elk relax -o $@



downloads/mgnify-biomes.tsv:
	curl -L -s "https://www.ebi.ac.uk/metagenomics/api/v1/biomes?ordering=&format=csv" > $@.tmp && csvformat -T $@.tmp > $@
