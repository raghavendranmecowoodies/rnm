import subprocess
import sys
import os

# Auto-install Playwright browsers if not found
def ensure_playwright_installed():
    try:
        from playwright.sync_api import sync_playwright
        # Try to get browser path
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
            except Exception:
                # Browser not found, install it
                print("Playwright browser not found. Installing...")
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Error ensuring Playwright: {e}")

# Run at import time
ensure_playwright_installed()

# Now import the rest
import json
import base64
from agentql.ext.playwright.sync_api import Page, sync_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def save_cookies_from_manual_login():
    """
    Opens browser for manual LinkedIn login and saves cookies
    """
    print("\n" + "="*80)
    print("MANUAL LOGIN - Please follow these steps:")
    print("="*80)
    print("1. Browser will open automatically")
    print("2. Log in to LinkedIn manually")
    print("3. Wait for the home feed to load completely")
    print("4. Come back here and press ENTER")
    print("="*80 + "\n")
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Go to LinkedIn
        page.goto("https://www.linkedin.com/login")
        
        # Wait for user to login manually
        input("Press ENTER after you've logged in and see your LinkedIn feed...")
        
        # Save cookies
        cookies = context.cookies()
        with open('linkedin_cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print("\n✅ Cookies saved to linkedin_cookies.json")
        
        browser.close()
        
    return cookies

def scrape_linkedin_profile(url, fields=None, linkedin_email=None, linkedin_password=None):
    """
    Scrape LinkedIn profile using AgentQL
    
    Args:
        url: LinkedIn profile URL
        fields: Optional dict of field descriptions to extract
        linkedin_email: LinkedIn login email
        linkedin_password: LinkedIn login password
    
    Returns:
        dict: Scraped profile data
    """
    try:
        # Load cookies if available
        cookies = []
        cookies_base64 = os.getenv('LINKEDIN_COOKIES_BASE64')
        
        if cookies_base64:
            try:
                cookies_json = base64.b64decode(cookies_base64).decode('utf-8')
                cookies = json.loads(cookies_json)
                print("✅ Loaded cookies from environment variable")
            except Exception as e:
                print(f"⚠️ Failed to load cookies from env: {e}")
        
        # If no cookies from env, try loading from file
        if not cookies:
            try:
                with open('linkedin_cookies.json', 'r') as f:
                    cookies = json.load(f)
                print("✅ Loaded cookies from file")
            except FileNotFoundError:
                print("⚠️ No cookies found - will need to login")
        
        # Start Playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = browser.new_context()
            
            # Add cookies if available
            if cookies:
                context.add_cookies(cookies)
                print("✅ Cookies added to browser context")
            
            page = context.new_page()
            
            # Navigate to profile
            print(f"📄 Navigating to: {url}")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Check if login is required
            current_url = page.url
            if 'linkedin.com/login' in current_url or 'linkedin.com/checkpoint' in current_url:
                print("⚠️ Login required - cookies may have expired")
                browser.close()
                return {
                    "success": False,
                    "error": "Login required. Please update your LinkedIn cookies.",
                    "url": url
                }
            
            # Wait for profile to load
            page.wait_for_load_state('networkidle')
            
            # Define default AgentQL query if no custom fields provided
            if not fields:
                PROFILE_QUERY = """
                {
                    name
                    headline
                    location
                    about
                    experience[] {
                        title
                        company
                        duration
                    }
                }
                """
            else:
                # Build custom query from fields
                field_queries = []
                for field_name, field_desc in fields.items():
                    field_queries.append(f"{field_name}")
                PROFILE_QUERY = "{\n    " + "\n    ".join(field_queries) + "\n}"
            
            print(f"🔍 Extracting data with query:\n{PROFILE_QUERY}")
            
            # Use AgentQL to extract data
            try:
                response = page.query_data(PROFILE_QUERY)
                print("✅ Data extracted successfully")
            except Exception as e:
                print(f"❌ AgentQL extraction failed: {e}")
                browser.close()
                return {
                    "success": False,
                    "error": f"Failed to extract data: {str(e)}",
                    "url": url
                }
            
            browser.close()
            
            return {
                "success": True,
                "url": url,
                "data": response
            }
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "url": url
        }

# Run this once to save cookies
if __name__ == "__main__":
    print("=== LinkedIn Cookie Setup ===")
    print("This will open a browser for you to login manually")
    save_cookies_from_manual_login()