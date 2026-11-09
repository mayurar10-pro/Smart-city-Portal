import os
import uuid
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

from config import Config
import models
from ml.train_model import predict_complaint_category

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Initialize & seed DB before handling requests
with app.app_context():
    models.init_db()
    models.seed_db()

# --- Context Processor for Global Template Variables ---
@app.context_processor
def inject_globals():
    return {
        'current_year': datetime.datetime.now().year,
        'is_admin': 'admin_logged_in' in session
    }

# ================= CITIZEN PORTAL ROUTES =================

@app.route('/')
def index():
    """Homepage: strictly displays the 3 main service cards, search, announcements & stats"""
    announcements = models.get_announcements(active_only=True)[:4]
    analytics = models.get_analytics_data()
    return render_template('index.html', announcements=announcements, analytics=analytics)

@app.route('/services')
def services():
    """Services Overview: Detailed guide to the 3 main services"""
    return render_template('services.html')

@app.route('/waste')
def waste():
    """Dedicated Waste Management Service Page"""
    search = request.args.get('search', '').strip()
    facilities = models.get_facilities(category='Waste Management', search=search)
    announcements = models.get_announcements(category='Waste Management')
    return render_template('waste.html', facilities=facilities, announcements=announcements, search=search)

@app.route('/hospitals')
def hospitals():
    """Dedicated Hospital Services Page"""
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    facilities = models.get_facilities(category='Hospital Services', search=search)
    
    # Filter by department if requested
    if department:
        facilities = [f for f in facilities if department.lower() in (f.get('details') or '').lower()]
        
    announcements = models.get_announcements(category='Hospital Services')
    return render_template('hospitals.html', facilities=facilities, announcements=announcements, search=search, department=department)

@app.route('/roads')
def roads():
    """Dedicated Road Management Service Page"""
    search = request.args.get('search', '').strip()
    facilities = models.get_facilities(category='Road Management', search=search)
    announcements = models.get_announcements(category='Road Management')
    return render_template('roads.html', facilities=facilities, announcements=announcements, search=search)

@app.route('/map')
def map_view():
    """Interactive City Map for all 3 services and civic complaints"""
    category = request.args.get('category', 'All')
    return render_template('map.html', active_category=category)

@app.route('/report', methods=['GET', 'POST'])
def report_issue():
    """Common Complaint Reporting System for Waste, Hospital, and Road services"""
    prefill_category = request.args.get('category', 'Waste Management')
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        location_name = request.form.get('location_name', '').strip()
        citizen_name = request.form.get('citizen_name', '').strip() or 'Anonymous Citizen'
        citizen_contact = request.form.get('citizen_contact', '').strip()
        
        # Coordinates (optional from map picker)
        try:
            latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
            longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
        except ValueError:
            latitude = None
            longitude = None

        if not title or not description or not location_name or not category:
            flash('Please complete all required fields (Title, Category, Location, and Description).', 'danger')
            return render_template('report_issue.html', prefill_category=category)

        # Handle file upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                ext = safe_name.rsplit('.', 1)[1].lower()
                image_filename = f"{uuid.uuid4().hex[:12]}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # AI Categorization prediction
        ml_res = predict_complaint_category(f"{title} {description}")
        predicted_cat = ml_res.get('category', category)
        confidence = ml_res.get('confidence', 0.0)

        # Generate unique tracking ID: SCC-[CAT_CODE]-[YYYYMMDD]-[RANDOM]
        cat_codes = {
            'Waste Management': 'WST',
            'Hospital Services': 'HSP',
            'Road Management': 'ROD'
        }
        code = cat_codes.get(category, 'CIV')
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        rand_num = str(uuid.uuid4().int)[:4]
        tracking_id = f"SCC-{code}-{date_str}-{rand_num}"

        complaint_data = {
            'tracking_id': tracking_id,
            'title': title,
            'category': category,
            'predicted_category': predicted_cat,
            'confidence': confidence,
            'description': description,
            'location_name': location_name,
            'latitude': latitude,
            'longitude': longitude,
            'image_path': image_filename,
            'citizen_name': citizen_name,
            'citizen_contact': citizen_contact,
            'status': 'Submitted',
            'admin_notes': '',
            'rejection_reason': ''
        }

        models.insert_complaint(complaint_data)
        flash(f'Your complaint has been submitted successfully! Your Tracking ID is {tracking_id}', 'success')
        return redirect(url_for('track_issue', tracking_id=tracking_id))

    return render_template('report_issue.html', prefill_category=prefill_category)

@app.route('/track', defaults={'tracking_id': None})
@app.route('/track/<tracking_id>')
def track_issue(tracking_id):
    """Track complaint progress using Unique Tracking ID"""
    searched_id = tracking_id or request.args.get('tracking_id', '').strip()
    complaint = None
    recent_complaints = []
    
    if searched_id:
        complaint = models.get_complaint_by_tracking_id(searched_id)
        if not complaint:
            flash(f'No complaint found with Tracking ID: {searched_id}. Please verify your ID.', 'warning')
    else:
        # Show a few recent complaints for public transparency
        recent_complaints = models.get_all_complaints()[:5]

    return render_template('track_issue.html', complaint=complaint, searched_id=searched_id, recent_complaints=recent_complaints)

