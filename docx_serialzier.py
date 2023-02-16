import os
import re
from pathlib import Path

from docx import Document
from docx.shared import Pt
from pypandoc import convert_text
from openpecha.utils import load_yaml

def regroup_same_notes(note_options):
    regrouped_notes = {}
    for pub_name, note_info in note_options.items():
        pub = pub_name[0].capitalize()
        regrouped_notes[note_info['note']] = [pub] if note_info['note'] not in regrouped_notes.keys() else regrouped_notes[note_info['note']] + [pub]
    return regrouped_notes

def get_note_text(note_options):
    note_text = ""
    regrouped_notes = regroup_same_notes(note_options)
    for note, pubs in regrouped_notes.items():
        pub_names = ','.join(pubs)
        note_text += f"{pub_names}: {note}; "
    return note_text[:-1]

def parse_note(durchen_layer):
    note_md = "\n\n"
    for note_walker, (_, ann) in enumerate(durchen_layer['annotations'].items(),1):
        note_text = get_note_text(ann['options'])
        note_md += f"[^{note_walker}]: {note_text}\n"
    return note_md


def save_collated_docx(base_text, durchen_layer, output_dir, text_title):
    collated_text_md = ""
    char_walker = 0
    for note_walker, (_, ann) in enumerate(durchen_layer['annotations'].items(),1):
        ann_end = ann['span']['end']
        collated_text_md += f"{base_text[char_walker:ann_end]}[^{note_walker}]"
        char_walker = ann_end
    collated_text_md += base_text[char_walker:]
    collated_text_md = re.sub('\n', '\n\n', collated_text_md)
    collated_text_md += parse_note(durchen_layer)
    output_path = output_dir / f"{text_title}.docx"
    convert_text(
        collated_text_md, "docx", "markdown", outputfile=str(output_path)
    )


if __name__ == "__main__":
    text_title = "rangdel"
    base_text = Path(f'./data/{text_title}/vulgate/OF67F47FF/OF67F47FF.opf/base/B63B.txt').read_text(encoding='utf-8')
    durchen_layer = load_yaml(Path(f'./data/{text_title}/vulgate/OF67F47FF/OF67F47FF.opf/layers/B63B/Durchen.yml'))
    output_dir = Path(f'./data/{text_title}/')
    save_collated_docx(base_text, durchen_layer,output_dir, text_title)