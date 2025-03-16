
from pathlib import Path
from typing import Optional 
from rich.console import Console

from .packages import Package
from .sitter.java_examiner import examine
from .paths import search_java_files

def examine_all_java(base: Path, root: Optional[Package] = None) -> Package: 
    if root is None: root = Package()
    for java_file in search_java_files(base): 
        print(java_file.as_posix())
        examine(java_file, root) 
    
    root.resolve_type_identifiers()
    return root 

