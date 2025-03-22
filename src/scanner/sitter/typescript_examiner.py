from pathlib import Path 
from typing import Dict 

from tree_sitter import Language, Parser, Node
from tree_sitter_language_pack import get_language, get_parser

from .node import TypedNode

TS_LANG = get_language('typescript')
TS_PARSER = get_parser('typescript')

def convert_to_dict(node, lang) -> Dict: 
    ...

def parse_to_node(p: Path): 
    bs = p.read_bytes() 
    parse_tree = TS_PARSER.parse(bs) 
    root_node = parse_tree.root_node
    d = convert_to_dict(root_node, TS_LANG)
    return TypedNode(d), bs
