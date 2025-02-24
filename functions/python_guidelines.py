from typing import Dict

def get_python_guideline(code: str) -> dict:
    return {
        "language": "Python",
        "guidelines": {
            "variable_naming": "snake_case",
            "class_naming": "PascalCase  # as per PEP8, class names should use CapWords",
            "constant_naming": "UPPERCASE_WITH_UNDERSCORES",
            "function_naming": "snake_case",
            "indentation": "4 spaces",
            "max_line_length": "79 characters",
            "imports": "Import each module on a separate line; avoid wildcard imports",
            "docstrings": "Use triple quotes and follow PEP257 guidelines",
            "whitespace": "Remove trailing whitespace and separate code blocks logically",
            "comments": "Write complete sentences with a capital letter; inline comments use '# '",
            "type_annotations": "Use type hints for functions and variables"
        },
        "code": code
    }