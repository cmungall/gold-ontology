import csv
import re
from collections import defaultdict
from copy import copy
from pathlib import Path

import click
import urllib
import hashlib
from rdflib import Namespace, URIRef
from rdflib.namespace import RDFS, SKOS
from typing import List, Dict, Tuple, Union
from funowl import OntologyDocument, Ontology, ObjectSomeValuesFrom, ClassAssertion, \
    SubClassOf, ObjectHasValue, AnnotationAssertion, ObjectIntersectionOf, Prefix, AnnotationSubject, Annotation

OBO_PREFIXES = ['UBERON', 'ENVO', 'PR', 'CHEBI', 'FOODON', 'PATO', 'NCBITaxon', 'PO', 'OBI', 'FAO', 'MIXS']
ENVO = Namespace('http://purl.obolibrary.org/obo/ENVO_')
GOLD_PATH = Namespace('https://w3id.org/gold.path/')
GOLD_PATH_PREFIX = "GOLDTERMS"
GOLD_VOCAB = Namespace('https://w3id.org/gold.vocab/')
GOLD_VOCAB_PREFIX = "GOLDVOCAB"
OIO = Namespace('http://www.geneontology.org/formats/oboInOwl#')

GOLDPATH_COLS = ['ECOSYSTEM PATH ID', 'ECOSYSTEM', 'ECOSYSTEM CATEGORY', 'ECOSYSTEM TYPE', 'ECOSYSTEM SUBTYPE', 'SPECIFIC ECOSYSTEM']
ENVOPATH_COLS = ['env_package', 'env_broad_scale', 'env_local_scale', 'env_medium']
UNC = 'Unclassified'
Label = str

def make_label(row: List[str], sep=' > ', rev=False) -> Label:
    if rev:
        row = list(row)
        row.reverse()
        row = tuple(row)
    n = sep.join(row)
    return n


def safe_id(atom: str) -> str:
    #atom = atom.replace("(", "")
    #atom = atom.replace(")", "")
    safe = urllib.parse.quote(atom.replace(' ', '-'))
    safe = safe.replace('%', '_')
    return safe


def make_uri(id: str) -> str:
    return f'{GOLD_PATH_PREFIX}:{id}'


def make_curie_for_atom(atom: str) -> str:
    #return make_uri(urllib.parse.quote(atom))
    if atom.startswith("gold.vocab:"):
        atom = atom.replace("gold.vocab:", "")
    id = safe_id(atom)
    return f'{GOLD_VOCAB_PREFIX}:{id}'


def make_envo_path_id(row: List[str]) -> str:
    id = safe_id('-'.join(row))
    return f'envo.path{id}'


def subtuples(row: tuple) -> List[tuple]:
    return [tuple(row[i:]) for i in range(0, len(row))]


def count_distinct_subtuples(row2id: dict) -> Dict[tuple, int]:
    subtuple_counts = defaultdict(int)
    for row in row2id.keys():
        for subt in subtuples(row):
            subtuple_counts[subt] += 1
    return subtuple_counts

def translate_goldpath_file_to_owl(f: Union[str, Path]):
    """
    Translate a GOLD path file into an ontology.

    The ontology will have 4 roots:

    - one root per GOLD ECOSYSTEM (Engineered, Environmental, Host-associated)
    - one root AtomicElement

    the gold ecosystem path terms will have equivalence axioms, e.g.

    .. code-block:: owl

      'Engineered > Bioreactor > Anaerobic > Biogas'
       EquivalentTo:
        ECOSYSTEM-PATH-ID some Engineered and
        ECOSYSTEM some Bioreactor and
        ECOSYSTEM_CATEGORY some Anaerobic and

    :param f: path to the GOLD path file
    :return:
    """
    o = Ontology("http://purl.obolibrary.org/obo/gold.owl")
    o.annotation(RDFS.label, 'gold')
    doc = OntologyDocument(GOLD_PATH, o)
    doc.prefixDeclarations.append(Prefix(GOLD_PATH_PREFIX, GOLD_PATH))
    doc.prefixDeclarations.append(Prefix(GOLD_VOCAB_PREFIX, GOLD_VOCAB))
    for p in OBO_PREFIXES:
        doc.prefixDeclarations.append(Prefix(p, Namespace(f'http://purl.obolibrary.org/obo/{p}_')))
    row2id = {} # maps vocab tuple to a gold path ID
    atom2ecosystem = {}
    atoms = set()
    with open(f, 'r') as stream:
        reader = csv.reader(stream, delimiter='\t')
        for row in reader:
            if row[0] == GOLDPATH_COLS[0]:
                continue
            while row[-1] == UNC:
                row.pop()
            id = row[0]
            if id == '':
                continue
            row = row[1:]
            for a in row:
                atoms.add(a)
                if a not in atom2ecosystem:
                    atom2ecosystem[a] = {}
                atom2ecosystem[a][row[0]] = True
            c = make_uri(id)
            row2id[tuple(row)] = c
    RootAE = make_uri('AtomicElement')
    for a in atoms:
        c = make_curie_for_atom(a)
        o.axioms.append(AnnotationAssertion(RDFS.label, c, a))
        #o.axioms.append(ClassAssertion(RootAE, c))
        o.axioms.append(SubClassOf(c, RootAE))
        for e in atom2ecosystem[a].keys():
            o.axioms.append(AnnotationAssertion(SKOS.inScheme, c, make_uri(e)))
    # fill in missing parts
    for row, id in row2id.copy().items():
        parent = row[0:-1]
        while parent != ():
            if parent not in row2id:
                row2id[parent] = make_uri(safe_id('-'.join(parent)))
            parent = parent[0:-1]
    # tree
    for row, id in row2id.items():
        parent = row[0:-1]
        if parent != ():
            o.subClassOf(id, row2id[parent])
    # find unique subtuples
    subtuples_counts = count_distinct_subtuples(row2id)
    # labels
    for t, c in row2id.items():
        row = list(t)
        label = make_label(row)
        #print(f'{c} Label = {label}')
        o.axioms.append(AnnotationAssertion(RDFS.label, c, label))
        # synonyms (unique only)
        for subt in subtuples(row):
            if subtuples_counts[subt] == 1:
                syn = make_label(subt, sep=", ", rev=True)
                if syn and syn != label:
                    o.axioms.append(AnnotationAssertion(OIO.hasExactSynonym, c, syn))
        i = 0
        xs = []
        for v in row:
            vc = make_curie_for_atom(v)
            vp = make_curie_for_atom(GOLDPATH_COLS[i])
            svf = ObjectSomeValuesFrom(vp, vc)
            xs.append(svf)
            i += 1
        if len(xs) > 1:
            ixn = ObjectIntersectionOf(*xs)
        elif len(xs) == 1:
            ixn = xs[0]
        o.equivalentClasses(c, ixn)
    for c in GOLDPATH_COLS:
        vp = make_curie_for_atom(c)
        o.subObjectPropertyOf(vp, make_curie_for_atom('environmental_property'))
    return doc

