"""
AST Parser Module & Optimizer.

Systematically parses incoming context to abstract syntax trees, strips out
token waste like docstrings and comments, and returns a minimized payload.
Includes generic minification fallbacks for non-Python languages.
"""
import ast
import re
import logging
from typing import Tuple, List

logger = logging.getLogger("contextshield.optimizer")
logger.setLevel(logging.INFO)

class DocstringRemover(ast.NodeTransformer):
    """
    Walks the Python AST and eliminates docstrings from modules, classes, and functions.
    """
    def _remove_docstring(self, node):
        # Safely verify if the first element is a string literal (docstring)
        if getattr(node, 'body', None) and isinstance(node.body, list) and len(node.body) > 0:
            first_expr = node.body[0]
            if isinstance(first_expr, ast.Expr):
                # Python 3.8+ compatibility for string literals
                is_str_constant = hasattr(ast, 'Constant') and isinstance(first_expr.value, ast.Constant) and isinstance(first_expr.value.value, str)
                is_legacy_str = hasattr(ast, 'Str') and isinstance(first_expr.value, getattr(ast, 'Str'))
                
                if is_str_constant or is_legacy_str:
                    node.body = node.body[1:]  # Slice out the docstring
        return node

    def visit_Module(self, node):
        self.generic_visit(node)
        return self._remove_docstring(node)

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        return self._remove_docstring(node)

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        return self._remove_docstring(node)

    def visit_AsyncFunctionDef(self, node):
        self.generic_visit(node)
        return self._remove_docstring(node)


def minify_generic_code(code_content: str) -> str:
    """
    Lightweight regex-based fallback cleaner for non-Python languages 
    (JavaScript, HTML, C++, etc.).
    """
    try:
        # 1. Remove block comments /* ... */
        cleaned = re.sub(r'/\*[\s\S]*?\*/', '', code_content)
        
        # 2. Remove inline comments starting with // (using lookbehind/spaces to avoid stripping URLs like http://)
        cleaned = re.sub(r'(?m)(^|\s+)//.*$', r'\1', cleaned)
        
        # 3. Remove standard hash-based comments #
        cleaned = re.sub(r'(?m)(^|\s+)#.*$', r'\1', cleaned)
        
        # 4. Strip trailing whitespaces per line
        lines = [line.rstrip() for line in cleaned.splitlines()]
        cleaned = "\n".join(lines)
        
        # 5. Reduce excessive consecutive empty vertical lines to a single blank line
        cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
        
        return cleaned.strip()
    except Exception as e:
        logger.error(f"Error during generic minification: {e}")
        return code_content


def optimize_python_code(code_content: str) -> str:
    """
    Uses Python's built-in AST to semantically compress Python code
    by stripping docstrings and completely unparsing comments.
    """
    try:
        # Parse into AST
        parsed = ast.parse(code_content)
        
        # Strip Docstrings
        transformer = DocstringRemover()
        modified_ast = transformer.visit(parsed)
        ast.fix_missing_locations(modified_ast)
        
        # Unparse back into string (this natively eliminates all other # comments because they aren't in the AST)
        unparsed_code = ast.unparse(modified_ast)
        
        # Clean trailing whitespaces and compact excessive blank lines
        lines = [line.rstrip() for line in unparsed_code.splitlines()]
        cleaned_code = "\n".join(lines)
        cleaned_code = re.sub(r'\n\s*\n+', '\n\n', cleaned_code)
        
        return cleaned_code.strip()
        
    except SyntaxError:
        logger.warning("SyntaxError encountered parsing Python code. Falling back to generic minifier.")
        return minify_generic_code(code_content)
    except Exception as e:
        logger.error(f"Unexpected error in optimize_python_code: {e}")
        return code_content


def optimize_context(payload_messages: List[dict]) -> Tuple[List[dict], int]:
    """
    Main integration entrypoint.
    Iterates through IDE payload messages, detects code snippets, applies appropriate
    optimizations, and measures token savings.
    
    Returns:
        tuple: (Optimized messages list, Total characters saved)
    """
    original_size = 0
    optimized_size = 0
    optimized_messages = []
    
    for msg in payload_messages:
        # Clone message to avoid mutating the original payload accidentally
        new_msg = msg.copy() if isinstance(msg, dict) else msg
        
        if isinstance(new_msg, dict) and "content" in new_msg:
            content = new_msg["content"]
            
            if isinstance(content, str):
                original_size += len(content)
                
                # Regex to extract markdown code blocks e.g. ```python ... ```
                pattern = re.compile(r'```([a-zA-Z0-9+\-.]*)\s*\n(.*?)```', re.DOTALL)
                
                def optimize_match(match):
                    lang = match.group(1).lower().strip()
                    code = match.group(2)
                    
                    if lang in ['python', 'py']:
                        optimized_code = optimize_python_code(code)
                    else:
                        optimized_code = minify_generic_code(code)
                        
                    return f"```{lang}\n{optimized_code}\n```"

                # Apply optimizations where markdown blocks exist
                try:
                    optimized_content = pattern.sub(optimize_match, content)
                except Exception as e:
                    logger.error(f"Error processing markdown code blocks: {e}")
                    optimized_content = content
                    
                new_msg["content"] = optimized_content
                optimized_size += len(optimized_content)
                
        optimized_messages.append(new_msg)
        
    saved_chars = original_size - optimized_size
    
    if original_size > 0 and saved_chars > 0:
        ratio = (saved_chars / original_size) * 100
        logger.info(f"Optimization complete! Reduced context size from {original_size} chars to {optimized_size} chars. ({ratio:.1f}% saved)")
    else:
        logger.info("Optimization complete. No reducible code blocks found.")
        
    # Prevent returning negative savings if generic minifier somehow bloated text
    return optimized_messages, max(0, saved_chars)
