import ast
import os
from pathlib import Path

def find_backslash_in_fstrings(dir_path):
    print(f"Scanning {dir_path} for Python 3.11 incompatible f-strings...")
    for root, dirs, files in os.walk(dir_path):
        # Skip directories we don't care about
        if any(p in Path(root).parts for p in [".venv", "venv", ".git", "node_modules", "__pycache__"]):
            continue
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = Path(root) / file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # We want to walk the AST of the file
                tree = ast.parse(content, filename=str(file_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.JoinedStr):
                        # This is an f-string. Let's look at its formatted values.
                        for value in node.values:
                            if isinstance(value, ast.FormattedValue):
                                # Get the unparsed expression inside the formatted value
                                expr_src = ast.unparse(value.value)
                                if "\\" in expr_src:
                                    print(f"FOUND: Backslash in f-string expression in {file_path}")
                                    # Print the line number if available
                                    lineno = getattr(value, "lineno", "unknown")
                                    print(f"  Line {lineno}: {{{expr_src}}}")
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")

if __name__ == "__main__":
    find_backslash_in_fstrings("c:/Rakshastra")
