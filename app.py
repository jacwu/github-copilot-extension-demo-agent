from flask import Flask, request, Response, stream_with_context, render_template, redirect, url_for
import requests
import json
from utils import GitHubUtils
from copilot_handler import CopilotHandler

app = Flask(__name__)

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
    
    payload = request.get_json()

    print("Payload:", payload)
    copilot_references = payload["messages"][-1]["copilot_references"]
    client_selection_block = next(
        (ref for ref in copilot_references if ref["type"] == "client.selection"),
        None
    )

    target_code_block = None
    # Build user message
    if client_selection_block and "data" in client_selection_block and "content" in client_selection_block["data"]:
        target_code_block = client_selection_block["data"]["content"]

    print("Target Code Block:", target_code_block)

    copilot_handler = CopilotHandler(github_utils.token)
    messages = copilot_handler.build_messages(
        user_name=user,
        selected_code=target_code_block
    )
    
    # 调用 Copilot API
    response = copilot_handler.call_copilot_api(messages)
    response_json = json.dumps(response)

    return Response(response_json, mimetype='application/json')

if __name__ == "__main__":
    app.run(port=8000)