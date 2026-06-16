import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Force production mode for WSGI
os.environ["FLASK_ENV"] = "production"

from app import create_app

# Create the application instance
app = create_app("production")

if __name__ == "__main__":
    # If run directly (not via gunicorn), run via waitress for testing on Windows
    from waitress import serve
    print("Starting Waitress production server on http://0.0.0.0:8000")
    serve(app, host="0.0.0.0", port=8000)
