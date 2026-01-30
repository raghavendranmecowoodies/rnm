import agentql
from playwright.sync_api import sync_playwright
import json
import os

def save_cookies_from_manual_login():
    """
    Helper function to login manually and save cookies
    Run this ONCE to save your LinkedIn cookies
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("🌐 Opening LinkedIn login page...")
        print("👉 Please login manually in the browser window that opens")
        print("👉 After login, press ENTER in this terminal...")
        
        page.goto("https://www.linkedin.com/login")
        
        # Wait for user to login manually
        input("Press ENTER after you've logged in successfully...")
        
        # Save cookies
        cookies = context.cookies()
        with open('linkedin_cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print("✅ Cookies saved to linkedin_cookies.json")
        browser.close()

def scrape_linkedin_profile(url, fields_to_extract=None, linkedin_email=None, linkedin_password=None):
    """
    Scrape LinkedIn profile using AgentQL with cookie-based authentication
    """
    if not fields_to_extract:
        fields_to_extract = {
            "name": "full name of the person",
            "title": "current job title",
            "company": "current company name",
            "location": "location or city"
        }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Load saved cookies if they exist
            cookies_file = 'linkedin_cookies.json'
            if os.path.exists(cookies_file):
                print("🍪 Loading saved LinkedIn cookies...")
                with open(cookies_file, 'r') as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                print("✅ Cookies loaded")
            else:
                print("⚠️ No cookies found - you need to run save_cookies_from_manual_login() first")
                browser.close()
                return {
                    "success": False,
                    "url": url,
                    "error": "No LinkedIn cookies found. Please run the cookie setup first."
                }
            
            page = context.new_page()
            page.set_default_timeout(60000)
            
            # Navigate directly to profile (using cookies for auth)
            print(f"🌐 Navigating to profile: {url}")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(8000)
            
            # Check if we're logged in
            current_url = page.url
            current_title = page.title()
            
            print(f"📍 Current URL: {current_url}")
            print(f"📍 Page Title: {current_title}")
            
            # Take screenshot
            page.screenshot(path="profile_page.png")
            print("📸 Screenshot saved: profile_page.png")
            
            # Check if we got blocked
            if "authwall" in current_url or "login" in current_url:
                print("❌ Cookies expired or invalid - need to login again")
                browser.close()
                return {
                    "success": False,
                    "url": url,
                    "error": "Cookies expired - please run cookie setup again"
                }
            
            # Use AgentQL to extract data
            print("🤖 Extracting data with AgentQL...")
            agentql_page = agentql.wrap(page)
            
            data = agentql_page.query_data("""
            {
                name
                headline
                location
            }
            """)
            
            print(f"✅ Data extracted: {data}")
            
            page.wait_for_timeout(3000)
            browser.close()
            
            return {
                "success": True,
                "url": url,
                "page_title": current_title,
                "data": data
            }
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error: {error_details}")
        return {
            "success": False,
            "url": url,
            "error": str(e)
        }

# Run this once to save cookies
if __name__ == "__main__":
    print("=== LinkedIn Cookie Setup ===")
    print("This will open a browser for you to login manually")
    save_cookies_from_manual_login()