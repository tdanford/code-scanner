
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from pathlib import Path 
from dataclasses import dataclass, field, asdict
from rich.tree import Tree
import os

import re 

class Package: 
    
    full_path: List[str]
    parent: 'Package' 
    class_files: Dict[str, 'ClassFile']
    packages: Dict[str, 'Package']

    @staticmethod
    def fromdict(root: 'Package', d: Dict[str, any]) -> 'Package': 
        pth = d.get('full_path') 
        class_files = {
            n: ClassFile.fromdict(root, cf) for (n, cf) in d.get('class_files').items()
        }
        pkg: Package = root.get_package(pth)
        pkg.class_files.update(class_files)
        for pd in d.get('packages').values():
            Package.fromdict(root, pd)
        return pkg
    
    def __init__(self, full_path: List[str] = [], parent: 'Package' = None, class_files: Dict[str, 'ClassFile'] = None, packages: Dict[str, 'Package'] = None): 
        self.full_path = full_path
        self.parent = parent 
        self.class_files = { **class_files } if class_files is not None else {}
        self.packages = { **packages } if packages is not None else {}
    
    def __repr__(self) -> str: 
        return f"Package({self.full_name} : {self.packages.keys()})"
    
    def __getitem__(self, idx): 
        qual = idx.split(".") 
        return self.find_package(qual)
        
    def resolve_type_identifiers(self): 
        for (name, cf) in self.class_files.items(): 
            cf.resolve_all_class_type_identifiers()
        for (name, pkg) in self.packages.items(): 
            pkg.resolve_type_identifiers()
    
    def resolve_package_name(self, pkg_name: str) -> Optional['Package']:
        root = self.find_root()
        steps = pkg_name.split('.') 
        return root.find_package(steps)
    
    def resolve_fully_qualified_name(self, pkg_name: str, name: str) -> Optional['JavaClass']:
        pkg = self.resolve_package_name(pkg_name)
        if pkg is not None: 
            for (_, cf) in self.class_files.items():
                if name in cf.classes: 
                    return cf.classes[name]
        return None

    def as_tree(self) -> Tree: 
        t = Tree(self.name) 
        for (n, cf) in self.class_files.items(): 
            t.add(cf.as_tree()) 
        for (n, p) in self.packages.items(): 
            t.add(p.as_tree())
        return t
    
    def package_tree(self, include_files: bool = False) -> Tree: 
        lbl = f"[cyan]{self.name}[/cyan]"
        t = Tree(lbl)
        if include_files: 
            for (n, f) in self.class_files.items(): 
                t.add(f.file.name)
        for (n, p) in self.packages.items(): 
            t.add(p.package_tree(include_files=include_files))
        return t
    
    @property 
    def name(self) -> str: 
        if len(self.full_path) == 0: 
            return ''
        else: 
            return self.full_path[-1]
    
    @property
    def full_name(self) -> str: 
        return '.'.join(self.full_path)

    def asdict(self) -> Dict[str, any]: 
        return {
            "full_path": self.full_path, 
            "class_files": {
                name: cf.asdict() for (name, cf) in self.class_files.items()
            },
            "packages": {
                name: p.asdict() for (name, p) in self.packages.items()
            }
        }
    
    def find_root(self) -> 'Package': 
        if self.parent is None: 
            return self 
        else: 
            return self.parent.find_root()

    def find_package(self, package_name: List[str]) -> Optional['Package']:
        if len(package_name) == 0: 
            return self 
        else: 
            [head, *rest] = package_name 
            if head not in self.packages: 
                return None
            return self.packages[head].find_package(rest)

    def get_package(self, package_name: List[str]) -> 'Package': 
        if len(package_name) == 0: 
            return self 
        else: 
            [head, *rest] = package_name 
            return self.add_package(head).get_package(rest) 
    
    def add_package(self, name: str) -> 'Package': 
        if name in self.packages: 
            return self.packages.get(name) 
        else: 
            p = Package(self.full_path + [name], parent=self) 
            self.packages[name] = p 
            return p 
        
    def contains_file_at_path(self, p: Path) -> bool: 
        for cf in self.class_files.values(): 
            if cf.file.samefile(p): 
                return True
        for pkg in self.packages.values(): 
            if pkg.contains_file_at_path(p): 
                return True
        return False
    
    def source_locations(self) -> Set[Path]: 
        return set(cf.file.parent for (_, cf) in self.class_files.items())
    
    def source_files(self) -> Set[Path]: 
        return set(cf.file for (_, cf) in self.class_files.items())

