import json
import re
import subprocess

from pathlib import Path
from datetime import datetime
from horology import timed
from openpecha.core.pecha import OpenPechaFS

from transfer_annotation import transfer_line_break
# @timed(unit='s', name="Compute collated text: ")
def get_collatex_output(witnesses_path):
    collatex_output = subprocess.check_output(f"java -jar collatex-tools-1.7.1.jar {str(witnesses_path)} -f csv", shell=True)
    return collatex_output

def get_base_names(pecha):
    base_names = []
    base_paths = list(pecha.base_path.iterdir())
    for base_path in base_paths:
        base_names.append(base_path.stem)
    base_names.sort()
    return base_names

def get_witnesses(witness_paths):
    witnesses = {
        'D':OpenPechaFS(path=witness_paths[0]),
        'N':OpenPechaFS(path=witness_paths[1]),
        'C':OpenPechaFS(path=witness_paths[2]),
        'G':OpenPechaFS(path=witness_paths[3]),
        'P':OpenPechaFS(path=witness_paths[4])
    }
    # for witness_walker, witness_path in enumerate(witness_paths, 1):
    #     witnesses[f"W{witness_walker}"] = OpenPechaFS(path=witness_path)
    return witnesses

def get_tokenized_witness(witness):
    witness = witness.replace(" ", "𰵀")
    witness = witness.replace("\n", "𰵁")
    tokenized_witness = re.sub("(་|།)", "\g<1> ", witness)
    return tokenized_witness

def detokenize_witness(tokenized_witness):
    detokenized_text = tokenized_witness.replace(" ", "")
    detokenized_text = detokenized_text.replace("𰵀", " ")
    detokenized_text = detokenized_text.replace("𰵁", "")
    return detokenized_text

def fill_missing_witness(witnesses, number_of_witnesses):
    new_witnesses = []
    for witness in witnesses:
        new_witnesses.append(witness)
    for walker in range(0, number_of_witnesses-len(witnesses)):
        new_witnesses.append("")
    return new_witnesses

def get_bases(base_name, witnesses):
    witness_bases = {
        "witnesses": []
    }
    for witness_id, witness in witnesses.items():
        
        witness_base = witness.read_base_file(base_name)
        tokenized_base = get_tokenized_witness(witness_base)
        cur_witness = {
            'id': witness_id,
            'content': tokenized_base
        }
        witness_bases["witnesses"].append(cur_witness)
    return witness_bases

def get_versions(segment, number_of_witnesses):
    versions = segment.split(",")
    versions = fill_missing_witness(versions, number_of_witnesses)
    return versions

def get_best_version(versions):
    if len(set(versions)) == len(versions):
        best_version = versions[0]
    else:   
        best_version = max(versions, key = versions.count)
    return best_version


def get_unique_versions(versions):
    reformated_versions = []
    for version in versions:
        reformated_versions.append(detokenize_witness(version))
    return set(reformated_versions)

def get_diffs(versions):
    diffs = ''
    unique_versions = set(versions)
    if len(unique_versions) > 1:
        diffs += f'<d>{versions[0]},<n>{versions[1]},<c>{versions[2]},<g>{versions[3]},<p>{versions[4]}'
    return diffs

def get_complete_collated_page(collatex_output, number_of_witnesses):
    collated_page = ""
    collatex_output = collatex_output.decode('utf-8')
    segments = collatex_output.splitlines()
    for segment in segments[1:]:
        versions = get_versions(segment, number_of_witnesses)
        best_version = get_best_version(versions)
        diffs = get_diffs(versions)
        if diffs:
            collated_page += f"{best_version}[{diffs}]"
        else:
            collated_page += best_version
    return collated_page

def get_collated_page(witness_pages):
    collatex_output_page = ""
    collatex_input_json = {
        'witnesses': []
    }
    for witness_id, witness_page in witness_pages.items():
        tokenized_page = get_tokenized_witness(witness_page)
        cur_witness = {
            'id': witness_id,
            'content': tokenized_page
        }
        collatex_input_json["witnesses"].append(cur_witness)
    collatex_input_json_obj = json.dumps(collatex_input_json)
    witness_combined_path = Path('./witnesses.json')
    witness_combined_path.write_text(collatex_input_json_obj, encoding='utf-8')
    collatex_output_page = get_collatex_output("./witnesses.json")
    witness_combined_path.unlink()
    return collatex_output_page

def get_witness_pages(witness_pagination, witness_base):
    witness_pages = {}
    for uuid, page_annotation in witness_pagination['annotations'].items():
        img_num = page_annotation['imgnum']
        start = page_annotation['span']['start']
        end = page_annotation['span']['end']
        page_text = witness_base[start:end]
        witness_pages[img_num] = page_text
    return witness_pages

def get_cur_pages_of_witnesses(witnesses_pages, img_num):
    cur_pages_of_witnesses = {}
    for witness_id, witness_pages in witnesses_pages.items():
        cur_pages_of_witnesses[witness_id] = witness_pages.get(img_num, '')
    return cur_pages_of_witnesses


def get_witnesses_pages(witnesses, base_name):
    witnesses_pages = {}
    for witness_id, witness in witnesses.items():
        witness_base = witness.read_base_file(base_name)
        witness_pagination = witness.read_layers_file(base_name, "Pagination")
        witnesses_pages[witness_id] = get_witness_pages(witness_pagination, witness_base)
    return witnesses_pages


@timed(unit='s', name="Compute collated text: ")
def get_collated_base(base_name, witnesses, number_of_witnesses):
    collated_base = ""
    derge_base = witnesses['D'].read_base_file(base_name)
    pagination_layer = witnesses['D'].read_layers_file(base_name, "Pagination")
    witnesses_pages = get_witnesses_pages(witnesses, base_name)
    for uuid, page_annotation in pagination_layer['annotations'].items():
        imgnum = page_annotation['imgnum']
        witness_pages = get_cur_pages_of_witnesses(witnesses_pages, imgnum)
        collatex_output_page = get_collated_page(witness_pages)
        if collatex_output_page:
            collated_base += get_complete_collated_page(collatex_output_page, number_of_witnesses)
    collated_base = detokenize_witness(collated_base)
    collated_base = transfer_line_break(derge_base, collated_base)
    return collated_base

def get_collated_text(witness_paths):
    collated_text = {}
    number_of_witnesses = len(witness_paths)
    witnesses = get_witnesses(witness_paths)

    reference_witness = witnesses['D']
    ref_witness_base_names = get_base_names(reference_witness)
    for base_name in ref_witness_base_names:
        collated_text[base_name] = get_collated_base(base_name, witnesses, number_of_witnesses)
    return collated_text


if __name__ == "__main__":
    parent_dir = Path('./data/opfs/part_2')
    witness_paths = [
        Path('./data/opfs/part_2/I0001/I0001.opf'),
        Path('./data/opfs/part_2/I0002/I0002.opf'),
        Path('./data/opfs/part_2/I0003/I0003.opf'),
        Path('./data/opfs/part_2/I0004/I0004.opf'),
        Path('./data/opfs/part_2/I0005/I0005.opf'),
    ]
    collated_base = get_collated_text(witness_paths)
    Path('./data/collated_part_2.txt').write_text(collated_base['A718'])