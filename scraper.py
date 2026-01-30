import os
import json
import base64
from playwright.sync_api import sync_playwright
import agentql

# BrowserBase configuration (optional - for remote browser)
BROWSERBASE_API_KEY = os.getenv('BROWSERBASE_API_KEY', '')
BROWSERBASE_PROJECT_ID = os.getenv('BROWSERBASE_PROJECT_ID', '')

def scrape_linkedin_profile(profile_url):
    """Scrape LinkedIn profile using AgentQL with BrowserBase support"""
    
    # Get credentials from environment
    agentql_api_key = os.getenv('AGENTQL_API_KEY')
    linkedin_email = os.getenv('LINKEDIN_EMAIL')
    linkedin_password = os.getenv('LINKEDIN_PASSWORD')
    cookies_base64 = os.getenv('LINKEDIN_COOKIES_BASE64')
    
    if not agentql_api_key:
        raise Exception("AGENTQL_API_KEY not found in environment variables")
    
    # Configure AgentQL
    agentql.configure(api_key=agentql_api_key)
    
    with sync_playwright() as p:
        # Choose browser: BrowserBase (remote) or local Chromium
        if BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID:
            print("🌐 Using BrowserBase (remote browser)")
            browser = p.chromium.connect_over_cdp(
                f"wss://connect.browserbase.com?apiKey={BROWSERBASE_API_KEY}&projectId={BROWSERBASE_PROJECT_ID}"
            )
            context = browser.contexts[0]
            page = agentql.wrap(context.pages[0])
        else:
            print("💻 Using local Chromium")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            context = browser.new_context()
            page = agentql.wrap(context.new_page())
        
        try:
            # Load cookies if available
            if cookies_base64:
                try:
                    cookies_json = base64.b64decode(cookies_base64).decode('utf-8')
                    cookies = json.loads(cookies_json)
                    context.add_cookies(cookies)
                    print("✅ Loaded cookies from environment")
                except Exception as e:
                    print(f"⚠️ Failed to load cookies: {str(e)}")
            
            # Navigate to profile
            print(f"🌐 Navigating to: {profile_url}")
            page.goto(profile_url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(3000)
            
            # Check if login is required
            if 'authwall' in page.url or 'login' in page.url:
                print("🔐 Login required, attempting to login...")
                
                if not linkedin_email or not linkedin_password:
                    raise Exception("LinkedIn credentials not found in environment")
                
                # Navigate to login page
                page.goto('https://www.linkedin.com/login', wait_until='networkidle')
                page.wait_for_timeout(2000)
                
                # Fill login form
                print("📝 Filling login credentials...")
                page.fill('input[name="session_key"]', linkedin_email)
                page.fill('input[name="session_password"]', linkedin_password)
                
                # Click login button
                print("🔑 Clicking login button...")
                page.click('button[type="submit"]')
                page.wait_for_timeout(5000)
                
                # Handle potential security check
                if 'checkpoint' in page.url or 'challenge' in page.url:
                    print("⚠️ Security checkpoint detected - may need manual verification")
                    # Wait a bit longer for manual intervention if needed
                    page.wait_for_timeout(10000)
                
                # Navigate to profile again after login
                print(f"🔄 Navigating to profile after login: {profile_url}")
                page.goto(profile_url, wait_until='networkidle', timeout=60000)
                page.wait_for_timeout(3000)
            
            # Define AgentQL query for LinkedIn profile data
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
                    description
                }
                education[] {
                    school
                    degree
                    field
                    dates
                }
                skills[]
            }
            """
            
            # Extract data using AgentQL
            print("🔍 Extracting profile data with AgentQL...")
            response = page.query_data(PROFILE_QUERY)
            
            print("✅ Profile scraped successfully!")
            return response
            
        except Exception as e:
            print(f"❌ Error during scraping: {str(e)}")
            # Take screenshot for debugging (if not using BrowserBase)
            if not BROWSERBASE_API_KEY:
                try:
                    page.screenshot(path="error_screenshot.png")
                    print("📸 Error screenshot saved")
                except:
                    pass
            raise e
            
        finally:
            # Cleanup
            try:
                if BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID:
                    # BrowserBase handles cleanup automatically
                    pass
                else:
                    context.close()
                    browser.close()
                print("🧹 Browser cleanup complete")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {str(e)}")


# Test function for local development
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test URL
    test_url = "https://www.linkedin.com/in/williamhgates"
    
    print("=" * 80)
    print("🚀 Starting LinkedIn Profile Scraper Test")
    print("=" * 80)
    
    try:
        result = scrape_linkedin_profile(test_url)
        print("\n" + "=" * 80)
        print("📊 SCRAPED DATA:")
        print("=" * 80)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")