from tree_sitter import Parser
from src.core.ast_parser import ASTParser

def _parse(language: str, src: str):
    parser = Parser()
    parser.language = ASTParser.language_map[language]
    return parser.parse(src.encode()).root_node

def test_extract_dependencies_python():
    src = """
    import discord

    def irrelevant():
        print('hello')
    """
    nodes = _parse('python', src)
    result = ASTParser()._extract_dependencies(nodes, 'python', src)
    assert result == ["import discord"]

def test_extract_symbols_python():
    src = "def foo():\n    return 1\n\nclass Bar:\n    def baz(self):\n        return 2\n"
    nodes = _parse('python', src)
    result = ASTParser()._extract_symbols(nodes, 'python', src)

    names = sorted(s.name for s in result)
    assert names == ["baz", "foo"]
    assert all(s.type == "function" for s in result)

    foo = next(s for s in result if s.name == "foo")
    assert foo.start_line == 0
    assert foo.signature == "def foo():"

def test_extract_dependencies_cpp():
    src = """
    #include <bits/stdc++.h>
    #include <stringstream>
    using namespace std;
    int main() {
        return 0;
    }
    """
    nodes = _parse('cpp', src)
    result = ASTParser()._extract_dependencies(nodes, 'cpp', src)
    assert result == ['#include <bits/stdc++.h>\n', '#include <stringstream>\n']
