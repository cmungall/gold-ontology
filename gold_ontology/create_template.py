import logging
import sys
from functools import lru_cache
from typing import Optional, Iterator, Dict, TextIO, List

import click
import yaml
from oaklib import get_adapter
from oaklib.datamodels.vocabulary import IS_A, OWL_CLASS
from oaklib.interfaces import MappingProviderInterface
from pydantic import BaseModel

from gold_ontology.gold_transform import parse_sssom

MATERIAL = "ENVO:00010483"
BIOME = "ENVO:00000428"
ECOSYSTEM = "ENVO:01001110"
ENVIRONMENTAL_SYSTEM = "ENVO:01000254"
ABP = "ENVO:01000813"
PRODUCT = "ENVO:00003074"
DEVICE = "OBI:0000968"

ROBOT_HEADER = {
    "id": "ID",
    "label": "LABEL",
    "level": "A oboInOwl:inSubset",
    "parent": "C %",
    # "vocab_differentia": "C %",
    "mixs_extension": "C RO:0001000 some %",  # derives from
    "env_broad": "C RO:0001025 some %",  # located in
    "env_local": "C RO:0002507 some %",  # determined by
    "env_medium": "C RO:0002219 some %",  # surrounded by
    "host_taxon": "C RO:0002162 some %",  # in taxon
    "anatomical_site": "C BFO:0000050 some %",  # part of
    "other": "C RO:0002321 some %",  # ecologically related to
    "interpretation": "CLASS_TYPE",
}

class OntologyClass(BaseModel):
    id: str
    label: str
    inferred: Optional[bool] = None


class GoldTerm(BaseModel):
    id: str
    label: str
    parent: Optional[str] = None
    level: int
    vocab_differentia: Optional[str] = None
    mixs_extension: Optional[OntologyClass] = None
    env_broad: Optional[OntologyClass] = None
    env_local: Optional[OntologyClass] = None
    env_medium: Optional[OntologyClass] = None
    host_taxon: Optional[OntologyClass] = None
    anatomical_site: Optional[OntologyClass] = None
    other: Optional[OntologyClass] = None
    curated: Optional[bool] = None


def write_robot_template(terms: Iterator[GoldTerm], file: TextIO=sys.stdout) -> None:
    """
    Convert a list of GoldTerms to a list of dictionaries suitable for a robot template

    >>> env1 = OntologyClass(id="ENVO:0000001", label="bar")
    >>> env2 = OntologyClass(id="ENVO:0000002", label="baz")
    >>> term1 = GoldTerm(id="GOLDTERMS:0001", label="foo", level=1, env_medium=env1)
    >>> term2 = GoldTerm(id="GOLDTERMS:0002", label="foo2", level=2, env_local=env2)
    >>> write_robot_template([term1, term2])
    id,label,level,vocab_differentia,mixs_extension,env_broad,env_local,env_medium,taxon,anatomical_site,other,interpretation
    ID,LABEL,A gold.level,C %,C RO:0001000 some %,C RO:0001025 some %,C RO:0002507 some %,C RO:0002219 some %,C RO:0002162 some %,C BFO:0000050 some %,C RO:0002321 some %,CLASS_TYPE
    GOLDTERMS:0001,foo,1,,,,,ENVO:0000001,,,,equivalent
    GOLDTERMS:0002,foo2,2,,,,ENVO:0000002,,,,,equivalent


    """
    import csv
    writer = csv.DictWriter(file, fieldnames=ROBOT_HEADER.keys())
    writer.writeheader()
    writer.writerows(as_robot_template(terms))

def as_robot_template(terms: Iterator[GoldTerm]) -> Iterator[Dict[str, str]]:
    """
    Convert a list of GoldTerms to a list of dictionaries suitable for a robot template


    :param terms:
    :return:
    """
    yield ROBOT_HEADER
    for term in terms:
        yield as_robot_template_row(term)

def as_robot_template_row(term: GoldTerm) -> Dict[str, str]:
    """
    Convert a GoldTerm to a dictionary suitable for a robot template row

    >>> env = OntologyClass(id="ENVO:0000001", label="bar")
    >>> term = GoldTerm(id="GOLDTERMS:0001", label="foo", level=1, env_medium=env)
    >>> as_robot_template_row(term)
    {'id': 'GOLDTERMS:0001', 'label': 'foo', 'level': '1', 'env_medium': 'ENVO:0000001', 'interpretation': 'equivalent'}

    >>> term.curated = False
    >>> as_robot_template_row(term)
    {'id': 'GOLDTERMS:0001', 'label': 'foo', 'level': '1', 'env_medium': 'ENVO:0000001', 'interpretation': 'subclass'}


    :param term:
    :return:
    """
    row = {
    }
    interp = "subclass" if term.curated is False else "equivalent"
    for slot in vars(term):
        if slot in row:
            continue
        obj = getattr(term, slot)
        if not obj:
            continue
        if isinstance(obj, OntologyClass):
            row[slot] = obj.id
        elif slot in ["curated", "vocab_differentia"]:
            continue
        else:
            row[slot] = str(obj)
    row["interpretation"] = interp
    return row

