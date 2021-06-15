import csv
import click
import re
import urllib
import hashlib
from rdflib import Namespace, URIRef
from rdflib.namespace import RDFS, SKOS
from typing import List
from funowl import OntologyDocument, Ontology, ObjectSomeValuesFrom, ClassAssertion, \
    SubClassOf, ObjectHasValue, AnnotationAssertion, ObjectIntersectionOf, Prefix

GOLD_PATH = Namespace('https://w3id.org/gold.path/')
GOLD_VOCAB = Namespace('https://w3id.org/gold.vocab/')
OIO = Namespace('http://www.geneontology.org/formats/oboInOwl#')

GOLDPATH_COLS = ['ECOSYSTEM PATH ID', 'ECOSYSTEM', 'ECOSYSTEM CATEGORY', 'ECOSYSTEM TYPE', 'ECOSYSTEM SUBTYPE', 'SPECIFIC ECOSYSTEM']
UNC = 'Unclassified'
Label = str

def make_label(row: List[str]) -> Label:
    n = " > ".join(row)
    return n

def safe_id(atom: str) -> str:
    return urllib.parse.quote(atom.replace(' ', '-'))

def make_uri(id: str) -> str:
    return f'gold.path:{id}'
def make_curie_for_atom(atom: str) -> str:
    #return make_uri(urllib.parse.quote(atom))
    id = safe_id(atom)
    return f'gold.vocab:{id}'

def translate_goldpaths(f: str):
    o = Ontology("http://purl.obolibrary.org/obo/gold.owl")
    o.annotation(RDFS.label, 'gold')
    doc = OntologyDocument(GOLD_PATH, o)
    doc.prefixDeclarations.append(Prefix('gold.path', GOLD_PATH))
    doc.prefixDeclarations.append(Prefix('gold.vocab', GOLD_VOCAB))
    row2id = {}
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
    # labels
    for t, c in row2id.items():
        row = list(t)
        label = make_label(row)
        #print(f'{c} Label = {label}')
        o.axioms.append(AnnotationAssertion(RDFS.label, c, label))
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

def parse_synonyms(doc: OntologyDocument, f: str) -> None:
    o = doc.ontology
    with open(f, 'r') as stream:
        reader = csv.reader(stream, delimiter='\t')
        for id, syn in reader:
            if id == 'id':
                continue
            o.axioms.append(AnnotationAssertion(OIO.hasExactSynonym, id, syn))



@click.command()
@click.option('-o', '--output')
@click.option('-s', '--synonyms')
@click.argument('input')
def cli(input: str, output: str, synonyms: str):
    doc = translate_goldpaths(input)
    if synonyms is not None:
        parse_synonyms(doc, synonyms)
    with open(output, 'w') as stream:
        stream.write(str(doc))


if __name__ == '__main__':
    cli()
