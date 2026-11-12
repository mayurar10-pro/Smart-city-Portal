import os
import re
import uuid
import base64
import random
import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, send_from_directory, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import (
    db, User, AuthorityUser, Complaint, ComplaintHistory,
    Service, Announcement, Notification, OTPVerification, seed_initial_data
)
from ml.train_model import predict_complaint_category

# =====================================================================
# Application Initialization & Setup
# =====================================================================
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Database with Flask-SQLAlchemy
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please sign in to access your citizen account or submit a civic grievance.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    """Load either citizen User or AuthorityUser based on prefixed ID"""
    if not user_id:
        return None
    if user_id.startswith('user_'):
        try:
            return User.query.get(int(user_id.split('_')[1]))
        except Exception:
            return None
    elif user_id.startswith('auth_'):
        try:
            return AuthorityUser.query.get(int(user_id.split('_')[1]))
        except Exception:
            return None
    return None

# Create tables & seed default data within app context
with app.app_context():
    db.create_all()
    seed_initial_data(Config)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# =====================================================================
# Global Template Context Processor
# =====================================================================
@app.context_processor
def inject_global_template_vars():
    unread_count = 0
    if current_user.is_authenticated and session.get('user_type') == 'citizen':
        try:
            unread_count = Notification.query.filter_by(
                user_id=current_user.user_id, is_read=False
            ).count()
        except Exception:
            unread_count = 0

    return {
        'current_year': datetime.datetime.now().year,
        'unread_notif_count': unread_count,
        'user_type': session.get('user_type')
    }

# =====================================================================
# SMS / OTP Verification Services
# =====================================================================
def send_sms_otp(mobile_number, otp_code):
    """
    Sends SMS OTP using Twilio if configured, or development simulation.
    Never exposes plain OTP in production logs.
    """
    if Config.SMS_PROVIDER == 'twilio' and Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN:
        try:
            # Twilio optional integration
            from twilio.rest import Client
            client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"Your SmartCity Connect verification code is {otp_code}. Valid for 10 minutes.",
                from_=Config.TWILIO_PHONE_NUMBER,
                to=f"+91{mobile_number}"
            )
            return True, None
        except Exception as e:
            return False, f"SMS Gateway error: {str(e)}"
    
    # Development Mode Fallback:
    # Code is stored hashed in DB and returned only for development testing display
    return True, str(otp_code)

# =====================================================================
# PUBLIC & CITIZEN PORTAL ROUTES
# =====================================================================

@app.route('/')
def index():
    """Homepage: strictly displays the 3 main service cards, search, announcements & stats"""
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(4).all()
    
    # Calculate live municipal statistics
    total_complaints = Complaint.query.count()
    resolved_complaints = Complaint.query.filter_by(status='Resolved').count()
    pending_complaints = Complaint.query.filter(Complaint.status.notin_(['Resolved', 'Rejected'])).count()
    facilities_count = Service.query.count()

    analytics = {
        'total': total_complaints,
        'resolved': resolved_complaints,
        'pending': pending_complaints,
        'facilities_count': facilities_count
    }

    return render_template('index.html', announcements=announcements, analytics=analytics)

@app.route('/services')
def services():
    """Three Core Services Overview"""
    return render_template('services.html')

@app.route('/waste')
def waste():
    """Dedicated Waste Management Service Page"""
    search = request.args.get('search', '').strip()
    query = Service.query.filter_by(category='Waste Management')
    if search:
        query = query.filter(
            (Service.service_name.ilike(f'%{search}%')) |
            (Service.address.ilike(f'%{search}%')) |
            (Service.description.ilike(f'%{search}%'))
        )
    facilities = query.all()
    announcements = Announcement.query.filter(
        (Announcement.category == 'Waste Management') | (Announcement.category == 'General')
    ).order_by(Announcement.created_at.desc()).all()

    return render_template('waste.html', facilities=facilities, announcements=announcements, search=search)

