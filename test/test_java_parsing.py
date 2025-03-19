
from scanner.sitter.java_examiner import examine, parse_to_node, Package
from rich.console import Console 
from pathlib import Path 

def test_java_parsing(): 
    p = Path(__file__).parent / 'java_test' / 'test' / 'TestClass.java' 
    node, bs = parse_to_node(p) 
    tree = node.astree()
    console = Console() 
    console.print(tree) 
    assert node.package.identifier.value == "test"
    
def test_examine_java(): 
    p = Path(__file__).parent / 'java_test' / 'test' / 'TestClass.java' 
    root = Package()
    examine(p, root)
    assert root.packages.get('test').class_files.get('TestClass.java') is not None