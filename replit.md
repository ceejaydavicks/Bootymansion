# BOOTYMANSION - Premium Model Gallery

## Project Overview
A Flask-based image and video gallery website for showcasing models with categorized profiles. The application features a modern dark theme interface with admin panel for content management.

## Architecture
- **Backend**: Python Flask web application
- **Database**: SQLite (bootymansion.db) with profiles, categories, media tables
- **File Storage**: Local file system (uploads/images, uploads/videos)
- **Authentication**: Admin login with session management
- **Security**: CSRF protection, file type validation, secure uploads

## Recent Changes (September 18, 2025)
- ✅ Configured for Replit environment with proxy support
- ✅ Set up workflow to run Flask server on port 5000
- ✅ Added cache control headers for proper Replit proxy behavior
- ✅ Initialized SQLite database with default categories
- ✅ Configured deployment for autoscale with Gunicorn
- ✅ Created proper .gitignore for Python Flask projects

## User Preferences
- Keep existing SQLite database (following project's original design)
- Maintain dark theme aesthetic
- Preserve security features and admin functionality
- Use development credentials for testing (admin/admin123)

## Project Structure
```
├── app.py              # Main Flask application
├── wsgi.py            # WSGI entry point for production
├── pyproject.toml     # Python dependencies
├── bootymansion.db    # SQLite database
├── templates/         # Jinja2 templates
│   ├── base.html
│   ├── index.html     # Homepage with model gallery
│   ├── profile.html   # Individual model profile
│   ├── admin.html     # Admin dashboard
│   └── admin_*.html   # Admin forms
├── static/
│   ├── css/styles.css # Dark theme styling
│   └── js/main.js     # Frontend JavaScript
└── uploads/
    ├── images/        # Profile images
    └── videos/        # Profile videos
```

## Environment Variables
Set these for production:
- `SECRET_KEY`: Flask session encryption key
- `ADMIN_USERNAME`: Admin panel username  
- `ADMIN_PASSWORD`: Admin panel password
- `PRODUCTION=true`: Enable production mode

## Development Credentials
- Admin Username: admin
- Admin Password: admin123
- Access: `/admin/login`

## Features
- Model profile management with categories
- Image and video upload support
- Category filtering (Latina, Ebony, Asian, etc.)
- Responsive design with lightbox gallery
- Admin dashboard for content management
- Secure file handling with validation