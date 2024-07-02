# Translation of GOLD paths to OWL and mapping to ENVO

This repo contains

1. A rendering of the GOLD ecosystem classification as OWL
2. Mappings of GOLD paths to ENVO expressions

## Top level

The top level consists of the 3 gold path roots (environmental, host, engineered), plus the AtomicElement grouping for capturing "atomic" gold words/terms:

|id|label|
|---|---|
|<https://w3id.org/gold.path/3964>|Environmental|
|<https://w3id.org/gold.path/4086>|Host-associated|
|<https://w3id.org/gold.path/4292>|Engineered|
|<https://w3id.org/gold.path/AtomicElement>|None|


![image](https://user-images.githubusercontent.com/50745/121285301-fe2bdd00-c892-11eb-92f6-5cf8c76bc284.png)

## Gold path elements

Each gold path class is organized in a tree hierarchy using SubClassOf axioms, and are given a logical
definition equivalent to the path; e..

```owl
'Environmental > Terrestrial > Geologic > Mine pit pond > Asbestos'
  SubClassOf 'Environmental > Terrestrial > Geologic > Mine pit pond'
  EquivalentTo
    (ECOSYSTEM some Terrestrial) and (ECOSYSTEM-CATEGORY some Geologic) and (ECOSYSTEM-PATH-ID some Environmental) and (ECOSYSTEM-SUBTYPE some Asbestos) and (ECOSYSTEM-TYPE some 'Mine pit pond')
```

![image](https://user-images.githubusercontent.com/50745/121285351-1ac81500-c893-11eb-8ad6-d441765262ed.png)

We use 5 different properties for the level-based definitions:

![image](https://user-images.githubusercontent.com/50745/121285430-3e8b5b00-c893-11eb-8466-5bfc128c7649.png)

## Atomic Elements

Each individual token/term used in a path is classified under AtomicElement; in Protege you can see all usages
of that in paths

![image](https://user-images.githubusercontent.com/50745/121285635-94600300-c893-11eb-8287-ba23a7bcfa8b.png)

## DL queries

![image](https://user-images.githubusercontent.com/50745/121285883-ec970500-c893-11eb-88d1-5a8d83fe9897.png)

![image](https://user-images.githubusercontent.com/50745/121285491-55ca4880-c893-11eb-9465-ddbd64120855.png)

![Uploading image.png…]()

# Mapping

Mapping GOLD to ENVO is an example of *Complex Mapping*. We don't have simple 1-1 relationships representable in SSSOM.

Instead we have mappings between GOLD paths and ENVO
*expressions*. These can be represented in YAML or TSV, and translated
to OWL expressions.

Engineered environment example:

```
- id: GOLDTERMS:5473
  label: Engineered > Bioreactor > Aerobic > Biofilm
  parent: GOLDTERMS:4536
  level: 4
  vocab_differentia: GOLDVOCAB:Biofilm
  mixs_extension:
    id: MIXS:MiscellaneousNaturalOrArtificialEnvironment
    label: MIXS:MiscellaneousNaturalOrArtificialEnvironment
  env_broad:
    id: ENVO:01000313
    label: anthropogenic environment
  env_local:
    id: OBI:0001046
    label: bioreactor
  other:
    id: ENVO:00002034
    label: biofilm
```

Host-associated example:

```yaml
- id: GOLDTERMS:5148
  label: Host-associated > Amphibia > Excretory system > Kidney
  parent: GOLDTERMS:4085
  level: 4
  vocab_differentia: GOLDVOCAB:Kidney
  mixs_extension:
    id: MIXS:HostAssociated
    label: MIXS:HostAssociated
  host_taxon:
    id: NCBITaxon:8292
    label: Amphibia
  anatomical_site:
    id: UBERON:0002113
    label: kidney
```

Environmental:

```yaml
- id: GOLDTERMS:5413
  label: Environmental > Aquatic > Floodplain > Sediment
  parent: GOLDTERMS:Environmental-Aquatic-Floodplain
  level: 4
  vocab_differentia: GOLDVOCAB:Sediment
  mixs_extension:
    id: MIXS:Sediment
    label: MIXS:Sediment
  env_broad:
    id: ENVO:01000254
    label: environmental system
  env_local:
    id: ENVO:00000255
    label: flood plain
  env_medium:
    id: ENVO:00002007
    label: sediment
```


* [gold_definitions.yaml](gold_definitions.yaml) - base definitions
* [gold_definitions_propagated.yaml](gold_definitions_propagated.yaml) - base definitions with slots propagated down
* [gold_definitions.owl](gold_definitions.owl) - OWL

TODO: Document semi-automated process

## Individual terms to be added to ENVO

https://github.com/EnvironmentOntology/envo/labels/GOLD%2FEBI-MGNIFY
