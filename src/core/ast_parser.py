from tree_sitter import Language, Parser, QueryCursor
from tree_sitter_language_pack import get_language

from typing import List, Optional, Any, Dict
from pathlib import Path

from loguru import logger

class Symbol:
    name: str
    type: str # function, class, method, etc.
    start_line: int
    end_line: int
    signature: Optional[str] = None
    docstring: Optional[str] = None

class ASTMetadata:
    language: str
    symbols: List[Symbol]
    dependencies: List[str] # import?
    lines: int
    raw_ast: Optional[Any] = None

class ASTParser:

    LANG_PYTHON = get_language('python')
    LANG_TYPESCRIPT = get_language('typescript')
    LANG_JAVASCRIPT = get_language('javascript')
    LANG_CPP = get_language('cpp')
    LANG_C = get_language('c')
    LANG_RUST = get_language('rust')
    LANG_GO = get_language('go')
    LANG_TSX = get_language('tsx')

    parser: Parser

    language_map = {
        'python': LANG_PYTHON,
        'typescript': LANG_TYPESCRIPT,
        'javascript': LANG_JAVASCRIPT,
        'cpp': LANG_CPP,
        'c': LANG_C,
        'rust': LANG_RUST,
        'tsx': LANG_TSX,
    }

    def __init__(self) -> None:
        self.parser = Parser()

    def parse_file(self, path: Path, content: str) -> Optional[ASTMetadata]:
        language = self._detect_language(path)
        if not language or language not in self.language_map.keys():
            logger.debug(f"Could not find a suitable parser for file: {path}")
            return None
        try:
            self.parser = Parser()
            self.parser.language = get_language(language)
            tree = self.parser.parse(content.encode())
            symbols = self._extract_symbols(tree.root_node, language, content)
            dependencies = self._extract_dependencies(tree.root_node, language, content)

            # treesitter gives you three options for walking through an AST: DFS, Tree Cursor (large files),
            # and querying through S-expressions ()
        except Exception as e:
            pass

    def _extract_symbols(self, node: Any, language: str, content: str) -> List[Symbol]:
        symbols: List[Symbol] = []

        # name every capture 'function' for general language support
        # methods are captured under the same name; see TODO to differentiate
        query_map = {
            "python": """
            (function_definition name: (identifier) @function.name) @function
            """,

            "javascript": """
            (function_declaration name: (identifier) @function.name) @function
            (method_definition name: (property_identifier) @function.name) @function
            (variable_declarator
                name: (identifier) @function.name
                value: [(arrow_function) (function_expression)]) @function
            """,

            "typescript": """
            (function_declaration name: (identifier) @function.name) @function
            (method_definition name: (property_identifier) @function.name) @function
            (variable_declarator
                name: (identifier) @function.name
                value: [(arrow_function) (function_expression)]) @function
            """,

            "tsx": """
            (function_declaration name: (identifier) @function.name) @function
            (method_definition name: (property_identifier) @function.name) @function
            (variable_declarator
                name: (identifier) @function.name
                value: [(arrow_function) (function_expression)]) @function
            """,

            "go": """
            (function_declaration name: (identifier) @function.name) @function
            (method_declaration   name: (field_identifier) @function.name) @function
            """,

            "rust": """
            (function_item name: (identifier) @function.name) @function
            """,

            "c": """
            (function_definition
                declarator: (function_declarator
                    declarator: (identifier) @function.name)) @function
            """,

            "cpp": """
            (function_definition
                declarator: (function_declarator
                    declarator: [(identifier) (field_identifier) (qualified_identifier)] @function.name)) @function
            """,
        }

        query = self.language_map[language].query(query_map[language])
        captures = QueryCursor(query).captures(node)

        def_nodes = captures.get("function", [])
        name_nodes = captures.get("function.name", [])
        name_by_start = {n.start_byte: n for n in name_nodes}

        src = content.encode()
        for def_node in def_nodes:
            name_node = next(
                (nn for s, nn in name_by_start.items()
                 if def_node.start_byte <= s < def_node.end_byte),
                None,
            )
            sym = Symbol()
            sym.name = name_node.text.decode() if name_node else "<anonymous>"
            sym.type = "function"
            sym.start_line = def_node.start_point[0]
            sym.end_line = def_node.end_point[0]
            chunk = src[def_node.start_byte:def_node.end_byte].decode(errors="replace")
            sym.signature = chunk.splitlines()[0] if chunk else ""
            sym.docstring = None
            symbols.append(sym)

        return symbols

    # use tree sitter S-expressions to find all imports
    # TODO determine outbound function calls / jumps
    def _extract_dependencies(self, node: Any, language: str, content: str) -> List[str]:
        dependencies: List[str] = []

        # query syntax: https://tree-sitter.github.io/tree-sitter/using-parsers/queries/1-syntax.html
        # grammar object name lookup / reference: https://tree-sitter.github.io/tree-sitter/7-playground.html?highlight=playground#
        # name every capture 'import' for general language support
        query_map = {
            "python": """
            (import_statement) @import
            (import_from_statement) @import
            """,

            "javascript": """
            (import_statement) @import
            """,

            "typescript": """
            (import_statement) @import
            """,

            "cpp": """
            (preproc_include) @import
            """,

            "c": """
            (preproc_include) @import
            """,

            "rust": """
            (use_declaration) @import
            """,

            "go": """
            (import_declaration) @import
            """
        }

        query = self.language_map[language].query(query_map[language])
        captures = QueryCursor(query).captures(node)

        for import_node in captures.get("import", []):
            dependencies.append(import_node.text.decode())

        return dependencies

    # use file extension to find language
    def _detect_language(self, path: Path) -> Optional[str]:
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'tsx',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.c': 'c',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
        }
        return language_map.get(path.suffix.lower())
