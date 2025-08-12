# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **high-feature blog CMS system** built with Flask and SQLAlchemy. The project is a sophisticated content management system featuring an advanced block-based editor, WordPress import functionality, 2FA authentication, and comprehensive security measures.

**Current Status**: Fully functional CMS with recent CSS architecture refactoring and UI/UX improvements (as of 2025-08-11).

## Technology Stack

- **Backend**: Python 3.10+, Flask 2.x, SQLAlchemy ORM
- **Database**: SQLite with Flask-Migrate
- **Frontend**: Bootstrap 5, ES6+ JavaScript, Sortable.js, Cropper.js
- **Security**: Flask-Login, TOTP/2FA, Flask-WTF CSRF protection
- **Content**: Markdown processing, Bleach HTML sanitization, PIL image processing
- **Deployment**: Gunicorn WSGI server, Nginx reverse proxy

## Recent Updates (2025-08-12)

### Critical Fixes
1. **Image Management Page**: Fixed template error (duplicate `{% endblock %}` tag)
2. **Featured Image Save**: Fixed image path storage in database
3. **Image URLs**: Corrected path format from `articles/` to `uploads/articles/`
4. **CSS Styles**: Added complete styling for image management interface

### New Features
- Image management grid layout with hover effects
- Image metadata editing (Alt text, caption, description)
- Image search functionality
- Usage tracking for uploaded images

## Previous Updates (2025-08-11)

### CSS Architecture Refactoring
The project underwent major CSS externalization:
- **components.css** (1,700+ lines): Common UI components
- **admin-enhanced.css** (900+ lines): Admin panel specific styles
- **main.css**: Base styles and CSS variables
- **rdash-admin.css**: Admin dashboard framework

### Fixed Issues
- ✅ Template errors from CSS externalization (duplicate `{% endblock %}` tags)
- ✅ SEO tools page layout restoration
- ✅ Hero section height optimization (400px desktop, 320px mobile)
- ✅ Category page styling with theme colors
- ✅ Markdown editor sizing (500px height)
- ✅ Markdown preview functionality restoration

## Architecture Overview

### Core Application Structure
- `app.py` - Main Flask application with public routes (25+ endpoints)
- `admin.py` - Admin panel Blueprint with protected routes (20+ endpoints)
- `models.py` - SQLAlchemy database models
- `forms.py` - WTForms for general forms
- `article_service.py` - Article-related business logic
- `wordpress_importer.py` - WordPress XML import functionality
- `ga4_analytics.py` - Google Analytics integration

### Database Models
- **Users**: Authentication, profiles, 2FA settings, roles (admin/author)
- **Articles**: Title, slug, summary, status, publication dates
- **Categories**: Hierarchical structure with SEO metadata
- **Comments**: Comment system with approval workflow
- **Images**: Image management with alt text and metadata
- **SeoAnalysis**: SEO analysis results storage
- **Many-to-Many**: Articles ↔ Categories via `article_categories`

### Security Architecture
- **2FA Required**: TOTP/Google Authenticator for admin access
- **Role-based Access**: Admin vs Author permission levels
- **CSRF Protection**: Flask-WTF on all forms
- **Input Sanitization**: Bleach for HTML content
- **File Upload Security**: Type/size validation
- **Session Management**: Secure handling with timeouts

## Common Commands

### Development Server
```bash
python app.py          # Start development server (port 5001)
flask run              # Alternative way to start server
```

### Database Management
```bash
flask db migrate -m "description"    # Generate new migration
flask db upgrade                     # Apply pending migrations
flask db downgrade                   # Rollback last migration
```

### WordPress Import
```bash
python wordpress_importer.py --xml sample.xml --author-id 1
```

### Admin User Management
```bash
python scripts/create_admin.py          # Create new admin user
python scripts/reset_admin_password.py  # Reset admin password
```

### Deployment
```bash
./deploy.sh    # Deploy to production server
```

## Key Directories

- `templates/` - Jinja2 templates
  - `templates/admin/` - Admin panel templates