#@lru_cache
def get_adapter_for(obj_id: str) -> Optional[MappingProviderInterface]:
    prefix = obj_id.split(":")[0]
    if prefix.startswith("GOLD"):
        return None
    prefix = prefix.lower()
    adapter = get_adapter(f"sqlite:obo:{prefix}")
    return adapter


def create_template(gold: MappingProviderInterface) -> Iterator[GoldTerm]:
    """
    Create a ROBOT template from the gold ontology plus mappings.

    Based on rules/heuristics about the mapped terms, different slots
    are filled in.

    :param gold:
    :return:
    """
    entities = gold.entities(owl_type=OWL_CLASS)
    for term_id in entities:
        if not term_id.startswith("GOLDTERMS:"):
            continue
        ancs = list(gold.ancestors(term_id, [IS_A]))
        label = gold.label(term_id)
        if not label:
            raise AssertionError(f"No label for {term_id}")
        t = GoldTerm(id=term_id, label=label, level=len(ancs))
        rels = list(gold.relationships([term_id]))
        rels = [r[2] for r in rels if r[1] != IS_A]
        parents = gold.hierarchical_parents(term_id, isa_only=True)
        parent_rels = []
        if parents:
            if len(parents) > 1:
                raise AssertionError(f"term {term_id} has >1 parents {parents}")
            parent = parents[0]
            t.parent = parent
            parent_rels = [r[2] for r in gold.relationships([parent]) if r[1] != IS_A]
        rels_diff = list(set(rels).difference(set(parent_rels)))
        if len(rels_diff) != 1:
            raise AssertionError(f"Diff {term_id} rels={rels} + diff={rels_diff} = {parent_rels}")
        t.vocab_differentia = rels_diff[0]
        mappings = list(gold.sssom_mappings([term_id, t.vocab_differentia]))
        n = 0
        for m in mappings:
            obj = m.object_id
            if obj.startswith("MIXS"):
                obj_label = obj.replace("MIXS:", "MIXS:")
            else:
                obj_adapter = get_adapter_for(obj)
                if not obj_adapter:
                    logging.warning(f"No adapter for {obj} for {term_id}")
                    continue
                obj_label = obj_adapter.label(obj)
                if not obj_label:
                    raise ValueError(f"No label for {obj}")
            ext_obj = OntologyClass(id=obj, label=obj_label)
            if obj.startswith("UBERON:") or obj.startswith("PO:"):
                slot = "anatomical_site"
            elif obj.startswith("FOODON:"):
                if "Host-associated" in label:
                    # FOODON is also used for grouping taxa
                    slot = "host_taxon"
                else:
                    slot = "env_medium"
            elif obj.startswith("MIXS:"):
                slot = "mixs_extension"
            elif obj.startswith("NCBITaxon:"):
                slot = "host_taxon"
            elif obj.startswith("ENVO:") or obj.startswith("OBI:"):
                ancs = list(obj_adapter.ancestors(obj, predicates=[IS_A]))
                if MATERIAL in ancs:
                    slot = "env_medium"
                elif ABP in ancs:
                    slot = "env_local"
                elif BIOME in ancs:
                    slot = "env_broad"
                elif DEVICE in ancs:
                    slot = "env_local"
                elif ECOSYSTEM in ancs:
                    # TODO: check
                    slot = "env_broad"
                elif ENVIRONMENTAL_SYSTEM in ancs:
                    # TODO: check
                    slot = "env_broad"
                else:
                    slot = "other"
            else:
                slot = "other"
            n += 1
            setattr(t, slot, ext_obj)
        if n == 0 and t.parent != "GOLDVOCAB:Unclassified":
            t.curated = False
        yield t


def propagate_down(terms: List[GoldTerm]) -> List[GoldTerm]:
    """
    Propagate relationships down the hierarchy

    :param terms:
    :return:
    """
    # sort by label
    terms = sorted(terms, key=lambda x: x.label)
    term_dict = {}
    for term in terms:
        term_dict[term.id] = term
        parent = term.parent
        if parent not in term_dict:
            if parent is not None:
                raise ValueError(f"Parent {parent} not found for {term.id}")
            continue
        parent_term = term_dict[parent]
        for slot in vars(parent_term):
            parent_val = getattr(parent_term, slot)
            if not isinstance(parent_val, OntologyClass):
                continue
            if getattr(term, slot):
                # TODO: consider checking redundancy
                continue
            logging.warning(f"Propagating {slot} = {parent_val} from {parent_term.id} to {term.id}")
            setattr(term, slot, parent_val)
        if parent_term.curated is False:
            term.curated = False
    return terms