@app.route('/announcements')
def announcements():
    """Civic announcements bulletin board"""
    category = request.args.get('category', 'All')
    announcements_list = models.get_announcements(category=category, active_only=True)
    return render_template('announcements.html', announcements=announcements_list, active_category=category)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded issue photos"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ================= API ENDPOINTS =================

@app.route('/api/predict-category', methods=['POST'])
def api_predict():
    """AI Prediction API Endpoint for real-time frontend suggestion"""
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'category': 'Waste Management', 'confidence': 0.0, 'scores': {}})
    
    result = predict_complaint_category(text)
    return jsonify(result)

@app.route('/api/facilities')
def api_facilities():
    """Return facilities JSON for Leaflet map markers"""
    category = request.args.get('category', 'All')
    facilities = models.get_facilities(category=category)
    return jsonify(facilities)

@app.route('/api/complaints-map')
def api_complaints_map():
    """Return geolocated complaints for map display"""
    complaints = models.get_all_complaints()
    geocoded = [c for c in complaints if c.get('latitude') and c.get('longitude')]
    return jsonify(geocoded)

# ================= ADMIN PORTAL ROUTES =================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin Authentication Portal"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = models.get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()

        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = admin['username']
            session['admin_name'] = admin['full_name']
            flash('Welcome back! You have successfully logged in to the Admin Portal.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials. Please verify your username and password.', 'danger')

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin Logout"""
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    """Admin Dashboard with Analytics and Key Metrics"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    analytics = models.get_analytics_data()
    recent_complaints = models.get_all_complaints()[:6]
    facilities = models.get_facilities()
    announcements = models.get_announcements(active_only=False)

    return render_template(
        'admin_dashboard.html',
        analytics=analytics,
        recent_complaints=recent_complaints,
        facilities=facilities,
        announcements=announcements
    )

@app.route('/admin/complaints')
def manage_complaints():
    """Admin Complaint Management Portal"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    category = request.args.get('category', 'All')
    status = request.args.get('status', 'All')
    search = request.args.get('search', '').strip()

    complaints = models.get_all_complaints(category=category, status=status, search=search)
    return render_template('manage_complaints.html', complaints=complaints, active_category=category, active_status=status, search=search)

@app.route('/admin/complaint/update/<int:complaint_id>', methods=['POST'])
def update_complaint(complaint_id):
    """Admin updates status, adds resolution note or rejection reason"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '').strip()
    rejection_reason = request.form.get('rejection_reason', '').strip()

    models.update_complaint_status(complaint_id, status, admin_notes, rejection_reason)
    flash(f'Complaint #{complaint_id} status updated to {status}.', 'success')
    return redirect(request.referrer or url_for('manage_complaints'))

@app.route('/admin/facility/add', methods=['POST'])
def add_facility():
    """Admin adds new service facility (Waste, Hospital, Road)"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    data = {
        'category': request.form.get('category'),
        'name': request.form.get('name'),
        'address': request.form.get('address'),
        'contact_number': request.form.get('contact_number'),
        'emergency_contact': request.form.get('emergency_contact'),
        'operating_hours': request.form.get('operating_hours'),
        'status': request.form.get('status', 'Operational'),
        'details': request.form.get('details'),
        'latitude': float(request.form.get('latitude') or Config.DEFAULT_MAP_LAT),
        'longitude': float(request.form.get('longitude') or Config.DEFAULT_MAP_LNG)
    }

    models.insert_facility(data)
    flash(f"New {data['category']} facility '{data['name']}' added successfully.", 'success')
    return redirect(url_for('admin_dashboard') + '#facilities-section')

@app.route('/admin/facility/delete/<int:facility_id>', methods=['POST'])
def delete_facility(facility_id):
    """Admin deletes a facility"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    models.delete_facility(facility_id)
    flash('Facility has been removed.', 'info')
    return redirect(url_for('admin_dashboard') + '#facilities-section')

@app.route('/admin/announcement/add', methods=['POST'])
def add_announcement():
    """Admin publishes a new civic announcement"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'General')
    content = request.form.get('content', '').strip()
    priority = request.form.get('priority', 'Normal')

    if title and content:
        models.insert_announcement(title, category, content, priority)
        flash('New civic announcement published successfully.', 'success')
    else:
        flash('Please fill in both title and announcement content.', 'danger')

    return redirect(url_for('admin_dashboard') + '#announcements-section')

@app.route('/admin/announcement/delete/<int:announcement_id>', methods=['POST'])
def delete_announcement(announcement_id):
    """Admin deletes an announcement"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    models.delete_announcement(announcement_id)
    flash('Announcement deleted.', 'info')
    return redirect(url_for('admin_dashboard') + '#announcements-section')

if __name__ == '__main__':
    # Run development server
    app.run(debug=True, host='127.0.0.1', port=5000)
