"""
Main Flask application entry point.
Initializes the app, configurations, and registers blueprints.
"""
import os
import logging
from flask import Flask
from flask_session import Session
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, User
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

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure ProxyFix for proper URL generation behind proxies
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize extensions
db.init_app(app)
Session(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(chat_bp)

with app.app_context():
    # Create database tables
    db.create_all()
    logger.info("Database tables created successfully")

logger.info("Application initialized successfully")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
