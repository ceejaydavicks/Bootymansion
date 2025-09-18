#!/usr/bin/env python3
import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import uuid
import mimetypes

app = Flask(__name__)

# Configure Flask for Replit proxy environment
app.config['SERVER_NAME'] = None  # Allow all hosts for Replit proxy
app.config['APPLICATION_ROOT'] = '/'

# Security configuration with development fallbacks
SECRET_KEY = os.environ.get('SECRET_KEY')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
IS_PRODUCTION = os.environ.get('PRODUCTION', 'false').lower() == 'true'

if IS_PRODUCTION and (not SECRET_KEY or not ADMIN_USERNAME or not ADMIN_PASSWORD):
    print("ERROR: Production mode requires all security environment variables:")
    print("- SECRET_KEY: Random secret for session security") 
    print("- ADMIN_USERNAME: Admin dashboard username")
    print("- ADMIN_PASSWORD: Admin dashboard password")
    print("- PRODUCTION=true")
    exit(1)

# Use secure defaults in production, development fallbacks otherwise
if not SECRET_KEY:
    SECRET_KEY = 'dev-key-change-in-production'
    print("WARNING: Using development SECRET_KEY. Set SECRET_KEY environment variable for production!")

if not ADMIN_USERNAME:
    ADMIN_USERNAME = 'admin'
    print("WARNING: Using development admin username. Set ADMIN_USERNAME for production!")

if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = 'admin123'  
    print("WARNING: Using development admin password. Set ADMIN_PASSWORD for production!")

app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Enable CSRF protection
csrf = CSRFProtect(app)

# Session security (only enforce HTTPS in production)
app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Add cache control headers for Replit proxy
@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

PORT = int(os.environ.get("PORT", "5000"))

# Admin credentials
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Allowed file extensions and MIME types
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

def allowed_file(filename):
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS

def validate_file_content(file, extension):
    """Validate file content matches expected type"""
    if extension in ALLOWED_IMAGE_EXTENSIONS:
        try:
            # Verify it's a valid image using PIL
            file.seek(0)
            with Image.open(file) as img:
                img.verify()  # Verify the image
            file.seek(0)  # Reset for later use
            return True
        except Exception:
            return False
    elif extension in ALLOWED_VIDEO_EXTENSIONS:
        # Basic video validation - check file signature
        file.seek(0)
        header = file.read(12)
        file.seek(0)
        
        # Check for common video signatures
        video_signatures = [
            b'\x00\x00\x00\x18ftypmp4',  # MP4
            b'\x00\x00\x00\x20ftypmp4',  # MP4
            b'\x1a\x45\xdf\xa3',  # WebM/Matroska
        ]
        
        return any(header.startswith(sig) for sig in video_signatures)
    
    return False

