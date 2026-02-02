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
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
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
                print("🔐 Login wall detected - attempting login with JavaScript injection")
                
                if not linkedin_email or not linkedin_password:
                    raise Exception("LinkedIn credentials not found")
                
                # Go to login page
                page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(3000)
                
                # Use JavaScript to fill the form (works even with hidden fields)
                print("📝 Filling login form with JavaScript...")
                try:
                    page.evaluate(f'''
                        // Find and fill email
                        const emailSelectors = [
                            'input#username',
                            'input[name="session_key"]',
                            'input[type="email"]',
                            'input[autocomplete="username"]'
                        ];
                        
                        let emailFilled = false;
                        for (const selector of emailSelectors) {{
                            const emailInput = document.querySelector(selector);
                            if (emailInput) {{
                                emailInput.value = "{linkedin_email}";
                                emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                emailInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                console.log('Email filled with: ' + selector);
                                emailFilled = true;
                                break;
                            }}
                        }}
                        
                        if (!emailFilled) {{
                            throw new Error('Could not find email field');
                        }}
                        
                        // Find and fill password
                        const passwordSelectors = [
                            'input#password',
                            'input[name="session_password"]',
                            'input[type="password"]'
                        ];
                        
                        let passwordFilled = false;
                        for (const selector of passwordSelectors) {{
                            const passwordInput = document.querySelector(selector);
                            if (passwordInput) {{
                                passwordInput.value = "{linkedin_password}";
                                passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                passwordInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                console.log('Password filled with: ' + selector);
                                passwordFilled = true;
                                break;
                            }}
                        }}
                        
                        if (!passwordFilled) {{
                            throw new Error('Could not find password field');
                        }}
                    ''')
                    print("✅ Form filled successfully")
                except Exception as e:
                    print(f"❌ JavaScript fill failed: {str(e)}")
                    raise Exception("Login form not found - could not fill fields")
                
                # Click login button
                print("🚀 Clicking login button...")
                try:
                    # Try multiple button selectors
                    page.evaluate('''
                        const buttonSelectors = [
                            'button[type="submit"]',
                            'button[data-litms-control-urn]',
                            'button.btn__primary--large'
                        ];
                        
                        for (const selector of buttonSelectors) {
                            const button = document.querySelector(selector);
                            if (button) {
                                button.click();
                                console.log('Button clicked: ' + selector);
                                break;
                            }
                        }
                    ''')
                    print("✅ Login button clicked")
                except Exception as e:
                    print(f"❌ Could not click button: {str(e)}")
                    raise Exception("Login button not found")
                
                print("⏳ Waiting for login to complete...")
                page.wait_for_timeout(10000)
                
                # Check login status
                current_url = page.url
                print(f"📍 Current URL: {current_url}")
                
                if 'checkpoint' in current_url or 'challenge' in current_url:
                    raise Exception("LinkedIn security checkpoint - manual verification required")
                
                if 'feed' in current_url or 'mynetwork' in current_url:
                    print("✅ Login successful!")
                elif 'login' in current_url:
                    raise Exception("Login failed - check credentials")
                
                # Navigate to profile
                print(f"🔄 Going to profile: {profile_url}")
                page.goto(profile_url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(5000)
            
            # Define AgentQL query
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
            
            # Extract data
            print("🔍 Extracting profile data...")
            response = page.query_data(PROFILE_QUERY)
            
            print("✅ Profile scraped successfully!")
            return response
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
            
        finally:
            print("🧹 Cleanup...")
            try:
                if BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID:
                    if browser:
                        browser.close()
                else:
                    if context:
                        context.close()
                    if browser:
                        browser.close()
                print("✅ Cleanup complete")
            except Exception as e:
                print(f"⚠️ Cleanup error: {str(e)}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    test_url = "https://www.linkedin.com/in/williamhgates"
    
    print("=" * 80)
    print("🚀 LinkedIn Scraper Test")
    print("=" * 80)
    
    try:
        result = scrape_linkedin_profile(test_url)
        print("\n" + "=" * 80)
        print("📊 RESULT:")
        print("=" * 80)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"\n❌ Failed: {str(e)}")