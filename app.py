from flask import Flask, request, Response, stream_with_context, render_template, redirect, url_for
import requests
import json
from typing import List, Dict, Any
from utils import GitHubUtils
from functions.python_guidelines import get_python_guideline
from functions.java_guidelines import get_java_guideline
from functions.no_supported_scenarios import get_no_supported_scenarios

app = Flask(__name__)

def get_functions() -> List[Dict[str, Any]]:
        """定义可用的函数"""
        return [
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
                "name": "get_no_supported_scenarios",
                "description": "获取不支持场景的指导方针",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

def build_messages(user_name: str, selected_code: str = None) -> List[Dict[str, str]]:

        prompt = """
        Please analyze the following code:
        - If it's Python code, use get_python_guideline function to analyze it
        - If it's Java code, use get_java_guideline function to analyze it
        - If the code is not Python and Java, or not provided, use get_no_supported_scenarios function to provide guidance
        - Based on the function results, provide detailed suggestions for improvement

        Code to analyze:
        """
        print("Selected Code:", selected_code)
        messages = []
        if selected_code:
            prompt = f"{prompt} {selected_code}"

        messages.insert(0, {
            "role": "user",
            "content": prompt
        })
        messages.insert(0, {
            "role": "system",
            "content": "You are a helpful programming assistant specialized in code analysis. You always show the guidelines that you refer first, then provide code analysis based on guidelines. But don't ask any questions"
        })
        messages.insert(0, {
            "role": "system",
            "content": f"Start every response with the user's name, which is @{user_name}, and also say 'this is PythonGenie'."
        })

        # Keep only 3 messages
        if len(messages) > 3:
            messages[2:len(messages)-1] = []

        print("build_messages:", messages)
        return messages

@app.route("/home", methods=["GET"])
def home():
    return render_template('index.html')

@app.route("/", methods=["POST"])
def handle_post():
    # Create GitHubUtils instance and get user
    github_utils = GitHubUtils(request)
    if not github_utils.verify_signature():
        return Response('Unauthorized: Invalid GitHub signature', status=401)
    user = github_utils.get_github_user()
    
    token = github_utils.token
    functions = get_functions()
    function_map = {
        'get_python_guideline': get_python_guideline,
        'get_java_guideline': get_java_guideline,
        'get_no_supported_scenarios': get_no_supported_scenarios
    }

    payload = request.get_json()

    print("Payload:", payload)
    copilot_references = payload["messages"][-1]["copilot_references"]
    client_selection_block = next(
        (ref for ref in copilot_references if ref["type"] == "client.selection"),
        None
    ) if copilot_references else None

    target_code_block = None
    # Build user message
    if client_selection_block and "data" in client_selection_block and "content" in client_selection_block["data"]:
        target_code_block = client_selection_block["data"]["content"]

    print("Target Code Block:", target_code_block)

    messages = build_messages(
        user_name=user,
        selected_code=target_code_block
    )
    
    response = requests.post(
        "https://models.inference.ai.azure.com/chat/completions",
        headers={
            "Authorization": f"Bearer {github_utils.token}",
            "Content-Type": "application/json"
        },
        json={
            "messages": messages,
            "model": "gpt-4o",
            "tools": [{"type": "function", "function": func} for func in functions],
            "tool_choice": "auto"
        }
    )
    response_json = response.json()
    print("First Response:", response_json)

    """处理包含tool_calls的响应并进行后续调用"""
    
    choice = response_json["choices"][0]
    
    tool_call = choice["message"]["tool_calls"][0]
    
    func_name = tool_call["function"]["name"]
    func_args = json.loads(tool_call["function"]["arguments"])
    result = function_map[func_name](**func_args) if func_args else function_map[func_name]()
    
    messages.append(choice["message"])
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": str(result)
    })
    
    print("Second messages:", messages)
    
    def generate():
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers={
                "Authorization": f"Bearer {github_utils.token}",
                "Content-Type": "application/json"
            },
            json={
                "messages": messages,
                "model": "gpt-4o",
                "tools": [{"type": "function", "function": func} for func in functions],
                "stream": True
            },
            stream=True
        )

        for chunk in response.iter_content(chunk_size=None):
            yield chunk

    return Response(stream_with_context(generate()), mimetype="application/json")

if __name__ == "__main__":
    app.run(port=8000)