from flask import Flask, request, Response, stream_with_context, render_template, redirect, url_for
import requests
from utils import GitHubUtils

app = Flask(__name__)

@app.route("/preauthorization", methods=["GET"])
def preauthorization():
    headers = dict(request.headers)
    return render_template('preauthorization.html', headers=headers)

@app.route("/home", methods=["GET"])
def home():
    headers = dict(request.headers)
    return render_template('index.html', headers=headers)

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


    prompt = """
    Objective
    ####
    - Check the following code is Python or not.
    - If not, let the user know you only work on Python.
    - If it is Python, clarify whether the code meets the code guideline
    - If there is some code which doesn't meet the guideline, provide a suggestion to fix it.

    Code guideline
    ####
    - Variable and Function Names should use lowercase letters with words separated by underscores (snake_case).
    - Class Names should use capitalized words without underscores (CamelCase).
    - Constant Names should use all uppercase letters with words separated by underscores.

    Code block
    ####
    """
    # Build user message
    if client_selection_block and "data" in client_selection_block and "content" in client_selection_block["data"]:
        content = client_selection_block["data"]["content"]
        user_message = f"{prompt} {content}"
        print("User Message:", user_message)
    else:
        user_message = "replay to ask the user select code to verify"
    
    # Build message list
    messages = []
    messages.insert(0, {
        "role": "user",
        "content": user_message
    })
    messages.insert(0, {
        "role": "system",
        "content": "You are a helpful python programming assistant."
    })
    messages.insert(0, {
        "role": "system",
        "content": f"Start every response with the user's name, which is @{user}, and also say 'this is PythonGenie'."
    })

    # Keep only 3 messages
    if len(messages) > 3:
        messages[2:len(messages)-1] = []
    
    print("Messages:", messages)

    # Call Copilot API
    def generate():
        response = requests.post(
            "https://api.githubcopilot.com/chat/completions",
            headers={
                "Authorization": f"Bearer {github_utils.token}",
                "Content-Type": "application/json"
            },
            json={"messages": messages, "stream": True},
            stream=True
        )
        for chunk in response.iter_content(chunk_size=None):
            yield chunk

    return Response(stream_with_context(generate()), mimetype='application/json')

if __name__ == "__main__":
    app.run(port=8000)