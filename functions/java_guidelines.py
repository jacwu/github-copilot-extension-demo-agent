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
            "max_line_length": "120 characters",
            "imports": "Use explicit import statements; avoid wildcard imports",
            "braces": "Place braces on the same line as declarations",
            "comments": "Use Javadoc for public APIs and standard comments for internal documentation",
            "package_naming": "all lowercase; follow reverse-domain naming if applicable"
        },
        "code": code
    }