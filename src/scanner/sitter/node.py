from itertools import groupby
from typing import Generic, Iterable, List, Dict, TypeVar, Optional, Generator
from functools import reduce 
from rich.tree import Tree

def create_tree(d: Dict[str, any]) -> Tree: 

    t = d.get("_type") 
    c = d.get("_children") 
    v = d.get("_value", '') 
    
    if c is None: 
        return Tree(f"{t} {v}") 
    else: 
        t = Tree(f"{t}") 
        for cc in c: 
            t.add(create_tree(cc)) 
        return t


N = TypeVar("N")
class QuerySet(Generic[N], Iterable[N]): 
    """QuerySet is a transformable list of items; this usually is a QuerySet[TypedNode] 
    
    generally, if n is a QuerySet[TypedNode], then
      n.foo 
    
    returns a QuerySet of the result of getting the 'foo' attribute on every element of n 

    i.e. 
      n = QuerySet([{'foo': 3}, {'foo': 10}])
      list(n.foo) == [3, 10] 
    """
    
    __elements: List[N]

    def __init__(self, elmts: List[N] = []): 
        self.__elements = [x for x in elmts]
        for e in self.__elements: 
            if isinstance(e, QuerySet): 
                raise ValueError()
    
    def first(self) -> Optional[N]: 
        if len(self.__elements) > 0: 
            return self.__elements[0]
        else: 
            return None
    
    def __getitem__(self, idx): 
        return self.__elements[idx]
    
    def __iter__(self): 
        return iter(self.__elements)
    
    def __len__(self): 
        return len(self.__elements)

    def __repr__(self): 
        return f"QuerySet({self.__elements})"
    
    def __add__(self, qset: 'QuerySet[N]' | N) -> 'QuerySet[N]':
        if isinstance(qset, QuerySet): 
            return QuerySet(self.__elements + qset.__elements)
        else: 
            return QuerySet(self.__elements + [qset])
    
    def __getattr__(self, attr): 
        if len(self.__elements) == 1: 
            return getattr(self.__elements[0], attr) 
        else: 
            return reduce(lambda a, b: a + b, [
                getattr(e, attr) for e in self.__elements
            ], QuerySet())
        

class TypedNode: 
    """TypedNode wraps the lightweight tree-of-dicts AST and provides easy querying and searching
    """
    
    _raw: Dict[str, any] 
    _parent: 'TypedNode' = None
    
    def __init__(self, raw: Dict[str, any], parent: 'TypedNode' = None): 
        self._raw = raw
        self._parent = parent 
    
    @property 
    def is_terminal(self) -> bool: 
        return self._raw.get('_children') is None
    
    @property
    def value(self) -> str: 
        return self._raw.get('_value')
    
    @property
    def type(self) -> str: 
        return self._raw.get('_type')
    
    @property
    def offset_start(self) -> int: return self._raw.get('_start')

    @property
    def offset_end(self) -> int: return self._raw.get('_end')

    @property
    def children(self) -> List['TypedNode']:
        return [TypedNode(n, self) for n in self._raw.get('_children', [])]
    
    def astree(self) -> Tree: 
        return create_tree(self._raw)
    
    def get_text(self, bs: bytes) -> str: 
        return bs[self._raw.get('_start'):self._raw.get('_end')].decode('UTF-8')
    
    def __repr__(self) -> str: 
        if self.is_terminal: 
            return f"{self.type} {self.value}"
        else: 
            ts = groupby(self.children, key=lambda t: t.type)
            counts = [(typename, len(list(values))) for (typename, values) in ts] 
            count_str = ", ".join(f"{n}:{c}" for (n, c) in counts)
            return f"{self.type} ({count_str})"
    
    @staticmethod 
    def matches_raw_dict(d: Dict[str, any], term: str) -> bool: 
        return d.get('_type', '').find(term) != -1
    
    def matches(self, term: str) -> bool: 
        return TypedNode.matches_raw_dict(self._raw, term)
    
    def get(self, attr_name: str) -> QuerySet['TypedNode']:
        children = [
            x for x in self._raw.get('_children', []) if x.get('_type') == attr_name
        ]
        return QuerySet([TypedNode(c, self) for c in children])
    
    def query(self, query_term: str) -> Generator['TypedNode', None, None]: 
        if TypedNode.matches_raw_dict(self._raw, query_term): 
            yield self 
        else: 
            for c in self.children:
                yield from c.query(query_term)

    def search(self, search_term: str) -> QuerySet['TypedNode']: 
        return QuerySet(list(self.query(search_term)))
    
    def find(self, search_term: str) -> QuerySet['TypedNode']:
        children = [
            x for x in self._raw.get('_children', []) if TypedNode.matches_raw_dict(x, search_term)
        ]
        return QuerySet([TypedNode(c, self) for c in children])
    
    def nearest_enclosing(self, search_term: str) -> 'TypedNode': 
        p = self._parent 
        while p is not None: 
            if p.matches(search_term): 
                break
            p = p._parent 
        return p
    
    def __getattr__(self, attr: str): 
        return self.find(attr)

