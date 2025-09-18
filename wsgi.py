#!/usr/bin/env python3
import os

# Set production environment BEFORE importing app
os.environ['PRODUCTION'] = 'true'

from app import app

# Production configuration
if __name__ == "__main__":
    # This is for development only
    app.run(debug=False)
else:
    # This is the WSGI callable for production servers like gunicorn
    application = app