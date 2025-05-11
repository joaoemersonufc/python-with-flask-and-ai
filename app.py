"""
Main Flask application entry point.
Initializes the app, configurations, and registers blueprints.
"""
import os
import logging
from flask import Flask
from flask_session import Session
from routes.chat_routes import chat_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)

# Configure the app
app.config.update(
    SECRET_KEY=os.environ.get("SESSION_SECRET", "dev-secret-key"),
    SESSION_TYPE="filesystem",
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True,
    SESSION_FILE_DIR=os.path.join(os.getcwd(), "flask_session"),
    PERMANENT_SESSION_LIFETIME=86400,  # 24 hours
)

# Initialize Flask-Session
Session(app)

# Register blueprints
app.register_blueprint(chat_bp)

logger.info("Application initialized successfully")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
