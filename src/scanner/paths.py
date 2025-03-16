
from typing import Generator, List, Dict

from pathlib import Path 
import re 

JAVA_FILENAME = re.compile("(.*)\\.java")
XML_FILENAME = re.compile("(.*)\\.xml")

def search_java_files(p: Path) -> Generator[Path, None, None]: 
    return search_files(p, JAVA_FILENAME)

def search_files(p: Path, filename_regex: re.Pattern) -> Generator[Path, None, None]: 
    if p.is_dir(): 
        for f in p.iterdir(): 
            if f.is_file(): 
                m = filename_regex.match(f.name) 
                if m: 
                    yield f 
            else: 
                yield from search_files(f, filename_regex=filename_regex)
    else: 
        yield p