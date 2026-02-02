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
    
    browser = None
    context = None
    page = None
    
    with sync_playwright() as p:
        try:
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
            page.goto(profile_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)
            
            # Check if login is required
            if 'authwall' in page.url or 'login' in page.url or 'checkpoint' in page.url:
                print("🔐 Login wall detected - cookies may be expired")
                
                if not linkedin_email or not linkedin_password:
                    raise Exception("LinkedIn credentials not found. Cookies expired and no credentials provided.")
                
                print("🔄 Attempting login...")
                
                # Go to login page
                page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(3000)
                
                # Wait for and fill email field - try multiple selectors
                print("📝 Looking for email field...")
                try:
                    page.wait_for_selector('input#username', state='visible', timeout=10000)
                    page.fill('input#username:visible', linkedin_email)
                    print("✅ Email filled (using #username)")
                except:
                    try:
                        page.wait_for_selector('input[name="session_key"]:visible', timeout=5000)
                        page.fill('input[name="session_key"]:visible', linkedin_email)
                        print("✅ Email filled (using name=session_key)")
                    except:
                        try:
                            page.wait_for_selector('input[type="email"]:visible', timeout=5000)
                            page.fill('input[type="email"]:visible', linkedin_email)
                            print("✅ Email filled (using type=email)")
                        except Exception as e:
                            print(f"❌ Could not find email field: {str(e)}")
                            raise Exception("Login form not found - email field")
                
                # Wait for and fill password field
                print("🔑 Looking for password field...")
                try:
                    page.wait_for_selector('input#password', state='visible', timeout=10000)
                    page.fill('input#password:visible', linkedin_password)
                    print("✅ Password filled (using #password)")
                except:
                    try:
                        page.wait_for_selector('input[name="session_password"]:visible', timeout=5000)
                        page.fill('input[name="session_password"]:visible', linkedin_password)
                        print("✅ Password filled (using name=session_password)")
                    except:
                        try:
                            page.wait_for_selector('input[type="password"]:visible', timeout=5000)
                            page.fill('input[type="password"]:visible', linkedin_password)
                            print("✅ Password filled (using type=password)")
                        except Exception as e:
                            print(f"❌ Could not find password field: {str(e)}")
                            raise Exception("Login form not found - password field")
                
                # Click login button
                print("🚀 Clicking login button...")
                try:
                    page.wait_for_selector('button[type="submit"]', state='visible', timeout=5000)
                    page.click('button[type="submit"]')
                    print("✅ Clicked submit button")
                except:
                    try:
                        page.click('button:has-text("Sign in")')
                        print("✅ Clicked 'Sign in' button")
                    except Exception as e:
                        print(f"❌ Could not find login button: {str(e)}")
                        raise Exception("Login button not found")
                
                print("⏳ Waiting for login to complete...")
                page.wait_for_timeout(8000)
                
                # Check if verification is needed
                current_url = page.url
                print(f"📍 Current URL after login: {current_url}")
                
                if 'checkpoint' in current_url or 'challenge' in current_url:
                    print("⚠️ LinkedIn security checkpoint detected!")
                    print("⚠️ Manual verification may be required")
                    raise Exception("LinkedIn security checkpoint - please verify your account manually and update cookies")
                
                if 'feed' in current_url or 'mynetwork' in current_url:
                    print("✅ Login successful!")
                elif 'login' in current_url:
                    print("❌ Login failed - still on login page")
                    raise Exception("Login failed - credentials may be incorrect")
                
                # Navigate to profile again
                print(f"🔄 Navigating to profile: {profile_url}")
                page.goto(profile_url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(5000)
            
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
                }
                education[] {
                    school
                    degree
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
            import traceback
            traceback.print_exc()
            raise e
            
        finally:
            # Cleanup
            print("🧹 Starting cleanup...")
            try:
                if BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID:
                    # For BrowserBase, just disconnect
                    print("🔌 Disconnecting from BrowserBase")
                    if browser:
                        try:
                            browser.close()
                            print("✅ BrowserBase disconnected")
                        except Exception as e:
                            print(f"⚠️ BrowserBase disconnect warning: {str(e)}")
                else:
                    # For local browser, close everything
                    print("🔒 Closing local browser")
                    if context:
                        try:
                            context.close()
                            print("✅ Context closed")
                        except Exception as e:
                            print(f"⚠️ Context close warning: {str(e)}")
                    if browser:
                        try:
                            browser.close()
                            print("✅ Browser closed")
                        except Exception as e:
                            print(f"⚠️ Browser close warning: {str(e)}")
                
                print("✅ Cleanup complete")
            except Exception as e:
                print(f"⚠️ Cleanup error: {str(e)}")


# Test function for local development
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
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