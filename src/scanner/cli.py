
from pathlib import Path
import json
from typing import Optional 

import click 
from rich.console import Console 

from .packages import Package
from .examiner import examine_all_java
import logging

@click.group()
def main(): 
    ...

@main.command("load") 
@click.argument("filename") 
def load_scan(filename: str): 
    p = Path(filename) 
    d = json.loads(p.read_text()) 
    root = Package() 
    console = Console() 
    Package.fromdict(root, d) 
    console.print(root.as_tree())

@main.command("examine") 
@click.argument("filename")
@click.option("-s", "--save-file", type=str, help="Optional file to save to, and load from")
@click.option("--verbose", is_flag=True, help="Verbose logging level")
def examine_path(filename: str, save_file: str, **kwargs):
    log_level = logging.DEBUG if kwargs.get('verbose', False) else logging.INFO
    logging.basicConfig(level=log_level)

    console = Console()

    root = Package()
    if save_file is not None: 
        p = Path(save_file) 
        if p.exists(): 
            Package.fromdict(root, json.loads(p.read_text()))
    
    examine_all_java(Path(filename), root)
    
    console.print(root.as_tree())
    if save_file is not None: 
        p = Path(save_file) 
        with p.open('wt') as outf: 
            outf.write(json.dumps(root.asdict(), indent=2))

if __name__ == '__main__': 
    main()

        