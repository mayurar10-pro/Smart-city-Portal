import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# =====================================================================
# 1. Citizen Users Table
# =====================================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    mobile_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    complaints = db.relationship('Complaint', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic', cascade='all, delete-orphan')

    def get_id(self):
        # Format user session ID for Flask-Login
        return f"user_{self.user_id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.mobile_number} - {self.name}>"

# =====================================================================
# 2. Authority Users Table (Protected Setup)
# =====================================================================
class AuthorityUser(UserMixin, db.Model):
    __tablename__ = 'authority_users'

    authority_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='Municipal Officer')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def get_id(self):
        return f"auth_{self.authority_id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<AuthorityUser {self.username} - {self.role}>"

# =====================================================================
# 3. Complaints Table
# =====================================================================
class Complaint(db.Model):
    __tablename__ = 'complaints'

    complaint_id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Waste Management, Hospital Services, Road Management
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_accuracy = db.Column(db.Float, nullable=True)  # in meters
    readable_address = db.Column(db.String(300), nullable=False)
    status = db.Column(db.String(50), default='Submitted', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    history = db.relationship('ComplaintHistory', backref='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='ComplaintHistory.updated_at.desc()')
    notifications = db.relationship('Notification', backref='complaint', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Complaint {self.tracking_id} - {self.category} - {self.status}>"

# =====================================================================
# 4. Complaint History Table (Status Transition Audit Log)
# =====================================================================
class ComplaintHistory(db.Model):
    __tablename__ = 'complaint_history'

    history_id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.complaint_id'), nullable=False)
    previous_status = db.Column(db.String(50), nullable=False)
    new_status = db.Column(db.String(50), nullable=False)
    updated_by = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<History {self.complaint_id}: {self.previous_status} -> {self.new_status}>"

# =====================================================================
# 5. Services Table (Waste, Hospital, Road facilities)
# =====================================================================
class Service(db.Model):
    __tablename__ = 'services'

    service_id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Waste Management, Hospital Services, Road Management
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    contact = db.Column(db.String(100), nullable=True)
    operating_hours = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Property aliases for backward compatibility with templates
    @property
    def name(self):
        return self.service_name

    @property
    def details(self):
        return self.description

    @property
    def contact_number(self):
        return self.contact

    @property
    def emergency_contact(self):
        return self.contact

    @property
    def status(self):
        return 'Operational'

    def __repr__(self):
        return f"<Service {self.service_name} ({self.category})>"

# =====================================================================
# 6. Announcements Table
# =====================================================================
class Announcement(db.Model):
    __tablename__ = 'announcements'

    announcement_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Waste Management, Hospital Services, Road Management, General
    affected_area = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)

    @property
    def content(self):
        return self.description

    @property
    def priority(self):
        return 'Important'

    def __repr__(self):
        return f"<Announcement {self.title}>"

# =====================================================================
# 7. Notifications Table
# =====================================================================
class Notification(db.Model):
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.complaint_id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Notification for User {self.user_id}: {self.message[:30]}>"

# =====================================================================
# 8. Mobile OTP Verification Table
# =====================================================================
class OTPVerification(db.Model):
    __tablename__ = 'otp_verifications'

    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(20), nullable=False, index=True)
    otp_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def set_otp(self, plain_otp):
        self.otp_hash = generate_password_hash(str(plain_otp))

    def verify_otp(self, candidate_otp):
        if self.is_used or datetime.datetime.utcnow() > self.expires_at:
            return False
        return check_password_hash(self.otp_hash, str(candidate_otp).strip())


# =====================================================================
# Seeding Helper Functions
# =====================================================================
def seed_initial_data(config):
    """Seed authority credentials, demo citizen, services, and announcements"""
    # 1. Authority User
    auth_user = AuthorityUser.query.filter_by(username=config.DEFAULT_AUTHORITY_USERNAME).first()
    if not auth_user:
        auth_user = AuthorityUser(
            username=config.DEFAULT_AUTHORITY_USERNAME,
            role=config.DEFAULT_AUTHORITY_ROLE
        )
        auth_user.set_password(config.DEFAULT_AUTHORITY_PASSWORD)
        db.session.add(auth_user)

    # 2. Demo Citizen User (Ramesh Kumar - 9876543210)
    demo_citizen = User.query.filter_by(mobile_number='9876543210').first()
    if not demo_citizen:
        demo_citizen = User(
            name='Ramesh Kumar',
            mobile_number='9876543210',
            email='ramesh.kumar@example.com',
            is_verified=True,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=7)
        )
        demo_citizen.set_password('CitizenPass@2026')
        db.session.add(demo_citizen)
        db.session.flush()

        # Seed sample complaints for the demo citizen
        sample_complaints = [
            (
                'SCC-WST-20261102-1001',
                'Waste Management',
                'Overflowing Community Garbage Bin on 4th Main',
                'Community dumpster is completely overflowing and waste is scattered onto pedestrian walkway. Foul odor.',
                'Near 4th Main Junction, Koramangala 3rd Block, Bengaluru',
                12.9344, 77.6211, 15.0,
                'Resolved',
                datetime.datetime.utcnow() - datetime.timedelta(days=6)
            ),
            (
                'SCC-ROD-20261105-1002',
                'Road Management',
                'Dangerous Deep Pothole Near EcoSpace Flyover',
                'Pothole filled with rainwater causing two-wheelers to slip. Needs urgent bituminous asphalt patching.',
                'Outer Ring Road near Bellandur EcoSpace, Bengaluru',
                12.9288, 77.6845, 12.0,
                'In Progress',
                datetime.datetime.utcnow() - datetime.timedelta(days=3)
            ),
            (
                'SCC-HSP-20261108-1003',
                'Hospital Services',
                'Outdated Emergency Telephone Line for Casualty Desk',
                'The landline number listed for Jayanagar General casualty was disconnected during late night medical inquiry.',
                'Jayanagar General Hospital premises, Bengaluru',
                12.9234, 77.5902, 20.0,
                'Under Review',
                datetime.datetime.utcnow() - datetime.timedelta(days=1)
            )
        ]

        for trk_id, cat, title, desc, addr, lat, lng, acc, st, dt in sample_complaints:
            cmp = Complaint(
                tracking_id=trk_id,
                user_id=demo_citizen.user_id,
                category=cat,
                title=title,
                description=desc,
                readable_address=addr,
                latitude=lat,
                longitude=lng,
                location_accuracy=acc,
                status=st,
                created_at=dt
            )
            db.session.add(cmp)
            db.session.flush()

            # Add History
            hist1 = ComplaintHistory(
                complaint_id=cmp.complaint_id,
                previous_status='None',
                new_status='Submitted',
                updated_by='Citizen Portal',
                notes='Citizen lodged complaint via mobile app with GPS geotag.',
                updated_at=dt
            )
            db.session.add(hist1)

            if st in ['Under Review', 'In Progress', 'Resolved']:
                hist2 = ComplaintHistory(
                    complaint_id=cmp.complaint_id,
                    previous_status='Submitted',
                    new_status='Under Review',
                    updated_by='Ward Engineer Desk',
                    notes='Complaint verified and routed to field technical inspection squad.',
                    updated_at=dt + datetime.timedelta(hours=4)
                )
                db.session.add(hist2)

            if st in ['In Progress', 'Resolved']:
                hist3 = ComplaintHistory(
                    complaint_id=cmp.complaint_id,
                    previous_status='Under Review',
                    new_status='In Progress',
                    updated_by='Field Action Crew',
                    notes='Field repair vehicle dispatched with material.',
                    updated_at=dt + datetime.timedelta(hours=18)
                )
                db.session.add(hist3)

            if st == 'Resolved':
                hist4 = ComplaintHistory(
                    complaint_id=cmp.complaint_id,
                    previous_status='In Progress',
                    new_status='Resolved',
                    updated_by='Zonal Supervisor',
                    notes='Sanitation truck cleared 1.5 tons of debris and sanitized the spot with lime.',
                    updated_at=dt + datetime.timedelta(hours=36)
                )
                db.session.add(hist4)

                # Add notification
                notif = Notification(
                    user_id=demo_citizen.user_id,
                    complaint_id=cmp.complaint_id,
                    message=f"Good news! Your complaint {trk_id} ('{title}') has been Resolved by municipal teams.",
                    is_read=False,
                    created_at=dt + datetime.timedelta(hours=36)
                )
                db.session.add(notif)

    # 3. Seed Core Services (Waste, Hospital, Road)
    if Service.query.count() == 0:
        services_data = [
            # Waste Management
            ('Central Solid Waste Processing Plant', 'Waste Management', 'Mechanical composting, daily collection hub, dry and wet segregation facility.', '8th Main, Koramangala 4th Block, Bengaluru', 12.9352, 77.6245, '080-25530112', 'Daily 6:00 AM - 2:00 PM'),
            ('Indiranagar Dry Waste Collection Centre', 'Waste Management', 'Neighborhood recycling, plastic sorting, e-waste drop-off counter.', '100ft Road, HAL 2nd Stage, Indiranagar, Bengaluru', 12.9784, 77.6408, '080-25219944', 'Mon-Sat 7:00 AM - 4:00 PM'),
            ('Jayanagar Community Bio-Digester Depot', 'Waste Management', 'Biogas generation from kitchen organic refuse, ward collection depot.', '32nd Cross, 4th Block, Jayanagar, Bengaluru', 12.9298, 77.5833, '080-26638890', 'Daily 6:30 AM - 1:30 PM'),
            ('Malleshwaram Resource Recovery Facility', 'Waste Management', 'Zero-landfill pilot depot, citizen compost pickup counter.', '15th Cross, Margosa Road, Malleshwaram, Bengaluru', 12.9982, 77.5711, '080-23345512', 'Mon-Sun 6:00 AM - 3:00 PM'),
            ('Whitefield Automated Compactor Station', 'Waste Management', 'High-capacity hydraulic compactors, covered transfer containers.', 'ITPL Main Road, Hope Farm Junction, Whitefield, Bengaluru', 12.9855, 77.7432, '080-28456671', '24/7 Automated'),

            # Hospital Services
            ('Victoria Multi-Speciality Government Hospital', 'Hospital Services', 'Verified 24/7 Trauma Care, 150 ICU Beds, Emergency Surgery, Cardiology & Blood Bank.', 'Fort Road, Near City Market, Kalasipalya, Bengaluru', 12.9629, 77.5753, '108 / 080-26701150', '24/7 Emergency & Inpatient'),
            ('Bowring & Lady Curzon Civil Hospital', 'Hospital Services', '24/7 Casualty Desk, Pediatrics, Gynecology, General Medicine, Diagnostic Imaging & Dialysis.', 'Lady Curzon Road, Tasker Town, Shivajinagar, Bengaluru', 12.9822, 77.6047, '108 / 080-25591325', '24/7 Emergency Services'),
            ('KC General District Hospital', 'Hospital Services', 'Maternity wing, Neonatal ICU, Orthopedic trauma, round-the-clock pharmacy.', '5th Cross, Malleshwaram West, Bengaluru', 13.0034, 77.5684, '108 / 080-23341771', '24/7 Emergency Ward'),
            ('Jayanagar General Government Hospital', 'Hospital Services', 'Cardiac ICU, Ophthalmology, Nephrology, 24-hour pathology lab and free generic pharmacy.', 'Near 4th T Block Bus Stand, Jayanagar, Bengaluru', 12.9234, 77.5902, '108 / 080-26563355', '24/7 Casualty & OPD'),
            ('Sri Jayadeva Institute of Cardiovascular Sciences', 'Hospital Services', 'Premier cardiac institute, emergency cath labs, pediatric cardiology, 24/7 CCU.', 'Bannerghatta Main Road, Jayanagar 9th Block, Bengaluru', 12.9198, 77.5991, '108 / 080-22977400', '24/7 Cardiac Emergency'),

            # Road Management
            ('Outer Ring Road (Silk Board - Marathahalli)', 'Road Management', 'Continuous asphalt patching underway between Bellandur & Kadubeesanahalli. Speed limit 40 km/h.', 'Central Silk Board to Marathahalli Flyover, Bengaluru', 12.9279, 77.6833, '080-22942222', '24/7 Traffic Surveillance'),
            ('MG Road & Brigade Commercial Boulevard', 'Road Management', 'Newly resurfaced bituminous asphalt, smart traffic signaling, clear pedestrian walkways.', 'MG Road Metro Station to Trinity Circle, Bengaluru', 12.9756, 77.6066, '080-22942444', '24/7 Monitored - Good Condition'),
            ('Old Airport Road Repair Corridor', 'Road Management', 'Night pothole filling and storm-drain concrete reinforcement. Restricted lanes 11:00 PM - 5:00 AM.', 'Domlur Flyover to HAL Main Gate, Bengaluru', 12.9611, 77.6481, '080-22942555', 'Active Repair Zone'),
            ('West of Chord Arterial Section', 'Road Management', 'Reinforced manhole covers installed, reflective lane markings repainted, zero reported potholes.', 'Rajajinagar 1st Block to Mahalakshmi Layout, Bengaluru', 13.0078, 77.5519, '080-22942666', '24/7 Monitored - Good Condition'),
            ('Bannerghatta Main Road Transit Stretch', 'Road Management', 'Underground utility pipeline work near Guruguntepalya junction. Commuters urged to follow diversions.', 'Dairy Circle to Sagar Hospital Junction, Bengaluru', 12.9321, 77.5982, '080-22942777', 'Caution - Work In Progress')
        ]

        for s_name, cat, desc, addr, lat, lng, cont, hrs in services_data:
            s = Service(
                service_name=s_name,
                category=cat,
                description=desc,
                address=addr,
                latitude=lat,
                longitude=lng,
                contact=cont,
                operating_hours=hrs
            )
            db.session.add(s)

    # 4. Seed Announcements
    if Announcement.query.count() == 0:
        announcements_data = [
            (
                'Door-to-Door Wet & Dry Waste Segregation Drive',
                'Citizens are requested to segregate waste into dry, wet, and sanitary categories before 7:30 AM handover. Free composting bins are available at ward offices.',
                'Waste Management',
                'All 198 Municipal Wards',
                datetime.datetime.utcnow() - datetime.timedelta(days=1),
                datetime.datetime.utcnow() + datetime.timedelta(days=30)
            ),
            (
                '24/7 Emergency Hospital & Cardiac Desks Operational',
                'All city government hospitals have updated emergency contact desks and ambulance units. In any critical health emergency, call 108 or direct hospital helplines immediately.',
                'Hospital Services',
                'Citywide Health Centers',
                datetime.datetime.utcnow() - datetime.timedelta(days=2),
                datetime.datetime.utcnow() + datetime.timedelta(days=60)
            ),
            (
                'Night Resurfacing & Pothole Repair on Old Airport Road',
                'Road maintenance teams are carrying out nocturnal asphalt resurfacing from 11:00 PM to 5:00 AM. Commuters are advised to exercise caution and heed detour signs.',
                'Road Management',
                'Old Airport Road - Domlur Corridor',
                datetime.datetime.utcnow() - datetime.timedelta(hours=12),
                datetime.datetime.utcnow() + datetime.timedelta(days=7)
            ),
            (
                'Monsoon 48-Hour Rapid Pothole Patching Program',
                'Citizens can report potholes with camera photographs and GPS geotags. Emergency flying squads deployed for 48-hour resolution of critical potholes.',
                'Road Management',
                'Major Arterial & Ring Roads',
                datetime.datetime.utcnow() - datetime.timedelta(hours=6),
                datetime.datetime.utcnow() + datetime.timedelta(days=45)
            )
        ]

        for title, desc, cat, area, c_at, e_at in announcements_data:
            ann = Announcement(
                title=title,
                description=desc,
                category=cat,
                affected_area=area,
                created_at=c_at,
                expires_at=e_at
            )
            db.session.add(ann)

    db.session.commit()
