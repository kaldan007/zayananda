from pathlib import Path

from antx.core import transfer


def transfer_line_break(src_text, target_text):
    patterns = [['line_break', "(\n)"]]
    new_text = transfer(src_text, patterns,target_text)
    return new_text

def transfer_page_annoation(src_text, target_text):
    patterns = [['pagination', '(\[\w\d.+\w\])']]
    new_text = transfer(src_text, patterns, target_text)
    return new_text

def transfer_all_pagination(collated_text, diplomatic_paths):

    for diplomatic_path in diplomatic_paths:
        diplomatic_text = diplomatic_path.read_text(encoding='utf-8')
        collated_text = transfer_page_annoation(diplomatic_text, collated_text)
    return collated_text



if __name__ == "__main__":
    collated_text = Path('./data/collated_part_1.txt').read_text(encoding='utf-8')
    diplomatic_paths = list(Path('./data/text_with_pagination/part_1').iterdir())
    collated_text_with_paginations = transfer_all_pagination(collated_text, diplomatic_paths)