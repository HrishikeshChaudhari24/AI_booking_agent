#!/usr/bin/env python3
"""
Helper script to extract Google OAuth credentials from credentials.json
and set them up for the AI Booking Agent.
"""

import json
import os
import sys

def extract_credentials():
    """Extract credentials from credentials.json file"""
    
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json file not found!")
        print("\nPlease:")
        print("1. Download credentials.json from Google Cloud Console")
        print("2. Place it in the project root directory")
        print("3. Run this script again")
        return False
    
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
        
        # Extract web credentials
        if 'web' in creds:
            web_creds = creds['web']
            client_id = web_creds.get('client_id')
            client_secret = web_creds.get('client_secret')
            
            if not client_id or not client_secret:
                print("❌ Invalid credentials.json format!")
                return False
            
            print("✅ Credentials extracted successfully!")
            print("\nAdd these to your Replit Secrets:")
            print(f"GOOGLE_CLIENT_ID = {client_id}")
            print(f"GOOGLE_CLIENT_SECRET = {client_secret}")
            
            # Get current Replit URL
            replit_url = os.environ.get('REPLIT_DEV_DOMAIN', 'your-replit-url.replit.dev')
            redirect_uri = f"https://{replit_url}/auth/callback"
            
            print(f"\n📝 Update your Google Cloud Console OAuth settings:")
            print(f"Add this redirect URI: {redirect_uri}")
            
            return True
            
        else:
            print("❌ credentials.json doesn't contain 'web' credentials!")
            print("Make sure you downloaded the correct OAuth 2.0 Client credentials file.")
            return False
            
    except json.JSONDecodeError:
        print("❌ Invalid JSON format in credentials.json!")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False

if __name__ == "__main__":
    print("🔧 AI Booking Agent - Credential Setup")
    print("=" * 40)
    
    if extract_credentials():
        print("\n🚀 Next steps:")
        print("1. Add the credentials to Replit Secrets")
        print("2. Update your Google Cloud Console redirect URI")
        print("3. Restart the application")
    else:
        print("\n💡 Need help?")
        print("Check the README.md for detailed setup instructions.")