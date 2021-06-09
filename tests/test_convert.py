from gold_ontology.gold_transform import translate
import os

cwd = os.path.abspath(os.path.dirname(__file__))
INPUT_DIR = os.path.join(cwd, 'inputs')
OUTPUT_DIR = os.path.join(cwd, 'outputs')

def test_convert():
    print('TESTING')
    o = translate(os.path.join(INPUT_DIR, 'goldpaths.tsv'))