def login_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Initialize database
def init_db():
    conn = sqlite3.connect('bootymansion.db')
    cursor = conn.cursor()
    
    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            cover_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            featured BOOLEAN DEFAULT 0
        )
    ''')
    
    # Profile categories junction table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            category_id INTEGER,
            FOREIGN KEY (profile_id) REFERENCES profiles (id),
            FOREIGN KEY (category_id) REFERENCES categories (id),
            UNIQUE(profile_id, category_id)
        )
    ''')
    
    # Media table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            filename TEXT NOT NULL,
            media_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles (id)
        )
    ''')
    
    # Insert default categories
    default_categories = [
        ('All', 'all'),
        ('Latina', 'latina'),
        ('Ebony', 'ebony'),
        ('Asian', 'asian'),
        ('Thick', 'thick'),
        ('Slim', 'slim'),
        ('Bikini', 'bikini'),
        ('Lingerie', 'lingerie')
    ]
    
    for name, slug in default_categories:
        cursor.execute('INSERT OR IGNORE INTO categories (name, slug) VALUES (?, ?)', (name, slug))
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('bootymansion.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
@app.route('/category/<slug>')
def index(slug=None):
    conn = get_db_connection()
    
    # Get all categories
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    
    # Get profiles with their categories and media
    if slug and slug != 'all':
        profiles_query = '''
            SELECT DISTINCT p.*, 
                   GROUP_CONCAT(c.name) as category_names,
                   GROUP_CONCAT(c.slug) as category_slugs
            FROM profiles p
            LEFT JOIN profile_categories pc ON p.id = pc.profile_id
            LEFT JOIN categories c ON pc.category_id = c.id
            WHERE p.id IN (
                SELECT DISTINCT p2.id 
                FROM profiles p2
                LEFT JOIN profile_categories pc2 ON p2.id = pc2.profile_id
                LEFT JOIN categories c2 ON pc2.category_id = c2.id
                WHERE c2.slug = ?
            )
            GROUP BY p.id
            ORDER BY p.created_at DESC
        '''
        profiles = conn.execute(profiles_query, (slug,)).fetchall()
    else:
        profiles_query = '''
            SELECT p.*, 
                   GROUP_CONCAT(c.name) as category_names,
                   GROUP_CONCAT(c.slug) as category_slugs
            FROM profiles p
            LEFT JOIN profile_categories pc ON p.id = pc.profile_id
            LEFT JOIN categories c ON pc.category_id = c.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        '''
        profiles = conn.execute(profiles_query).fetchall()
    
    # Add media count for each profile
    profiles_with_media = []
    for profile in profiles:
        media_count = conn.execute('SELECT COUNT(*) FROM media WHERE profile_id = ?', (profile['id'],)).fetchone()[0]
        profile_dict = dict(profile)
        profile_dict['media_count'] = media_count
        profiles_with_media.append(profile_dict)
    
    conn.close()
    
    current_category = slug or 'all'
    return render_template('index.html', 
                         profiles=profiles_with_media, 
                         categories=categories,
                         current_category=current_category)

@app.route('/profile/<int:profile_id>')
def profile_detail(profile_id):
    conn = get_db_connection()
    
    # Get profile with categories
    profile = conn.execute('''
        SELECT p.*, GROUP_CONCAT(c.name) as category_names
        FROM profiles p
        LEFT JOIN profile_categories pc ON p.id = pc.profile_id
        LEFT JOIN categories c ON pc.category_id = c.id
        WHERE p.id = ?
        GROUP BY p.id
    ''', (profile_id,)).fetchone()
    
    if not profile:
        return redirect(url_for('index'))
    
    # Get all media for this profile
    media_rows = conn.execute('''
        SELECT * FROM media 
        WHERE profile_id = ? 
        ORDER BY created_at ASC
    ''', (profile_id,)).fetchall()
    
    # Convert Row objects to dictionaries for JSON serialization
    media = [dict(row) for row in media_rows]
    
    # Get next profile for "Next Girl" functionality
    next_profile = conn.execute('''
        SELECT id FROM profiles 
        WHERE id > ? 
        ORDER BY id ASC 
        LIMIT 1
    ''', (profile_id,)).fetchone()
    
    if not next_profile:
        # If no next profile, get the first one
        next_profile = conn.execute('SELECT id FROM profiles ORDER BY id ASC LIMIT 1').fetchone()
    
    conn.close()
    
    return render_template('profile.html', 
                         profile=dict(profile), 
                         media=media,
                         next_profile_id=next_profile['id'] if next_profile else None)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Successfully logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    conn = get_db_connection()
    profiles = conn.execute('SELECT * FROM profiles ORDER BY created_at DESC').fetchall()
    categories = conn.execute('SELECT * FROM categories WHERE slug != "all" ORDER BY name').fetchall()
    conn.close()
    return render_template('admin.html', profiles=profiles, categories=categories)

@app.route('/admin/profile/new', methods=['GET', 'POST'])
@login_required
def admin_new_profile():
    if request.method == 'POST':
        return create_or_update_profile()
    
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories WHERE slug != "all" ORDER BY name').fetchall()
    conn.close()
    return render_template('admin_profile_form.html', categories=categories)

@app.route('/admin/profile/<int:profile_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_profile(profile_id):
    if request.method == 'POST':
        return create_or_update_profile(profile_id)
    
    conn = get_db_connection()
    
    profile = conn.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,)).fetchone()
    if not profile:
        return redirect(url_for('admin_dashboard'))
    
    categories = conn.execute('SELECT * FROM categories WHERE slug != "all" ORDER BY name').fetchall()
    profile_categories = conn.execute('''
        SELECT category_id FROM profile_categories WHERE profile_id = ?
    ''', (profile_id,)).fetchall()
    profile_category_ids = [row['category_id'] for row in profile_categories]
    
    media = conn.execute('SELECT * FROM media WHERE profile_id = ? ORDER BY created_at', (profile_id,)).fetchall()
    
    conn.close()
    
    return render_template('admin_profile_form.html', 
                         profile=profile, 
                         categories=categories,
                         profile_category_ids=profile_category_ids,
                         media=media)

def create_or_update_profile(profile_id=None):
    conn = get_db_connection()
    
    name = request.form.get('name')
    description = request.form.get('description')
    category_ids = request.form.getlist('categories')
    
    if profile_id:
        # Update existing profile
        conn.execute('UPDATE profiles SET name = ?, description = ? WHERE id = ?',
                    (name, description, profile_id))
        
        # Delete existing category associations
        conn.execute('DELETE FROM profile_categories WHERE profile_id = ?', (profile_id,))
    else:
        # Create new profile
        cursor = conn.execute('INSERT INTO profiles (name, description) VALUES (?, ?)',
                            (name, description))
        profile_id = cursor.lastrowid
    
    # Add category associations
    for category_id in category_ids:
        conn.execute('INSERT INTO profile_categories (profile_id, category_id) VALUES (?, ?)',
                    (profile_id, category_id))
    
    # Handle file uploads
    handle_file_uploads(request.files.getlist('media_files'), profile_id, conn)
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

def handle_file_uploads(files, profile_id, conn):
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            extension = filename.rsplit('.', 1)[1].lower()
            
            # Validate file content
            if not validate_file_content(file, extension):
                print(f"Warning: Invalid file content for {filename}, skipping")
                continue
            
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Determine media type and path
            if extension in ALLOWED_VIDEO_EXTENSIONS:
                media_type = 'video'
                upload_dir = 'uploads/videos'
            else:
                media_type = 'image'
                upload_dir = 'uploads/images'
            
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # If it's an image, create a thumbnail
            if media_type == 'image':
                try:
                    create_thumbnail(file_path)
                except Exception as e:
                    print(f"Error creating thumbnail: {e}")
            
            # Save to database
            conn.execute('''
                INSERT INTO media (profile_id, filename, media_type, file_path)
                VALUES (?, ?, ?, ?)
            ''', (profile_id, unique_filename, media_type, file_path))
            
            # Set as cover image if it's the first image for this profile
            existing_cover = conn.execute('SELECT cover_image FROM profiles WHERE id = ?', (profile_id,)).fetchone()
            if not existing_cover['cover_image'] and media_type == 'image':
                conn.execute('UPDATE profiles SET cover_image = ? WHERE id = ?', (file_path, profile_id))

def create_thumbnail(image_path):
    with Image.open(image_path) as img:
        img.thumbnail((400, 400))
        thumb_path = image_path.replace('.', '_thumb.')
        img.save(thumb_path)

@app.route('/api/profiles')
def api_profiles():
    conn = get_db_connection()
    category = request.args.get('category', 'all')
    
    if category and category != 'all':
        profiles = conn.execute('''
            SELECT DISTINCT p.*, 
                   GROUP_CONCAT(c.name) as category_names
            FROM profiles p
            LEFT JOIN profile_categories pc ON p.id = pc.profile_id
            LEFT JOIN categories c ON pc.category_id = c.id
            WHERE p.id IN (
                SELECT DISTINCT p2.id 
                FROM profiles p2
                LEFT JOIN profile_categories pc2 ON p2.id = pc2.profile_id
                LEFT JOIN categories c2 ON pc2.category_id = c2.id
                WHERE c2.slug = ?
            )
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''', (category,)).fetchall()
    else:
        profiles = conn.execute('''
            SELECT p.*, GROUP_CONCAT(c.name) as category_names
            FROM profiles p
            LEFT JOIN profile_categories pc ON p.id = pc.profile_id
            LEFT JOIN categories c ON pc.category_id = c.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''').fetchall()
    
    conn.close()
    
    return jsonify([dict(profile) for profile in profiles])

@app.route('/uploads/<path:filename>')
def secure_upload(filename):
    """Securely serve uploaded files"""
    # Determine if it's an image or video
    if filename.startswith('images/'):
        directory = 'uploads/images'
        filename = filename[7:]  # Remove 'images/' prefix
    elif filename.startswith('videos/'):
        directory = 'uploads/videos'
        filename = filename[7:]  # Remove 'videos/' prefix
    else:
        return "File not found", 404
    
    try:
        return send_from_directory(directory, filename)
    except FileNotFoundError:
        return "File not found", 404

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

# Initialize database on import for serverless
init_db()

if __name__ == '__main__':
    # Get debug mode from environment (False by default for production)
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Server running at http://0.0.0.0:{PORT}/")
    print("Admin dashboard available at /admin")
    if not debug_mode:
        print("Production mode - Debug disabled")
    
    app.run(host='0.0.0.0', port=PORT, debug=debug_mode)