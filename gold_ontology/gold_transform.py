import csv
import click
import re
import urllib
import hashlib
from rdflib import Namespace, URIRef
from rdflib.namespace import RDFS
from typing import List
from funowl import OntologyDocument, Ontology, ObjectSomeValuesFrom, AnnotationAssertion, ObjectIntersectionOf, Prefix

GOLD = Namespace('https://w3id.org/gold/')

COLS = ['ECOSYSTEM PATH ID','ECOSYSTEM', 'ECOSYSTEM CATEGORY', 'ECOSYSTEM TYPE', 'ECOSYSTEM SUBTYPE', 'SPECIFIC ECOSYSTEM']
UNC = 'Unclassified'
Label = str

def make_label(row: List[str]) -> Label:
    n = " > ".join(row)
    return n

def make_uri(id: str) -> str:
    return f'gold.path:{id}'
def make_uri_from_atom(atom: str) -> str:
    #return make_uri(urllib.parse.quote(atom))
    return make_uri(urllib.parse.quote(atom.replace(' ', '-')))

def translate(f: str):
    o = Ontology("http://purl.obolibrary.org/obo/gold.owl")
    o.annotation(RDFS.label, 'gold')
    doc = OntologyDocument(GOLD, o)
    doc.prefixDeclarations.append(Prefix('gold.path', GOLD))
    row2id = {}
    atoms = set()
    with open(f, 'r') as stream:
        reader = csv.reader(stream, delimiter='\t')
        for row in reader:
            if row[0] == COLS[0]:
                continue
            while row[-1] == UNC:
                row.pop()
            id = row[0]
            if id == '':
                continue
            row = row[1:]
            for x in row:
                atoms.add(x)
            c = make_uri(id)
            row2id[tuple(row)] = c
    for a in atoms:
        c = make_uri_from_atom(a)
        o.axioms.append(AnnotationAssertion(RDFS.label, c, a))
        o.subClassOf(c, make_uri('AtomicElement'))
    # fill in missing parts
    for row, id in row2id.copy().items():
        parent = row[0:-1]
        while parent != ():
            if parent not in row2id:
                row2id[parent] = make_uri_from_atom('-'.join(parent))
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
            vc = make_uri_from_atom(v)
            vp = make_uri_from_atom(COLS[i])
            svf = ObjectSomeValuesFrom(vp, vc)
            xs.append(svf)
            i += 1
        if len(xs) > 1:
            ixn = ObjectIntersectionOf(*xs)
        elif len(xs) == 1:
            ixn = xs[0]
        o.equivalentClasses(c, ixn)
    for c in COLS:
        vp = make_uri_from_atom(COLS[i])
        o.subObjectPropertyOf(vp, make_uri_from_atom('environmental_property'))
    return doc




@click.command()
@click.option('-o', '--output')
@click.argument('input')
def cli(input: str, output: str):
    doc = translate(input)
    with open(output, 'w') as stream:
        stream.write(str(doc))

if __name__ == '__main__':
    cli()
