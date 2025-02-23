from base64 import b64decode
import os
import requests
from ecdsa import VerifyingKey, BadSignatureError, NIST256p
from ecdsa.util import sigdecode_der
from hashlib import sha256

class GitHubUtils:
    def __init__(self, req: requests.Request):
        self.token = req.headers.get("X-GitHub-Token")
        self.key_identifier = req.headers.get('X-Github-Public-Key-Identifier')
        self.github_signature = req.headers.get('X-Github-Public-Key-Signature')
        self.raw_body = req.data

    """
    Follow https://docs.github.com/en/copilot/building-copilot-extensions/building-a-copilot-agent-for-your-copilot-extension/configuring-your-copilot-agent-to-communicate-with-github#verifying-that-payloads-are-coming-from-github
    Verifies the GitHub signature using the public key from GitHub.
    Returns:
        bool: True if the signature is valid, False otherwise.
    Raises:
        ValueError: If the public key is not found.
    Notes:
        - The method requires `self.token`, `self.key_identifier`, and `self.github_signature` to be set.
        - It fetches the public keys from the GitHub API and uses the key corresponding to `self.key_identifier`.
        - The signature is verified using ECDSA with SHA-256.
    """
    def verify_signature(self):
        # if token, key_identifier, github_signature is not set, return false
        if not self.token or not self.key_identifier or not self.github_signature:
            return False
        
        # get the public keys from github api
        GITHUB_KEYS_URI = "https://api.github.com/meta/public_keys"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        key_resp = requests.get(GITHUB_KEYS_URI, headers=headers, timeout=5).json()
        for k in key_resp["public_keys"]:
            if k["key_identifier"] == self.key_identifier:
                public_key = k["key"]
                break
        else:
            raise ValueError("Public key not found")

        ecdsa_verifier = VerifyingKey.from_pem(string=public_key, hashfunc=sha256)
        try:
            raw_sig = b64decode(self.github_signature)
            ecdsa_verifier.verify(
                signature=raw_sig, data=self.raw_body, sigdecode=sigdecode_der
            )
            return True
        except (BadSignatureError, ValueError):
            return False
        
    """
    Fetches the GitHub username of the authenticated user using the GitHub API.
    Returns:
        str: The GitHub username if the request is successful and the user is authenticated.
        None: If the request fails or the user is not authenticated.
    """
    def get_github_user(self):
        
        # GitHub API endpoint
        url = f"https://api.github.com/user"
        
        # Set request headers with authentication token
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            # Send GET request
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get("login")
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None
