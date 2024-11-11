from pathlib import Path

from gold_ontology.gold_transform import translate_goldpath_file_to_owl
import os

TEST_DIR = Path(__file__).parent
INPUT_DIR = TEST_DIR / 'inputs'
OUTPUT_DIR = TEST_DIR / 'outputs'

def test_convert():
    o = translate_goldpath_file_to_owl(INPUT_DIR / 'goldpaths.tsv')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR /'gold.ofn', "w") as stream:
        stream.write(str(o))

