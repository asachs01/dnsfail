from flask import Flask
from datetime import datetime

def create_app(counter_instance=None):
    app = Flask(__name__)
    
    # Store counter instance for access in routes
    app.counter_instance = counter_instance
    
    # Import and register blueprints
    from .routes import api
    app.register_blueprint(api)
    
    return app