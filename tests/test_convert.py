from gold_ontology.gold_transform import translate_goldpaths
import os

cwd = os.path.abspath(os.path.dirname(__file__))
INPUT_DIR = os.path.join(cwd, 'inputs')
OUTPUT_DIR = os.path.join(cwd, 'outputs')

def test_convert():
    print('TESTING')
    o = translate_goldpaths(os.path.join(INPUT_DIR, 'goldpaths.tsv'))
    with open(os.path.join(OUTPUT_DIR, 'gold.ofn')) as stream:
        stream.write(str(o))