def write_csv(terms: List[GoldTerm]) -> None:
    """
    Write a list of GoldTerms to CSV

    :param terms:
    :return:
    """
    import csv

    rows = []
    cols = []
    for term in terms:
        row = {}
        for slot in vars(term):
            obj = getattr(term, slot)
            if obj is None:
                obj = ""
            if isinstance(obj, OntologyClass):
                row[f"{slot}_id"] = obj.id
                row[f"{slot}_label"] = obj.label
                slots = [f"{slot}_id", f"{slot}_label"]
            else:
                row[slot] = str(obj)
                slots = [slot]
            for slot in slots:
                if slot not in cols:
                    cols.append(slot)
        rows.append(row)

    writer = csv.DictWriter(sys.stdout, fieldnames=cols)
    writer.writeheader()
    writer.writerows(rows)

def write_simple_robot_csv(terms: List[GoldTerm]) -> None:
    """
    Write a list of GoldTerms to a simple robot template

    :param terms:
    :return:
    """
    import csv

    rows = []
    cols = []
    hmap = {
        "id": "ID",
    }
    for term in terms:
        row = {}
        status = "partial"
        if term.curated:
            status = "complete"
        for slot in vars(term):
            if slot in ["label", "level", "curated", "parent", "vocab_differentia"]:
                continue
            obj = getattr(term, slot)
            if obj is None:
                obj = ""
            if isinstance(obj, OntologyClass):
                row[f"{slot}_id"] = obj.id
                row[f"{slot}_label"] = obj.label
                slots = [f"{slot}_id", f"{slot}_label"]
            else:
                row[slot] = str(obj)
                slots = [slot]
            for slot in slots:
                if slot not in cols:
                    cols.append(slot)
        info = {}
        for k, v in row.items():
            if k.endswith("_id"):
                if k not in hmap:
                    hmap[k] = f"AI MIXS:{k.replace('_id', '')}"
            elif k.endswith("_label"):
                k2 = k.replace("_label", "")
                info[k2] = v
                if k not in hmap:
                    hmap[k] = ""
            elif k == "id":
                pass
            else:
                if ":" in v and " " not in v:
                    hmap[k] = f"AI MIXS:{k}"
                else:
                    hmap[k] = f"A MIXS:{k}"
                if k not in hmap:
                    hmap[k] = v
        if info:
            hmap["info"] = "A rdfs:comment"
            row["info"] = yaml.dump(info).strip().replace("\n", "; ")
            row["info"] += f"; {status}"

        rows.append(row)

    writer = csv.DictWriter(sys.stdout, fieldnames=hmap.keys())
    writer.writeheader()
    writer.writerows([hmap] + rows)

@click.command()
@click.option('-o', '--output')
@click.option(
    "--curated-only/--no-curated-only",
    default=False,
)
@click.option(
    "--uncurated-only/--no-uncurated-only",
    default=False,
    show_default=True,
    help="Only output uncurated terms",
)
@click.option(
    "--stream/--no-stream",
    default=False,
    show_default=True,
    help="Stream output",
)
@click.option(
    "--propagate/--no-propagate",
    default=False,
    show_default=True,
    help="Propagate relationships down the hierarchy",
)
@click.option(
    "--template-output",
    "-t",
    help="Output a robot template",
)
@click.option(
    "--format",
    "-f",
    help="Output format",
)
@click.argument('input')
def cli(input: str, output: str, curated_only: bool, uncurated_only: bool, format: str, stream: bool, propagate: bool, template_output: Optional[str]):
    adapter = get_adapter(input)
    dict_objs = []
    objs = []
    for term in create_template(adapter):
        if curated_only and term.curated is False:
            continue
        if uncurated_only and term.curated is not False:
            continue
        objs.append(term)
        as_dict = term.model_dump(exclude_unset=True)
        if stream:
            print(yaml.dump(as_dict))
    if propagate:
        objs = propagate_down(objs)
    # sort objects by label
    dict_objs = [o.model_dump(exclude_unset=True) for o in objs]
    dict_objs = sorted(dict_objs, key=lambda x: x['label'])
    parent = {
        "terms": dict_objs
    }
    if not format or format == "yaml":
        print(yaml.dump(parent, sort_keys=False))
    elif format == "csv":
        write_csv(objs)
    elif format == "simple-robot":
        write_simple_robot_csv(objs)
    elif format == "robot":
        write_robot_template(objs)
    else:
        raise ValueError(f"Unsupported format: {format}")
    if template_output:
        with open(template_output, 'w', encoding='utf-8') as stream:
            write_robot_template(objs, stream)



if __name__ == '__main__':
    cli()
