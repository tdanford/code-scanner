
from scanner.sitter.xml_examiner import * 

def test_json_context_parsing(): 
    p = Path(__file__).parent / 'json-context.xml' 
    node, bs = parse_to_node(p) 
    root = node.element[0] 
    xml_tree: XMLTree = create_xml_tree(root) 
    console = Console() 
    console.print(xml_tree) 
    assert xml_tree.attrs.get('xmlns') == '"http://www.springframework.org/schema/beans"'
    