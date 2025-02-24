from typing import Dict

def get_python_guideline(code: str) -> dict:
    return {
        "language": "Python",
        "guidelines": {
            "variable_naming": "snake_case",
            "class_naming": "PascalCase  # as per PEP8, class names should use CapWords",
            "constant_naming": "UPPERCASE_WITH_UNDERSCORES",
            "function_naming": "snake_case",
            "max_line_length": "79 characters"
        },
        "code": code
    }