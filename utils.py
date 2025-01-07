import requests

def get_github_user(token):
    # GitHub API endpoint
    url = "https://api.github.com/user"
    
    # Set request headers with authentication token
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # Send GET request
        response = requests.get(url, headers=headers)
        
        # Check response status
        if response.status_code == 200:
            user_data = response.json()
            return {
                "name": user_data.get("name"),
                "login": user_data.get("login"),
                "email": user_data.get("email")
            }
        else:
            return f"Error: {response.status_code} - {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"
