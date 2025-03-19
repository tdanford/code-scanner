
import tree_sitter_xml as tsxml 
from tree_sitter import Parser, Language, Node 
from rich.console import Console 
from rich.tree import Tree 
from pathlib import Path 
from typing import Dict, List

from .node import TypedNode, QuerySet, create_tree

XML_LANGUAGE = Language(tsxml.language_xml()) 
XML_PARSER = Parser(XML_LANGUAGE) 

class XMLContent: 
    def astree(self): 
        ...

class XMLCharData(XMLContent): 
    
    char_data: str 
    
    def __init__(self, node: TypedNode): 
        self.char_data = node.value
    
    def astree(self): 
        return f"CHAR_DATA: \"{self.char_data}\""
    
    def __repr__(self) -> str: 
        return f"CHAR_DATA({self.char_data[0:20]})"

class XMLComment(XMLContent): 
    
    comment: str 
    
    def __init__(self, node: TypedNode): 
        self.comment = node.value
    
    def astree(self): 
        return f"COMMENT: {self.comment}"
    
    def __repr__(self) -> str: 
        return f"COMMENT({self.char_data[0:20]})"


class XMLTree(XMLContent): 

    name: str 
    attrs: Dict[str, str]
    children: List[XMLContent]

    def __init__(self, node: TypedNode): 
        try: 
            self.name = node.Tag.first().Name.value
            self.attrs = {
                a.Name.value: a.AttValue.value
                for a in node.Tag.Attribute
            }
            self.children = [
                create_xml_tree(c) for c in node.content.children
            ]
        except IndexError: 
            console = Console()
            console.print(node.astree())
            console.print(node.Tag) 
            console.print(node.content.children)
    
    def __repr__(self) -> str: 
        return f"Element({self.name})"
    
    def astree(self) -> Tree: 
        t = Tree(f"ELEMENT: {self.name}")
        if len(self.attrs) > 0: 
            at = Tree("ATTRIBUTES")
            for (k, v) in self.attrs.items(): 
                at.add(f"{k}={v}")
            t.add(at) 
        if len(self.children) > 0: 
            ct = Tree("CONTENT") 
            for i in range(len(self.children)): 
                ct.add(self.children[i].astree())
            t.add(ct) 
        return t
        
    
def create_xml_tree(n: TypedNode) -> XMLContent: 
    if n.type == 'CharData': 
        return XMLCharData(n) 
    elif n.type == 'Comment': 
        return XMLComment(n)
    else: 
        return XMLTree(n)    

def convert_to_dict(node: Node, lang: Language = XML_LANGUAGE) -> Dict[str, any]: 
    """Converts a TreeSitter Node into a tree-of-dicts that we use as a lightweight AST 

    This drops certain kinds of Nodes (mostly token-like nodes) and standardizes out the 
    fields that we want to use later.  Since we mostly just wrap this tree-of-dicts into 
    TypedNode objects, it'd probably be easy to just adapt the TypedNode stuff to work 
    directly from the TreeSitter Nodes themselves.

    Args:
        node (Node): a Node generated by TreeSitter

    Returns:
        Dict[str, any]: a reduced AST as a series of nested Dictionaries
    """
    field_id = lang.id_for_node_kind(node.type, True)
    if field_id is None: 
        return None
    
    pairs = [
        x for x in list(convert_to_dict(c, lang) for c in node.children) if x is not None
    ]
    val = node.text.decode("UTF-8") if node.text is not None else None
    if len(pairs) > 0: 
        d = {
            "_type": node.type, 
            "_children": pairs,
            "_start": node.start_byte, 
            "_end": node.end_byte
        }
        if val is not None: 
            d['_value'] = val 
    else: 
        d = { 
             "_type": node.type,
             "_value": node.text.decode("UTF-8"),
            "_start": node.start_byte, 
            "_end": node.end_byte
        }
    return d

def parse_to_node(p: Path): 
    bs = p.read_bytes() 
    parse_tree = XML_PARSER.parse(bs) 
    root_node = parse_tree.root_node
    d = convert_to_dict(root_node, XML_LANGUAGE)
    n = TypedNode(d) 
    return n, bs