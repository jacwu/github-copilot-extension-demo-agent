import requests
from typing import List, Dict, Any
import json
from functions.python_guidelines import get_python_guideline
from functions.java_guidelines import get_java_guideline

class CopilotHandler:
    def __init__(self, github_token: str):
        self.token = github_token
        self.functions = self._get_functions()
        self.function_map = {
            'get_python_guideline': get_python_guideline,
            'get_java_guideline': get_java_guideline
        }

    def _get_functions(self) -> List[Dict[str, Any]]:
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
            }
        ]

    def build_messages(self, user_name: str, selected_code: str = None) -> List[Dict[str, str]]:

        prompt = """
        Please analyze the following code:
        - If no code is provided, use no_code_selected function to remind the user
        - If it's Python code, use get_python_guideline function to analyze it
        - If it's Java code, use get_java_guideline function to analyze it
        - Based on the function results, provide detailed suggestions for improvement

        Code to analyze:
        """

        messages = []
        if selected_code:
            prompt = f"{prompt} {selected_code}"

        messages.insert(0, {
            "role": "user",
            "content": prompt
        })
        messages.insert(0, {
            "role": "system",
            "content": "You are a helpful programming assistant specialized in code analysis. You always provide code analysis based on guidelines. But don't ask any questions"
        })
        messages.insert(0, {
            "role": "system",
            "content": f"Start every response with the user's name, which is @{user_name}, and also say 'this is PythonGenie'."
        })

        # Keep only 3 messages
        if len(messages) > 3:
            messages[2:len(messages)-1] = []

        return messages

    def call_copilot_api(self, messages: List[Dict[str, str]]) -> requests.Response:
        """调用Copilot API进行代码分析"""
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            json={
                "messages": messages,
                "model": "gpt-4o",
                "tools": [{"type": "function", "function": func} for func in self.functions],
                "tool_choice": "auto"
            }
        )

        response_json = response.json()

        print("First Response:", response_json)
        """处理包含tool_calls的响应并进行后续调用"""
        if "choices" in response_json and len(response_json["choices"]) > 0:
            choice = response_json["choices"][0]
            if "message" in choice and "tool_calls" in choice["message"]:
                tool_call = choice["message"]["tool_calls"][0]
                if tool_call["type"] == "function":
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])
                    result = self.function_map[func_name](**func_args) if func_args else self.function_map[func_name]()
                    
                    messages.append(choice["message"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": str(result)
                    })
                    
                    response = requests.post(
                        "https://models.inference.ai.azure.com/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.token}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "messages": messages,
                            "model": "gpt-4o",
                            "tools": [{"type": "function", "function": func} for func in self.functions]
                        }
                    )

                    print("Second Response:", response.json())
                    # 再次调用API
                    return response.json()
        
        return None


