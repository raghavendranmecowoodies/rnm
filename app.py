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
        "endpoints": {
            "/health": "GET - Health check",
            "/scrape": "POST - Scrape LinkedIn profile"
        }
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/scrape', methods=['POST'])
def scrape():
    """
    API endpoint to scrape LinkedIn profiles
    Expected JSON body:
    {
        "profile_url": "https://www.linkedin.com/in/johndoe"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'profile_url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'profile_url' in request body"
            }), 400
        
        profile_url = data['profile_url']
        
        # Scrape the profile
        result = scrape_linkedin_profile(profile_url)
        
        return jsonify({
            "success": True,
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)