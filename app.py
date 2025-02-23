from flask import Flask, request, Response, stream_with_context, render_template, redirect, url_for
import requests
import json
from utils import GitHubUtils

app = Flask(__name__)

def get_python_guideline(code: str) -> dict:
    return {
        "language": "Python",
        "guidelines": {
            "variable_naming": "snake_case",
            "class_naming": "CamelCase",
            "constant_naming": "UPPERCASE"
        },
        "code": code
    }

def get_java_guideline(code: str) -> dict:
    return {
        "language": "Java",
        "guidelines": {
            "variable_naming": "camelCase",
            "class_naming": "PascalCase",
            "constant_naming": "UPPERCASE"
        },
        "code": code
    }

def no_code_selected() -> dict:
    """提醒用户需要先选择代码"""
    return {
        "message": "Please select code first before checking."
    }

@app.route("/home", methods=["GET"])
def home():
    headers = dict(request.headers)
    return render_template('index.html')

@app.route("/", methods=["POST"])
def handle_post():
    # Create GitHubUtils instance and get user
    github_utils = GitHubUtils(request)
    user = github_utils.get_github_user()

    # Check if user is authenticated
    if not user:
        return Response('Unauthorized: Invalid GitHub token', status=401)

    # Parse request data
    payload = request.get_json()
    print("Payload:", payload)
    
    copilot_references = payload["messages"][-1]["copilot_references"]
    client_selection_block = next(
        (ref for ref in copilot_references if ref["type"] == "client.selection"),
        None
    )
    print("Client Selection Block:", client_selection_block)

    # 定义可用的函数
    functions = [
        {
            "name": "get_python_guideline",
            "description": "获取Python代码的规范指南",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要分析的Python代码"
                    }
                },
                "required": ["code"]
            }
        },
        {
            "name": "get_java_guideline",
            "description": "获取Java代码的规范指南",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要分析的Java代码"
                    }
                },
                "required": ["code"]
            }
        },
        {
            "name": "no_code_selected",
            "description": "提醒用户需要先选择代码",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    ]

    prompt = """
    Please analyze the following code:
    - If no code is provided, use no_code_selected function to remind the user
    - If it's Python code, use get_python_guideline function to analyze it
    - If it's Java code, use get_java_guideline function to analyze it
    - Based on the function results, provide detailed suggestions for improvement

    Code to analyze:
    """

    # Build user message
    if client_selection_block and "data" in client_selection_block and "content" in client_selection_block["data"]:
        content = client_selection_block["data"]["content"]
        user_message = f"{prompt} {content}"
    else:
        user_message = prompt

    # Build message list
    messages = []
    messages.insert(0, {
        "role": "user",
        "content": user_message
    })
    messages.insert(0, {
        "role": "system",
        "content": "You are a helpful programming assistant specialized in code analysis."
    })
    messages.insert(0, {
        "role": "system",
        "content": f"Start every response with the user's name, which is @{user}, and also say 'this is PythonGenie'."
    })

    # Keep only 3 messages
    if len(messages) > 3:
        messages[2:len(messages)-1] = []
    
    print("Messages:", messages)

    # 根据代码内容自动选择工具
    tool_choice = "auto"

    # 转换函数定义为tools格式
    tools = [{
        "type": "function",
        "function": func
    } for func in functions]

    # Call Copilot API with functions
    def generate():
        response = requests.post(
            "https://api.githubcopilot.com/chat/completions",
            headers={
                "Authorization": f"Bearer {github_utils.token}",
                "Content-Type": "application/json"
            },
            json={
                "messages": messages,
                "model": "gpt-4o",
                "tools": tools,
                "tool_choice": tool_choice,
                "stream": True
            },
            stream=True
        )
        for chunk in response.iter_content(chunk_size=None):
            yield chunk

    return Response(stream_with_context(generate()), mimetype='application/json')

if __name__ == "__main__":
    app.run(port=8000)