@dataclass
class JavaField: 
    name: str 
    type: str 
    modifiers: List[str] = field(default_factory=list)
    annotations: List['JavaAnnotation'] = field(default_factory=list)

    @staticmethod 
    def fromdict(d: Dict[str, any]) -> 'JavaField': 
        return JavaField(
            name = d.get('name'), 
            type = d.get('type'), 
            modifiers=d.get('modifiers', []), 
            annotations=[JavaAnnotation.fromdict(a) for a in d.get("annotations", [])],
        )
    
    @property 
    def modstring(self) -> str: 
        return " ".join(self.modifiers)

@dataclass 
class JavaAnnotation: 
    
    name: str 
    arguments: List[str] = field(default_factory=list)

    @staticmethod 
    def fromdict(d: Dict[str, any]) -> 'JavaAnnotation': 
        return JavaAnnotation(**d)
    
    def __repr__(self) -> str: 
        args = f",".join(self.arguments)
        return f"@{self.name}({args})"

@dataclass
class JavaParameter: 
    name: str 
    type: str 

    @staticmethod 
    def fromdict(d: Dict[str, any]) -> 'JavaParameter': 
        return JavaParameter(**d)

@dataclass
class JavaMethod: 
    name: str 
    return_type: str 
    parameters: List[JavaParameter]
    modifiers: List[str] = field(default_factory=list)
    annotations: List[JavaAnnotation] = field(default_factory=list)

    @property 
    def is_public(self) -> bool: return 'public' in self.modifiers

    @property 
    def is_static(self) -> bool: return 'static' in self.modifiers

    def as_tree(self) -> Tree: 
        pubs = ','.join(self.modifiers)
        t = Tree(f"METHOD {self.name}:{self.return_type} ({pubs})")
        for p in self.parameters: 
            t.add(f"PARAM {p.name} {p.type}")
        for a in self.annotations: 
            t.add(f"ANNOTATION {a}")
        return t
    
    @staticmethod 
    def fromdict(d: Dict[str, any]) -> 'JavaMethod': 
        return JavaMethod(
            name = d.get('name'), 
            return_type = d.get('return_type'), 
            parameters = [JavaParameter.fromdict(pd) for pd in d.get('parameters')],
            modifiers=d.get('modifiers', []), 
            annotations=[JavaAnnotation.fromdict(a) for a in d.get("annotations", [])],
        )

class JavaClassKind(Enum): 
    CLASS = "class"
    INTERFACE = "interface"
    ENUM = "enum"

def custom_asdict_factory(data):

    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value
        return obj

    return dict((k, convert_value(v)) for k, v in data)

@dataclass
class JavaClass: 
    
    name: str 
    kind: JavaClassKind = field(default=JavaClassKind.CLASS)
    fields: Dict[str, JavaField] = field(default_factory=dict)
    methods: Dict[str, JavaMethod] = field(default_factory=dict)
    classes: Dict[str, 'JavaClass'] = field(default_factory=dict)
    type_identifiers: Set[str] = field(default_factory=set)
    modifiers: List[str] = field(default_factory=list)
    annotations: List[JavaAnnotation] = field(default_factory=list)

    def as_tree(self) -> Tree: 
        mod_string = ",".join(self.modifiers)
        t = Tree(f"{self.kind.value} {self.name} ({mod_string})")
        for a in self.annotations: 
            t.add(f"ANNOTATION {a}")
        for (n, f) in self.fields.items(): 
            ft = Tree(f"FIELD {f.name}:{f.type} ({f.modstring})")
            for ann in f.annotations: 
                ft.add(f"ANNOTATION {ann}")
            t.add(ft)
        for (n, m) in self.methods.items(): 
            t.add(m.as_tree())
        for (n, c) in self.classes.items(): 
            t.add(c.as_tree())
        if len(self.type_identifiers) > 0: 
            tis = Tree("TYPE_IDENTIFIERS")
            for ti in self.type_identifiers: tis.add(ti)
            t.add(tis) 
        return t
    
    def __hash__(self) -> int: 
        return hash((
            self.name, self.kind.value, tuple(self.fields.keys()), tuple(self.methods.keys())
        ))
    
    def asdict(self, **kwargs) -> Dict[str, any]: 
        return asdict(self, **kwargs)
    
    @staticmethod
    def fromdict(d: Dict[str, any]) -> 'JavaClass': 
        return JavaClass(
            name=d.get('name'), 
            kind=JavaClassKind(d.get("kind")),
            fields={n: JavaField.fromdict(f) for (n, f) in d.get('fields').items()}, 
            methods={n: JavaMethod.fromdict(f) for (n, f) in d.get('methods').items()}, 
            classes={n: JavaClass.fromdict(f) for (n, f) in d.get('classes').items()},
            modifiers=d.get("modifiers", []), 
            annotations=[JavaAnnotation.fromdict(a) for a in d.get("annotations", [])],
            type_identifiers=set(d.get('type_identifiers'))
        )