def translate_envopaths(f: str):
    o = Ontology("http://purl.obolibrary.org/obo/envo/paths.owl")
    o.annotation(RDFS.label, 'envo paths')
    doc = OntologyDocument(ENVO, o)
    doc.prefixDeclarations.append(Prefix('envo.path', ENVO_PATH))
    doc.prefixDeclarations.append(Prefix('ENVO', ENVO))
    row2id = {}
    atom2ecosystem = {}
    atoms = set()
    with open(f, 'r') as stream:
        reader = csv.DictReader(stream, delimiter='\t')
        for item in reader:
            row = [item[k] for k in ENVOPATH_COLS]
            if None not in row:
                # todo: do something with blank IDs
                id = make_envopath_id(row)
                row2id[tuple(row)] = c
    # fill in missing parts
    for row, id in row2id.copy().items():
        parent = row[0:-1]
        while parent != ():
            if parent not in row2id:
                row2id[parent] = make_envopath_id(parent)
            parent = parent[0:-1]
    # tree
    for row, id in row2id.items():
        parent = row[0:-1]
        if parent != ():
            o.subClassOf(id, row2id[parent])
    # labels
    for t, c in row2id.items():
        row = list(t)
        label = make_label(row, '/') + ' sample'
        o.axioms.append(AnnotationAssertion(RDFS.label, c, label))
        i = 0
        xs = []
        for v in row:
            vc = envo_id(v)
            vp = make_curie_for_atom(GOLDPATH_COLS[i])
            svf = ObjectSomeValuesFrom(vp, vc)
            xs.append(svf)
            i += 1
        if len(xs) > 1:
            ixn = ObjectIntersectionOf(*xs)
        elif len(xs) == 1:
            ixn = xs[0]
        o.equivalentClasses(c, ixn)
    for c in GOLDPATH_COLS:
        vp = make_curie_for_atom(c)
        o.subObjectPropertyOf(vp, make_curie_for_atom('environmental_property'))
    return doc

def parse_synonyms(doc: OntologyDocument, f: str) -> None:
    """
    Parse a file with synonyms and inject them into the ontology

    :param doc:
    :param f: file to parse (2 col TSV)
    :return:
    """
    o = doc.ontology
    with open(f, 'r') as stream:
        reader = csv.DictReader(stream, delimiter='\t')
        for row in reader:
            id, syn = (row['id'], row['synonym'])
            if id and syn:
                o.axioms.append(AnnotationAssertion(OIO.hasExactSynonym, make_curie_for_atom(id), syn))

def parse_sssom(doc: OntologyDocument, f: str) -> None:
    """
    Parse a file with SSSOM mappings and inject them into the ontology

    :param doc:
    :param f:
    :return:
    """
    o = doc.ontology
    with open(f, 'r') as stream:
        # ignore comment lines starting with #
        # stream = filter(lambda x: not x.startswith('#'), stream)
        reader = csv.DictReader(stream, delimiter='\t')
        for row in reader:
            subject_id = row['subject_id']
            object_id = row['object_id']
            p = row['predicate_id']
            if p == 'skos:exactMatch':
                pred = SKOS.exactMatch
            elif p == 'skos:closeMatch':
                pred = SKOS.closeMatch
            elif p == 'skos:narrowMatch':
                pred = SKOS.narrowMatch
            elif p == 'skos:broadMatch':
                pred = SKOS.broadMatch
            else:
                continue
            anns = [Annotation(RDFS.label, row['object_label'])]
            aa = AnnotationAssertion(pred, subject_id, object_id, anns)
            o.axioms.append(aa)



@click.command()
@click.option('-o', '--output')
@click.option('-s', '--synonyms',
              help="Manually created synonyms for each GOLD vocab element",
              )
@click.option('-m', '--mappings', multiple=True)
@click.argument('input')
def cli(input: str, output: str, synonyms: str, mappings: Tuple[str]):
    """

    """
    doc = translate_goldpath_file_to_owl(input)
    if synonyms is not None:
        # inject synonyms
        parse_synonyms(doc, synonyms)
    if mappings is not None:
        # inject mappings
        for mappings_file in mappings:
            parse_sssom(doc, mappings_file)
    with open(output, 'w') as stream:
        owl_str = str(doc)
        # owl_str = re.sub(r'<(\S+)>', r'$\1', owl_str)
        stream.write(owl_str)


if __name__ == '__main__':
    cli()
