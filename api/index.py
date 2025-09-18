
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-key')

# Remove database functionality for serverless
@app.route('/')
def index():
    return render_template('index.html', profiles=[], categories=[])

@app.route('/api/profiles')
def api_profiles():
    return jsonify([])

# Export for Vercel
def handler(request):
    return app(request.environ, lambda *args: None)
