from flask import Flask, request, jsonify
from scraper import scrape_linkedin_profile
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    """Root endpoint - shows API is running"""
    return jsonify({
        "status": "ok",
        "message": "LinkedIn Scraper API is running on Render",
        "service": "rnm",
        "endpoints": {
            "/health": "GET - Health check",
            "/scrape": "POST - Scrape LinkedIn profile",
            "/test-env": "GET - Test environment variables"
        }
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/test-env')
def test_env():
    """Test if environment variables are loaded"""
    return jsonify({
        "BROWSERBASE_API_KEY_exists": bool(os.getenv('BROWSERBASE_API_KEY')),
        "BROWSERBASE_PROJECT_ID_exists": bool(os.getenv('BROWSERBASE_PROJECT_ID')),
        "AGENTQL_API_KEY_exists": bool(os.getenv('AGENTQL_API_KEY')),
        "LINKEDIN_EMAIL_exists": bool(os.getenv('LINKEDIN_EMAIL')),
        "LINKEDIN_PASSWORD_exists": bool(os.getenv('LINKEDIN_PASSWORD')),
        "LINKEDIN_COOKIES_BASE64_exists": bool(os.getenv('LINKEDIN_COOKIES_BASE64')),
        "BROWSERBASE_API_KEY_length": len(os.getenv('BROWSERBASE_API_KEY', '')),
        "BROWSERBASE_PROJECT_ID_length": len(os.getenv('BROWSERBASE_PROJECT_ID', ''))
    }), 200

@app.route('/scrape', methods=['POST'])
def scrape():
    """
    API endpoint to scrape LinkedIn profiles
    Expected JSON body:
    {
        "url": "https://www.linkedin.com/in/johndoe"
    }
    OR
    {
        "profile_url": "https://www.linkedin.com/in/johndoe"
    }
    """
    try:
        data = request.get_json()
        
        # Accept both 'url' and 'profile_url'
        profile_url = data.get('url') or data.get('profile_url')
        
        if not profile_url:
            return jsonify({
                "success": False,
                "error": "Missing 'url' or 'profile_url' in request body",
                "example": {
                    "url": "https://www.linkedin.com/in/williamhgates"
                }
            }), 400
        
        # Scrape the profile
        print(f"🚀 Starting scrape for: {profile_url}")
        result = scrape_linkedin_profile(profile_url)
        
        return jsonify({
            "success": True,
            "data": result,
            "profile_url": profile_url
        }), 200
        
    except Exception as e:
        print(f"❌ Error scraping profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "profile_url": profile_url if 'profile_url' in locals() else None
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)