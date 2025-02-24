from typing import Dict

def get_java_guideline(code: str) -> dict:
    return {
        "language": "Java",
        "guidelines": {
            "variable_naming": "camelCase",
            "class_naming": "PascalCase  # as per Java conventions, class names should use UpperCamelCase",
            "constant_naming": "UPPERCASE_WITH_UNDERSCORES",
            "method_naming": "camelCase",
            "indentation": "4 spaces",
            "max_line_length": "120 characters"
        },
        "code": code
    }