class ClassFile: 
    
    package: Package 
    file: Path
    name: str 

    imports: List[Tuple[str, str]]
    classes: Dict[str, JavaClass]
    resolved_type_identifiers: Dict[str, Dict[str, JavaClass]]

    def __init__(
        self, 
        package: Package, 
        file: Path, 
        name: str, 
        classes: Dict[str, JavaClass] = None,
        imports: List[Tuple[str, str]] = None
    ):
        self.package = package 
        self.file = file 
        self.name = name 
        self.classes = classes or {}
        self.imports = imports or []
        self.resolved_type_identifiers = {}
    
    def resolve_all_class_type_identifiers(self):
        resolved = {}
        for (clsname, cls) in self.classes.items(): 
            pairs = [
                (type_id, self.resolve_type_identifier(type_id)) 
                for type_id in cls.type_identifiers
            ]
            resolved[clsname] = {
                (name, cls) for (name, cls) in pairs if cls is not None
            }
        self.resolved_type_identifiers = resolved
    
    def resolve_type_identifier(self, type_identifier: str) -> Optional[JavaClass]:
        """Turns a type identifier into a JavaClass, *or* None if we can't resolve the identifier.

        This is a method on ClassFile, because the resolution of the identifier depends on 
        both the imports in this particular file, _as well as_ the other classes that are 
        found in the same package.  

        This only returns references to other source files if we've seen them, so for example 
        "List" will return a None _even if_ we've imported java.util.List, since we don't 
        see the source of java.util.List

        Args:
            type_identifier (str): A String identifier for a Java type

        Returns:
            Optional[JavaClass]: A reference to the Java class for the type, if we've seen its source, or None otherwise.
        """
        for (pkg, name) in self.imports: 
            if name == type_identifier: 
                return self.package.resolve_fully_qualified_name(pkg, name) 
        for (_, cf) in self.package.class_files.items(): 
            if type_identifier in cf.classes: 
                return cf.classes[type_identifier]
        return None

    @staticmethod 
    def fromdict(root: Package, d: Dict[str, any]) -> 'ClassFile': 
        return ClassFile(
            package=root.get_package(d.get('package')),
            file=Path(d.get('file')),
            name=d.get('name'),
            imports=[
                (p, imp) for [p, imp] in d.get('imports')
            ],
            classes={
                n: JavaClass.fromdict(cd) for (n, cd) in d.get('classes').items()
            }
        )
    
    def asdict(self) -> Dict[str, any]: 
        return {
            "package": self.package.full_path, 
            "file": os.path.abspath(self.file.as_posix()),
            "name": self.name, 
            "imports": [
                [p, imp] for (p, imp) in self.imports
            ],
            "classes": {
                name: cls.asdict(dict_factory=custom_asdict_factory) for (name, cls) in self.classes.items()
            }
        }
    
    def as_tree(self) -> Tree: 
        t = Tree(f"FILE {self.name}")
        t.add(f"PACKAGE {self.package.full_name}")
        for (p, imp) in self.imports:
            t.add(f"IMPORT {p} {imp}")
        for (n, c) in self.classes.items(): 
            t.add(c.as_tree())
        total_res_size = sum(len(d) for d in self.resolved_type_identifiers.values())
        if total_res_size > 0: 
            rr = Tree("RESOLVED TYPE IDENTIFIERS")
            t.add(rr) 
            for (clsname, resdict) in self.resolved_type_identifiers.items(): 
                if len(resdict) > 0: 
                    rest = Tree(clsname)
                    rr.add(rest) 
                    for (type_id, cls) in resdict: 
                        rest.add(f"{type_id} -> {cls.name}")
        return t
    
    def add_class(self, clazz: JavaClass): 
        if clazz.name in self.classes: 
            raise ValueError(f"Class with name {clazz.name} already exists")
        else: 
            self.classes[clazz.name] = clazz
    
    