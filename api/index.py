
from flask import Flask, render_template_string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vercel-key'

# Minimal template since templates directory won't be available
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>BOOTYMANSION</title>
    <style>
        body { background: #000; color: #fff; font-family: Arial; text-align: center; padding: 50px; }
        h1 { color: #ff1744; }
    </style>
</head>
<body>
    <h1>BOOTYMANSION</h1>
    <p>Serverless version - Limited functionality</p>
    <p>Database and uploads not available in serverless environment</p>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE)

@app.route('/api/profiles')
def api_profiles():
    return {'profiles': []}

# Vercel handler
def handler(request):
    return app.wsgi_app(request.environ, request.start_response)

if __name__ == '__main__':
    app.run(debug=True)
