RUN = poetry run
OBO = http://purl.obolibrary.org/obo
MAPPED_ONTS = envo po uberon obi foodon ncbitaxon fao mixs
#MAPPINGS = mappings/gold-to-envo.curated.sssom.tsv 

CURATED_MAPPING_FILES = $(patsubst %,mappings/gold-to-%.curated.sssom.tsv,$(MAPPED_ONTS))

all: gold.owl gold.obo gold_definitions.yaml gold_definitions_propagated.csv gold_definitions_propagated.yaml

test:
	$(RUN) pytest

## Ontology Build ##

CODE = gold_ontology/gold_transform.py
gold.ofn: tests/inputs/goldpaths.tsv $(CODE) config/gold-env-synonyms.tsv $(CURATED_MAPPING_FILES)
	$(RUN) python $(CODE) -s config/gold-env-synonyms.tsv $(patsubst %,-m %,$(CURATED_MAPPING_FILES))  $< -o $@
gold-no-mappings.ofn: tests/inputs/goldpaths.tsv $(CODE) config/gold-env-synonyms.tsv 
	$(RUN) python $(CODE) -s config/gold-env-synonyms.tsv   $< -o $@
.PRECIOUS: gold.ofn

gold.owl: gold.ofn
	robot relax -i $< reason -r elk -o $@
.PRECIOUS: gold.owl

gold.json: gold.owl
	robot convert -i $< -o $@

gold.obo: gold.owl
	robot convert -i $< -o $@.tmp.obo --check false && perl -npe 's@property_value: skos:\S+Match@xref:@;s@idspace: oboInOwl.*\n@@' $@.tmp.obo > $@

# makes OWL as side-effect
gold.db: gold.owl
	runoak -i sqlite:$< statistics

data/gold-biosample-subset.db: data/gold-biosample-subset.tsv
	sqlite3 $@ -cmd ".mode tabs" ".import $< biosample"


## Mappings ##


gold_definitions.yaml: gold.obo
	$(RUN) create-template simpleobo:$< -t gold_definitions.csv > $@.tmp && mv $@.tmp $@

gold_definitions_propagated.yaml: gold.obo
	$(RUN) create-template simpleobo:$< -t gold_definitions.csv --propagate > $@.tmp && mv $@.tmp $@

gold_definitions_propagated.csv: gold.obo
	$(RUN) create-template simpleobo:$< -t gold_definitions.csv --propagate -f csv > $@.tmp && mv $@.tmp $@

all_mappings: $(patsubst %,mappings/gold-to-%.sssom.tsv,$(MAPPED_ONTS))


LEX_ARGS =  -R conf/lexmatch-config.yaml --exclude-mapped
DB = ../semantic-sql/db
mappings/gold-to-envo.sssom.tsv: gold.obo
	runoak --stacktrace -i simpleobo:$< -a sqlite:obo:envo lexmatch $(LEX_ARGS) i^GOLD @ i^ENVO: > $@.tmp && mv $@.tmp $@

mappings/gold-to-po.sssom.tsv: gold.obo
	runoak -i simpleobo:$< -a sqlite:obo:po lexmatch $(LEX_ARGS) i^GOLD @ i^PO: > $@.tmp && mv $@.tmp $@

mappings/gold-to-uberon.sssom.tsv: gold.obo
	runoak -i simpleobo:$< -a sqlite:obo:uberon lexmatch $(LEX_ARGS) i^GOLD @ i^UBERON: > $@.tmp && mv $@.tmp $@

mappings/gold-to-fao.sssom.tsv: gold.obo
	runoak -i simpleobo:$< -a sqlite:obo:fao lexmatch $(LEX_ARGS) i^GOLD @ i^FAO: > $@.tmp && mv $@.tmp $@

mappings/gold-to-ncbitaxon.sssom.tsv: gold.obo
	runoak -i simpleobo:$< -a sqlite:obo:taxslim lexmatch $(LEX_ARGS) i^GOLD @ i^NCBITaxon: > $@.tmp && mv $@.tmp $@

mappings/gold-to-obi.sssom.tsv: gold.obo
	runoak -i simpleobo:$< -a sqlite:obo:obi lexmatch $(LEX_ARGS) i^GOLD @ i^OBI: > $@.tmp && mv $@.tmp $@

mappings/gold-to-foodon.sssom.tsv: gold.obo
	runoak -i simpleobo:$< -a sqlite:obo:foodon lexmatch $(LEX_ARGS) i^GOLD @ i^FOODON: > $@.tmp && mv $@.tmp $@

mappings/gold-to-mixs.sssom.tsv: gold.obo
	runoak -i simpleobo:$< -a simpleobo:data/mixs-extensions.obo lexmatch $(LEX_ARGS) i^GOLD @ i^MIXS: > $@.tmp && mv $@.tmp $@

#mappings/gold-to-mixs-packages.sssom.tsv:
#	runoak -i $(DB)/goldterms.db -a sqlite:obo:envo lexmatch $(LEX_ARGS) i^ENVO: @ i^GOLD > $@.tmp && mv $@.tmp $@

gold_definitions.owl: gold_definitions.csv
	robot template -t gold_definitions.csv -o $@ -p "GOLDTERMS: https://w3id.org/gold.path/" -p "MIXS: $(OBO)/MIXS_"

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