- `static/` - Static assets
  - `static/css/` - Stylesheets (externalized)
  - `static/js/` - JavaScript files
  - `static/uploads/` - User uploads
    - `articles/` - Article images
    - `category_ogp/` - Category OGP images
    - `content/` - Content images
- `migrations/` - Database migration files
- `reports/` - Development reports and documentation
- `scripts/` - Utility scripts

## UI/UX Features

### Category Theme Colors
- **Programming**: Blue (#007bff)
- **Design**: Pink (#e83e8c)
- **Lifestyle**: Teal (#20c997)
- **Tech**: Purple (#6f42c1)
- **Business**: Orange (#fd7e14)

### Responsive Design
- Mobile-first approach
- Breakpoints: 576px, 768px, 1024px
- Touch-optimized interfaces

### Enhanced Features
- **Markdown Editor**: 500px height with real-time preview
- **Image Cropping**: Cropper.js integration
- **Drag & Drop**: Article ordering
- **SEO Tools**: Comprehensive SEO management
- **Analytics**: Google Analytics 4 integration

## Development Notes

### Working with CSS
The CSS architecture is modular:
1. **components.css**: Reusable components (cards, buttons, forms)
2. **admin-enhanced.css**: Admin-specific enhancements
3. **main.css**: Base styles and CSS variables
4. Use CSS variables for consistent theming

### Template Structure
- All templates extend from base layouts
- Admin templates use `templates/admin/layout.html`
- Public templates use `templates/layout.html`
- Flash messages handled via `_flash_messages.html`

### JavaScript Integration
- Markdown preview: Real-time preview with syntax highlighting
- Image cropping: Cropper.js for featured images
- Drag & drop: Sortable.js for content ordering
- CSRF tokens required for all AJAX requests

### Security Best Practices
- Always validate user input
- Use parameterized queries (via SQLAlchemy)
- Sanitize HTML content with Bleach
- Require 2FA for admin access
- Implement proper CSRF protection

## Testing & Quality Assurance

### Linting and Type Checking
```bash
# Add these commands if available:
npm run lint       # Run linting
npm run typecheck  # Run type checking
```

### Manual Testing Areas
- Admin authentication flow (including 2FA)
- Article creation/editing
- Category management
- Image upload and cropping
- Markdown preview functionality
- WordPress import process
- SEO tools functionality

## Production Deployment

### Server Configuration
- **Web Server**: Nginx (see `nginx_miniblog.conf`)
- **WSGI Server**: Gunicorn (see `gunicorn_config.py`)
- **Service**: Systemd (see `miniblog.service`)
- **SSL/TLS**: Required for production

### Deployment Checklist
1. Set production environment variables
2. Run database migrations
3. Collect static files
4. Configure Nginx
5. Set up SSL certificates
6. Configure backup procedures
7. Monitor application logs

## Known Issues & Future Improvements

### To Do
- [ ] Image optimization automation
- [ ] Enhanced SEO tool implementations
- [ ] Performance optimizations (CSS/JS minification)
- [ ] CDN integration
- [ ] Advanced caching strategies

### Recent Fixes (2025-08-11)
- ✅ Template syntax errors from CSS externalization
- ✅ SEO tools page layout
- ✅ Hero section responsive sizing
- ✅ Category page theming
- ✅ Markdown editor UX
- ✅ Preview functionality

## Troubleshooting

### Common Issues
1. **Template Errors**: Check for duplicate `{% endblock %}` tags
2. **CSS Not Loading**: Verify static file serving configuration
3. **Markdown Preview 404**: Ensure correct URL generation with `url_for()`
4. **2FA Issues**: Check TOTP time synchronization
5. **Import Failures**: Validate XML structure and author IDs

### Debug Mode
```python
# In app.py, ensure debug mode is appropriate:
app.run(debug=True)  # Development only
```

---

**Project Maintainer Notes**: This project demonstrates advanced Flask development with emphasis on security, user experience, and content management capabilities. The recent CSS refactoring improves maintainability and performance while preserving all functionality.