@app.route('/hospitals')
def hospitals():
    """Dedicated Hospital Services Page"""
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    query = Service.query.filter_by(category='Hospital Services')

    if search:
        query = query.filter(
            (Service.service_name.ilike(f'%{search}%')) |
            (Service.address.ilike(f'%{search}%')) |
            (Service.description.ilike(f'%{search}%'))
        )
    if department:
        query = query.filter(Service.description.ilike(f'%{department}%'))

    facilities = query.all()
    announcements = Announcement.query.filter(
        (Announcement.category == 'Hospital Services') | (Announcement.category == 'General')
    ).order_by(Announcement.created_at.desc()).all()

    return render_template('hospitals.html', facilities=facilities, announcements=announcements, search=search, department=department)

@app.route('/roads')
def roads():
    """Dedicated Road Management Service Page"""
    search = request.args.get('search', '').strip()
    query = Service.query.filter_by(category='Road Management')
    if search:
        query = query.filter(
            (Service.service_name.ilike(f'%{search}%')) |
            (Service.address.ilike(f'%{search}%')) |
            (Service.description.ilike(f'%{search}%'))
        )
    facilities = query.all()
    announcements = Announcement.query.filter(
        (Announcement.category == 'Road Management') | (Announcement.category == 'General')
    ).order_by(Announcement.created_at.desc()).all()

    return render_template('roads.html', facilities=facilities, announcements=announcements, search=search)

@app.route('/map')
def map_view():
    """Interactive City Map with Leaflet and OpenStreetMap"""
    category = request.args.get('category', 'all')
    return render_template('map.html', active_category=category)

@app.route('/announcements')
def announcements():
    """Public Announcements Bulletin"""
    category = request.args.get('category', 'All')
    query = Announcement.query
    if category != 'All':
        query = query.filter(
            (Announcement.category == category) | (Announcement.category == 'General')
        )
    announcements_list = query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=announcements_list, active_category=category)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded or camera captured photos securely"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], secure_filename(filename))

