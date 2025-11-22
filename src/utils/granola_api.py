#!/usr/bin/env python3
"""
Granola Cloud API Client
Fetches meeting data directly from Granola's cloud API
"""

import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
import sys

class GranolaAPIClient:
    """Client for Granola's cloud API"""

    # API endpoints (based on Granola's infrastructure)
    BASE_URL = "https://api.granola.ai"
    AUTH_FILE = Path.home() / "Library/Application Support/Granola/supabase.json"

    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.load_auth()

    def load_auth(self):
        """Load authentication tokens from local file"""
        try:
            with open(self.AUTH_FILE, 'r') as f:
                auth_data = json.load(f)

            # Parse the nested JSON strings
            cognito_tokens = json.loads(auth_data.get('cognito_tokens', '{}'))
            user_info = json.loads(auth_data.get('user_info', '{}'))
            workos_tokens = json.loads(auth_data.get('workos_tokens', '{}'))

            # Try WorkOS token first (more recent), fallback to Cognito
            self.access_token = workos_tokens.get('access_token') or cognito_tokens.get('access_token')
            self.refresh_token = workos_tokens.get('refresh_token') or cognito_tokens.get('refresh_token')
            self.user_id = user_info.get('id')

            if not self.access_token:
                raise Exception("No access token found in auth file")

            return True

        except Exception as e:
            print(f"❌ Error loading auth: {e}", file=sys.stderr)
            return False

    def _make_request(self, endpoint, method='GET', data=None):
        """Make authenticated API request"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        url = f"{self.BASE_URL}{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token expired, try to refresh
                if self.refresh_access_token():
                    # Retry with new token
                    return self._make_request(endpoint, method, data)
            raise
        except Exception as e:
            print(f"❌ API request failed: {e}", file=sys.stderr)
            raise

    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        # TODO: Implement token refresh
        # For now, just return False and user will need to re-authenticate
        return False

    def get_all_documents(self):
        """Fetch all documents (meetings) from the API"""
        try:
            # Try common API endpoints
            possible_endpoints = [
                '/v1/documents',
                '/documents',
                '/api/v1/documents',
                '/api/documents'
            ]

            for endpoint in possible_endpoints:
                try:
                    result = self._make_request(endpoint)
                    if result and isinstance(result, (list, dict)):
                        return result
                except:
                    continue

            raise Exception("Could not find valid documents endpoint")

        except Exception as e:
            print(f"❌ Error fetching documents: {e}", file=sys.stderr)
            return None

    def get_document(self, doc_id):
        """Fetch a single document with full details"""
        try:
            possible_endpoints = [
                f'/v1/documents/{doc_id}',
                f'/documents/{doc_id}',
                f'/api/v1/documents/{doc_id}',
                f'/api/documents/{doc_id}'
            ]

            for endpoint in possible_endpoints:
                try:
                    result = self._make_request(endpoint)
                    if result:
                        return result
                except:
                    continue

            raise Exception(f"Could not fetch document {doc_id}")

        except Exception as e:
            print(f"❌ Error fetching document {doc_id}: {e}", file=sys.stderr)
            return None

    def test_connection(self):
        """Test if API connection and authentication work"""
        print("🔍 Testing Granola API connection...")
        print(f"   User ID: {self.user_id}")
        print(f"   Token loaded: {'Yes' if self.access_token else 'No'}")

        # Try to fetch documents
        try:
            docs = self.get_all_documents()
            if docs:
                print(f"✅ API connection successful!")
                if isinstance(docs, list):
                    print(f"   Found {len(docs)} documents")
                elif isinstance(docs, dict):
                    print(f"   Response: {list(docs.keys())}")
                return True
            else:
                print("❌ API returned no data")
                return False
        except Exception as e:
            print(f"❌ API test failed: {e}")
            return False


def main():
    """Test the API client"""
    client = GranolaAPIClient()
    client.test_connection()


if __name__ == "__main__":
    main()
