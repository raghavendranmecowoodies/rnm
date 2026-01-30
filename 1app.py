from flask import Flask, request, jsonify
from scraper import scrape_linkedin_profile
import os

app = Flask(__name__)

# LinkedIn credentials from environment variables
LINKEDIN_EMAIL = os.environ.get('LINKEDIN_EMAIL', '')
LINKEDIN_PASSWORD = os.environ.get('LINKEDIN_PASSWORD', '')

@app.route('/scrape', methods=['POST'])
def scrape():
    """
    API endpoint to scrape LinkedIn profiles
    
    Expected JSON body:
    {
        "url": "https://www.linkedin.com/in/johndoe",
        "fields": {
            "name": "person's name",
            "title": "job title"
        },
        "linkedin_email": "your@email.com",
        "linkedin_password": "yourpassword"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'url' in request body"
            }), 400
        
        url = data['url']
        fields = data.get('fields', None)
        
        # Get LinkedIn credentials (from request or environment variables)
        linkedin_email = data.get('linkedin_email', LINKEDIN_EMAIL)
        linkedin_password = data.get('linkedin_password', LINKEDIN_PASSWORD)
        
        # Scrape the profile
        result = scrape_linkedin_profile(
            url, 
            fields, 
            linkedin_email, 
            linkedin_password
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)