# =====================================================================
# CITIZEN REGISTRATION & MOBILE OTP VERIFICATION
# =====================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Citizen Registration using Mobile Number"""
    if current_user.is_authenticated and session.get('user_type') == 'citizen':
        return redirect(url_for('citizen_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        email = request.form.get('email', '').strip() or None
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validation
        if not name or not mobile_number or not password:
            flash('Please fill in all required fields (Name, Mobile Number, Password).', 'danger')
            return render_template('register.html')

        if not re.match(r'^[0-9]{10}$', mobile_number):
            flash('Please enter a valid 10-digit mobile number.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please verify and re-enter.', 'danger')
            return render_template('register.html')

        # Check if mobile number already exists
        existing_user = User.query.filter_by(mobile_number=mobile_number).first()
        if existing_user and existing_user.is_verified:
            flash('This mobile number is already registered. Please sign in.', 'info')
            return redirect(url_for('login'))

        # Create or update unverified user
        if not existing_user:
            user = User(
                name=name,
                mobile_number=mobile_number,
                email=email,
                is_verified=False
            )
            user.set_password(password)
            db.session.add(user)
        else:
            user = existing_user
            user.name = name
            user.email = email
            user.set_password(password)

        db.session.commit()

        # Generate Secure 6-digit OTP
        plain_otp = f"{random.randint(100000, 999999)}"
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=Config.OTP_EXPIRY_MINUTES)

        # Invalidate old OTPs for this number
        OTPVerification.query.filter_by(mobile_number=mobile_number, is_used=False).update({'is_used': True})

        otp_rec = OTPVerification(
            mobile_number=mobile_number,
            expires_at=expires_at,
            attempts=0,
            is_used=False
        )
        otp_rec.set_otp(plain_otp)
        db.session.add(otp_rec)
        db.session.commit()

        # Send OTP
        success, dev_code = send_sms_otp(mobile_number, plain_otp)
        session['pending_mobile'] = mobile_number
        if dev_code:
            session['dev_otp'] = dev_code

        flash(f'An SMS verification code has been dispatched to +91 {mobile_number}.', 'success')
        return redirect(url_for('verify_otp'))

    return render_template('register.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify Mobile Number OTP before account activation"""
    mobile_number = session.get('pending_mobile')
    if not mobile_number:
        flash('No pending registration found. Please register first.', 'warning')
        return redirect(url_for('register'))

    dev_otp = session.get('dev_otp')

    if request.method == 'POST':
        candidate_otp = request.form.get('otp', '').strip()
        form_mobile = request.form.get('mobile_number', mobile_number).strip()

        # Find latest active OTP record
        otp_rec = OTPVerification.query.filter_by(
            mobile_number=form_mobile, is_used=False
        ).order_by(OTPVerification.created_at.desc()).first()

        if not otp_rec:
            flash('No active verification code found. Please request a new OTP.', 'danger')
            return render_template('verify_otp.html', mobile_number=form_mobile, dev_otp=dev_otp)

        otp_rec.attempts += 1
        if otp_rec.attempts > 5:
            otp_rec.is_used = True
            db.session.commit()
            flash('Too many incorrect attempts. Please request a new verification code.', 'danger')
            return redirect(url_for('register'))

        if otp_rec.verify_otp(candidate_otp):
            otp_rec.is_used = True
            
            # Activate user
            user = User.query.filter_by(mobile_number=form_mobile).first()
            if user:
                user.is_verified = True
                db.session.commit()

                # Clean up session OTP data
                session.pop('pending_mobile', None)
                session.pop('dev_otp', None)

                # Log the citizen in automatically
                login_user(user)
                session['user_type'] = 'citizen'

                flash('Your mobile number has been successfully verified! Welcome to SmartCity Connect.', 'success')
                return redirect(url_for('citizen_dashboard'))
        else:
            db.session.commit()
            flash('Invalid or expired verification code. Please try again.', 'danger')

    return render_template('verify_otp.html', mobile_number=mobile_number, dev_otp=dev_otp)

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend 6-Digit Verification Code"""
    mobile_number = request.form.get('mobile_number') or session.get('pending_mobile')
    if not mobile_number:
        flash('Invalid session. Please register.', 'warning')
        return redirect(url_for('register'))

    plain_otp = f"{random.randint(100000, 999999)}"
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=Config.OTP_EXPIRY_MINUTES)

    OTPVerification.query.filter_by(mobile_number=mobile_number, is_used=False).update({'is_used': True})

    otp_rec = OTPVerification(
        mobile_number=mobile_number,
        expires_at=expires_at,
        attempts=0,
        is_used=False
    )
    otp_rec.set_otp(plain_otp)
    db.session.add(otp_rec)
    db.session.commit()

    success, dev_code = send_sms_otp(mobile_number, plain_otp)
    session['pending_mobile'] = mobile_number
    if dev_code:
        session['dev_otp'] = dev_code

    flash(f'A fresh verification code has been dispatched to +91 {mobile_number}.', 'info')
    return redirect(url_for('verify_otp'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Citizen Login using Mobile Number and Password"""
    if current_user.is_authenticated and session.get('user_type') == 'citizen':
        return redirect(url_for('citizen_dashboard'))

    if request.method == 'POST':
        mobile_number = request.form.get('mobile_number', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(mobile_number=mobile_number).first()
        if user and user.check_password(password):
            if not user.is_verified:
                session['pending_mobile'] = mobile_number
                flash('Your mobile number is not yet verified. Please complete OTP verification.', 'warning')
                return redirect(url_for('verify_otp'))

            login_user(user)
            session['user_type'] = 'citizen'
            flash(f'Welcome back, {user.name}!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('citizen_dashboard'))
        else:
            flash('Invalid mobile number or password. Please verify your credentials.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Citizen Logout"""
    logout_user()
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('index'))

# =====================================================================
# INDIVIDUAL CITIZEN DASHBOARD & PRIVATE COMPLAINTS
# =====================================================================

@app.route('/citizen/dashboard')
@login_required
def citizen_dashboard():
    """Individual Citizen Dashboard: Displays ONLY this user's complaints and profile"""
    if session.get('user_type') != 'citizen':
        return redirect(url_for('authority_dashboard'))

    # Load only complaints belonging to current authenticated citizen
    user_complaints = Complaint.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Complaint.created_at.desc()).all()

    # Load notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Notification.created_at.desc()).all()

    # Stats for this user
    stats = {
        'total': len(user_complaints),
        'submitted': sum(1 for c in user_complaints if c.status == 'Submitted'),
        'under_review': sum(1 for c in user_complaints if c.status == 'Under Review'),
        'assigned': sum(1 for c in user_complaints if c.status == 'Assigned'),
        'in_progress': sum(1 for c in user_complaints if c.status == 'In Progress'),
        'resolved': sum(1 for c in user_complaints if c.status == 'Resolved'),
        'rejected': sum(1 for c in user_complaints if c.status == 'Rejected')
    }

    unread_count = sum(1 for n in notifications if not n.is_read)

    return render_template(
        'citizen_dashboard.html',
        complaints=user_complaints,
        notifications=notifications,
        stats=stats,
        unread_count=unread_count
    )

@app.route('/citizen/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update Citizen Name and Email"""
    if session.get('user_type') != 'citizen':
        abort(403)

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip() or None

    if name:
        current_user.name = name
        current_user.email = email
        db.session.commit()
        flash('Your profile details have been updated.', 'success')
    return redirect(url_for('citizen_dashboard'))

@app.route('/citizen/password/change', methods=['POST'])
@login_required
def change_password():
    """Change Citizen Password"""
    if session.get('user_type') != 'citizen':
        abort(403)

    current_pass = request.form.get('current_password', '').strip()
    new_pass = request.form.get('new_password', '').strip()

    if not current_user.check_password(current_pass):
        flash('Current password incorrect. Please try again.', 'danger')
    elif len(new_pass) < 6:
        flash('New password must be at least 6 characters.', 'danger')
    else:
        current_user.set_password(new_pass)
        db.session.commit()
        flash('Password updated successfully.', 'success')

    return redirect(url_for('citizen_dashboard'))

@app.route('/citizen/notification/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notif = Notification.query.filter_by(
        notification_id=notification_id, user_id=current_user.user_id
    ).first()
    if notif:
        notif.is_read = True
        db.session.commit()
    return redirect(url_for('citizen_dashboard'))

# =====================================================================
# CIVIC ISSUE REPORTING & TRACKING
# =====================================================================

@app.route('/report', methods=['GET', 'POST'])
def report_issue():
    """Common Complaint Reporting with Camera & GPS Integration"""
    # Enforce citizen login before submitting a grievance
    if not current_user.is_authenticated or session.get('user_type') != 'citizen':
        flash('Please sign in or register with your mobile number to report a civic issue.', 'info')
        return redirect(url_for('login', next=url_for('report_issue')))

    prefill_category = request.args.get('category', 'Waste Management')

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        readable_address = request.form.get('readable_address', '').strip()

        # Coordinates & GPS Accuracy
        try:
            latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
            longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
            location_accuracy = float(request.form.get('location_accuracy')) if request.form.get('location_accuracy') else None
        except ValueError:
            latitude, longitude, location_accuracy = None, None, None

        if not title or not category or not description or not readable_address:
            flash('Please complete all required fields (Category, Title, Description, and Address).', 'danger')
            return render_template('report_issue.html', prefill_category=category)

        # Handle Photograph: from either live camera capture (Base64) or file upload
        saved_image_filename = None
        camera_data = request.form.get('camera_captured_data', '').strip()

        if camera_data and camera_data.startswith('data:image'):
            try:
                header, encoded = camera_data.split(',', 1)
                image_bytes = base64.b64decode(encoded)
                saved_image_filename = f"cam_{uuid.uuid4().hex[:12]}.jpg"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_image_filename)
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
            except Exception as e:
                print('Error saving camera snapshot:', e)

        elif 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                ext = safe_name.rsplit('.', 1)[1].lower()
                saved_image_filename = f"up_{uuid.uuid4().hex[:12]}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_image_filename))

        # Generate Unique Tracking ID: SCC-[CAT]-[YYYYMMDD]-[RANDOM]
        cat_codes = {
            'Waste Management': 'WST',
            'Hospital Services': 'HSP',
            'Road Management': 'ROD'
        }
        code = cat_codes.get(category, 'CIV')
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        rand_suffix = str(uuid.uuid4().int)[:4]
        tracking_id = f"SCC-{code}-{date_str}-{rand_suffix}"

        # Create Complaint Record
        complaint = Complaint(
            tracking_id=tracking_id,
            user_id=current_user.user_id,
            category=category,
            title=title,
            description=description,
            image_path=saved_image_filename,
            latitude=latitude,
            longitude=longitude,
            location_accuracy=location_accuracy,
            readable_address=readable_address,
            status='Submitted',
            created_at=datetime.datetime.utcnow()
        )
        db.session.add(complaint)
        db.session.flush()

        # Create Initial Audit History Record
        history = ComplaintHistory(
            complaint_id=complaint.complaint_id,
            previous_status='None',
            new_status='Submitted',
            updated_by=f"Citizen ({current_user.name})",
            notes='Grievance submitted with supporting photographic and GPS evidence.',
            updated_at=datetime.datetime.utcnow()
        )
        db.session.add(history)

        # Create Notification for User
        notif = Notification(
            user_id=current_user.user_id,
            complaint_id=complaint.complaint_id,
            message=f"Grievance '{title}' submitted successfully. Your Tracking ID is {tracking_id}."
        )
        db.session.add(notif)
        db.session.commit()

        flash(f'Your complaint has been successfully registered! Unique Tracking ID: {tracking_id}', 'success')
        return redirect(url_for('track_issue', tracking_id=tracking_id))

    return render_template('report_issue.html', prefill_category=prefill_category)

@app.route('/track', defaults={'tracking_id': None})
@app.route('/track/<tracking_id>')
def track_issue(tracking_id):
    """Personal Complaint Tracking with Access Control Protection"""
    searched_id = tracking_id or request.args.get('tracking_id', '').strip()
    complaint = None

    if searched_id:
        found = Complaint.query.filter_by(tracking_id=searched_id).first()
        if found:
            # Privacy Enforcer: Only author or authority user can inspect the complaint
            if current_user.is_authenticated:
                if session.get('user_type') == 'authority' or found.user_id == current_user.user_id:
                    complaint = found
                else:
                    flash('Privacy Protection: You are not authorized to view another citizen\'s complaint.', 'danger')
                    return redirect(url_for('citizen_dashboard'))
            else:
                flash('Please log in with your mobile number to view your private complaint details.', 'info')
                return redirect(url_for('login', next=url_for('track_issue', tracking_id=searched_id)))
        else:
            flash(f'No complaint found with Tracking ID: {searched_id}. Please verify your ID.', 'warning')

    return render_template('track_issue.html', complaint=complaint, searched_id=searched_id)

# =====================================================================
# API ENDPOINTS (AI CATEGORIZATION & MAP DATA)
# =====================================================================

@app.route('/api/predict-category', methods=['POST'])
def api_predict():
    """Real-time AI Categorization API"""
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'category': 'Waste Management', 'confidence': 0.0, 'scores': {}})
    
    result = predict_complaint_category(text)
    return jsonify(result)

@app.route('/api/facilities')
def api_facilities():
    """Return JSON list of services/facilities for Leaflet map"""
    category = request.args.get('category', 'all')
    query = Service.query
    if category != 'all':
        query = query.filter_by(category=category)
    services_list = query.all()

    data = [{
        'service_id': s.service_id,
        'service_name': s.service_name,
        'category': s.category,
        'description': s.description,
        'address': s.address,
        'latitude': s.latitude,
        'longitude': s.longitude,
        'contact': s.contact,
        'operating_hours': s.operating_hours
    } for s in services_list]

    return jsonify(data)

@app.route('/api/complaints-map')
def api_complaints_map():
    """
    Returns generalized / anonymized complaint locations for public map.
    Protects citizen privacy by omitting personal names and exact street coordinates.
    """
    complaints = Complaint.query.filter(
        Complaint.latitude.isnot(None), Complaint.longitude.isnot(None)
    ).all()

    data = [{
        'complaint_id': c.complaint_id,
        'tracking_id': c.tracking_id,
        'category': c.category,
        'title': c.title,
        'description': c.description[:80] + '...' if len(c.description) > 80 else c.description,
        'latitude': round(c.latitude, 3), # Generalized to ~100m for privacy
        'longitude': round(c.longitude, 3),
        'readable_address': c.readable_address.split(',')[0], # Neighborhood only
        'status': c.status
    } for c in complaints]

    return jsonify(data)

# =====================================================================
# PROTECTED AUTHORITY MANAGEMENT PORTAL
# (No Admin button on Citizen Homepage)
# =====================================================================

@app.route('/authority/login', methods=['GET', 'POST'])
def authority_login():
    """Separate Protected Authority Authentication Portal"""
    if current_user.is_authenticated and session.get('user_type') == 'authority':
        return redirect(url_for('authority_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        auth_user = AuthorityUser.query.filter_by(username=username).first()
        if auth_user and auth_user.check_password(password):
            login_user(auth_user)
            session['user_type'] = 'authority'
            flash(f'Authority Console initialized. Signed in as {auth_user.username} ({auth_user.role}).', 'success')
            return redirect(url_for('authority_dashboard'))
        else:
            flash('Invalid authority credentials.', 'danger')

    return render_template('authority/login.html')

@app.route('/authority/logout')
def authority_logout():
    """Authority Logout"""
    logout_user()
    session.clear()
    flash('Authority session concluded.', 'info')
    return redirect(url_for('index'))

@app.route('/authority/dashboard')
@login_required
def authority_dashboard():
    """Authority Analytics & Overview Dashboard"""
    if session.get('user_type') != 'authority':
        abort(403)

    total_complaints = Complaint.query.count()
    waste_count = Complaint.query.filter_by(category='Waste Management').count()
    hospital_count = Complaint.query.filter_by(category='Hospital Services').count()
    road_count = Complaint.query.filter_by(category='Road Management').count()

    statuses = ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Rejected']
    status_breakdown = {st: Complaint.query.filter_by(status=st).count() for st in statuses}

    stats = {
        'total': total_complaints,
        'waste_count': waste_count,
        'hospital_count': hospital_count,
        'road_count': road_count,
        'status_breakdown': status_breakdown
    }

    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(8).all()
    return render_template('authority/dashboard.html', stats=stats, recent_complaints=recent_complaints)

@app.route('/authority/complaints')
@login_required
def authority_complaints():
    """Authority Complaints Management & Review"""
    if session.get('user_type') != 'authority':
        abort(403)

    category = request.args.get('category', 'All')
    status = request.args.get('status', 'All')
    search = request.args.get('search', '').strip()

    query = Complaint.query

    if category != 'All':
        query = query.filter_by(category=category)
    if status != 'All':
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            (Complaint.tracking_id.ilike(f'%{search}%')) |
            (Complaint.title.ilike(f'%{search}%')) |
            (Complaint.description.ilike(f'%{search}%')) |
            (Complaint.readable_address.ilike(f'%{search}%'))
        )

    complaints = query.order_by(Complaint.created_at.desc()).all()
    return render_template(
        'authority/complaints.html',
        complaints=complaints,
        active_category=category,
        active_status=status,
        search=search
    )

@app.route('/authority/complaint/update/<int:complaint_id>', methods=['POST'])
@login_required
def authority_update_complaint(complaint_id):
    """Authority updates status, logs history, and notifies citizen"""
    if session.get('user_type') != 'authority':
        abort(403)

    complaint = Complaint.query.get_or_404(complaint_id)
    new_status = request.form.get('status')
    notes = request.form.get('notes', '').strip()
    rejection_reason = request.form.get('rejection_reason', '').strip()

    previous_status = complaint.status
    complaint.status = new_status

    final_notes = notes
    if new_status == 'Rejected' and rejection_reason:
        final_notes = f"Rejection Reason: {rejection_reason}. {notes}".strip()

    # Create history entry
    hist = ComplaintHistory(
        complaint_id=complaint.complaint_id,
        previous_status=previous_status,
        new_status=new_status,
        updated_by=f"Officer {current_user.username}",
        notes=final_notes,
        updated_at=datetime.datetime.utcnow()
    )
    db.session.add(hist)

    # Notify Citizen
    notif_msg = f"Status update on {complaint.tracking_id} ('{complaint.title}'): Now '{new_status}'."
    if final_notes:
        notif_msg += f" Note: {final_notes}"

    notif = Notification(
        user_id=complaint.user_id,
        complaint_id=complaint.complaint_id,
        message=notif_msg
    )
    db.session.add(notif)
    db.session.commit()

    flash(f"Complaint {complaint.tracking_id} status updated to {new_status} and citizen notified.", 'success')
    return redirect(url_for('authority_complaints'))

@app.route('/authority/services')
@login_required
def authority_services():
    """Authority Service Facilities & Announcements Manager"""
    if session.get('user_type') != 'authority':
        abort(403)

    services_list = Service.query.order_by(Service.service_id.asc()).all()
    announcements_list = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('authority/manage_services.html', services=services_list, announcements=announcements_list)

@app.route('/authority/service/add', methods=['POST'])
@login_required
def authority_add_service():
    """Add new facility"""
    if session.get('user_type') != 'authority':
        abort(403)

    service = Service(
        service_name=request.form.get('service_name'),
        category=request.form.get('category'),
        description=request.form.get('description'),
        address=request.form.get('address'),
        latitude=float(request.form.get('latitude') or Config.DEFAULT_MAP_LAT),
        longitude=float(request.form.get('longitude') or Config.DEFAULT_MAP_LNG),
        contact=request.form.get('contact'),
        operating_hours=request.form.get('operating_hours')
    )
    db.session.add(service)
    db.session.commit()
    flash('Service facility added successfully.', 'success')
    return redirect(url_for('authority_services'))

@app.route('/authority/service/delete/<int:service_id>', methods=['POST'])
@login_required
def authority_delete_service(service_id):
    """Delete facility"""
    if session.get('user_type') != 'authority':
        abort(403)

    s = Service.query.get_or_404(service_id)
    db.session.delete(s)
    db.session.commit()
    flash('Facility deleted.', 'info')
    return redirect(url_for('authority_services'))

@app.route('/authority/announcement/add', methods=['POST'])
@login_required
def authority_add_announcement():
    """Publish municipal announcement"""
    if session.get('user_type') != 'authority':
        abort(403)

    ann = Announcement(
        title=request.form.get('title'),
        description=request.form.get('description'),
        category=request.form.get('category'),
        affected_area=request.form.get('affected_area')
    )
    db.session.add(ann)
    db.session.commit()
    flash('Announcement published successfully.', 'success')
    return redirect(url_for('authority_services'))

@app.route('/authority/announcement/delete/<int:announcement_id>', methods=['POST'])
@login_required
def authority_delete_announcement(announcement_id):
    """Delete announcement"""
    if session.get('user_type') != 'authority':
        abort(403)

    ann = Announcement.query.get_or_404(announcement_id)
    db.session.delete(ann)
    db.session.commit()
    flash('Announcement removed.', 'info')
    return redirect(url_for('authority_services'))

if __name__ == '__main__':
    # Start Flask Server
    app.run(debug=True, host='127.0.0.1', port=5000)
