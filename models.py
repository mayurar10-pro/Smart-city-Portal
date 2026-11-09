import sqlite3
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Admin Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')

    # 2. Service Facilities Table (Waste, Hospital, Road)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL, -- 'Waste Management', 'Hospital Services', 'Road Management'
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        contact_number TEXT,
        emergency_contact TEXT,
        operating_hours TEXT,
        status TEXT NOT NULL,
        details TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')

    # 3. Complaints Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracking_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL, -- 'Waste Management', 'Hospital Services', 'Road Management'
        predicted_category TEXT,
        confidence REAL,
        description TEXT NOT NULL,
        location_name TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        image_path TEXT,
        citizen_name TEXT,
        citizen_contact TEXT,
        status TEXT NOT NULL, -- 'Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Rejected'
        admin_notes TEXT,
        rejection_reason TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')

    # 4. Announcements Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL, -- 'Waste Management', 'Hospital Services', 'Road Management', 'General'
        content TEXT NOT NULL,
        priority TEXT NOT NULL, -- 'Normal', 'Important', 'Emergency'
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

def seed_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if admin exists
    cursor.execute('SELECT COUNT(*) as count FROM admins WHERE username = ?', (Config.ADMIN_USERNAME,))
    if cursor.fetchone()['count'] == 0:
        cursor.execute('''
        INSERT INTO admins (username, password_hash, full_name, created_at)
        VALUES (?, ?, ?, ?)
        ''', (
            Config.ADMIN_USERNAME,
            generate_password_hash(Config.ADMIN_PASSWORD),
            'Municipal Administrator',
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))

    # Check if facilities exist
    cursor.execute('SELECT COUNT(*) as count FROM facilities')
    if cursor.fetchone()['count'] == 0:
        facilities_data = [
            # Waste Management
            ('Waste Management', 'Central Solid Waste Processing Plant', '8th Main, Koramangala 4th Block, Bengaluru', '080-25530112', '1800-425-5001', 'Daily 6:00 AM - 2:00 PM', 'Operational', 'Dry & wet organic waste processing, mechanical composting, daily collection fleet hub.', 12.9352, 77.6245),
            ('Waste Management', 'Indiranagar Dry Waste Collection Centre', '100ft Road, HAL 2nd Stage, Indiranagar, Bengaluru', '080-25219944', '1800-425-5001', 'Mon-Sat 7:00 AM - 4:00 PM', 'Operational', 'Electronic waste, plastic sorting, paper baling, and neighborhood recycling drop-off.', 12.9784, 77.6408),
            ('Waste Management', 'Jayanagar Community Bio-Digester & Disposal Depot', '32nd Cross, 4th Block, Jayanagar, Bengaluru', '080-26638890', '1800-425-5001', 'Daily 6:30 AM - 1:30 PM', 'Operational', 'Biogas generation from kitchen organic refuse, local ward wet waste receiving station.', 12.9298, 77.5833),
            ('Waste Management', 'Malleshwaram Ward 150 Resource Recovery Facility', '15th Cross, Margosa Road, Malleshwaram, Bengaluru', '080-23345512', '1800-425-5001', 'Mon-Sun 6:00 AM - 3:00 PM', 'Operational', 'Dedicated segregation center, compost pickup counter for citizens, zero-landfill pilot center.', 12.9982, 77.5711),
            ('Waste Management', 'Whitefield Automated Waste Compactor Station', 'ITPL Main Road, Hope Farm Junction, Whitefield, Bengaluru', '080-28456671', '1800-425-5001', '24/7 Automated', 'Operational', 'High-capacity hydraulic compactors, covered transfer containers preventing leakage and odor.', 12.9855, 77.7432),

            # Hospital Services
            ('Hospital Services', 'Victoria Multi-Speciality Government Hospital', 'Fort Road, Near City Market, Kalasipalya, Bengaluru', '080-26701150', '108 / 080-26701155', '24/7 Emergency & Inpatient', 'Operational', 'Verified 24/7 Trauma Care, 150 ICU Beds, Emergency Surgery, Cardiology, Burns Ward & Blood Bank.', 12.9629, 77.5753),
            ('Hospital Services', 'Bowring & Lady Curzon Civil Hospital', 'Lady Curzon Road, Tasker Town, Shivajinagar, Bengaluru', '080-25591325', '108 / 080-25591320', '24/7 Emergency Services', 'Operational', '24/7 Casualty Desk, Pediatrics, Gynecology, General Medicine, Diagnostic Imaging & Dialysis.', 12.9822, 77.6047),
            ('Hospital Services', 'KC General District Hospital', '5th Cross, Malleshwaram West, Bengaluru', '080-23341771', '108 / 080-23341770', '24/7 Emergency Ward', 'Operational', 'Maternity wing, Neonatal ICU, Orthopedic trauma, round-the-clock pharmacy and oxygen ward.', 13.0034, 77.5684),
            ('Hospital Services', 'Jayanagar General Government Hospital', 'Near 4th T Block Bus Stand, Jayanagar, Bengaluru', '080-26563355', '108 / 080-26563350', '24/7 Casualty & OPD', 'Operational', 'Cardiac ICU, Ophthalmology, Nephrology, 24-hour pathology lab and free Jan Aushadhi generic pharmacy.', 12.9234, 77.5902),
            ('Hospital Services', 'Sri Jayadeva Institute of Cardiovascular Sciences', 'Bannerghatta Main Road, Jayanagar 9th Block, Bengaluru', '080-22977400', '108 / 080-22977500', '24/7 Cardiac Emergency', 'Operational', 'Premier heart institute, emergency cath labs, dedicated pediatric cardiology, 24/7 CCU.', 12.9198, 77.5991),

            # Road Management
            ('Road Management', 'Outer Ring Road (Silk Board - Marathahalli Corridor)', 'Central Silk Board to Marathahalli Flyover, Bengaluru', '080-22942222', '080-22943333', '24/7 Traffic Surveillance', 'Moderate / Surface Repairs', 'Continuous asphalt patching underway between Bellandur & Kadubeesanahalli. Speed limit 40 km/h.', 12.9279, 77.6833),
            ('Road Management', 'MG Road & Brigade Road Commercial Boulevard', 'MG Road Metro Station to Trinity Circle, Bengaluru', '080-22942444', '080-22942222', '24/7 Monitored', 'Good Condition', 'Newly resurfaced bituminous asphalt, smart traffic signaling, clear pedestrian walkways.', 12.9756, 77.6066),
            ('Road Management', 'Old Airport Road Infrastructure Work Zone', 'Domlur Flyover to HAL Main Gate, Bengaluru', '080-22942555', '080-22942222', 'Active Repair Zone', 'Under Maintenance', 'Night pothole filling and storm-drain concrete reinforcement. Restricted lanes 11:00 PM to 5:00 AM.', 12.9611, 77.6481),
            ('Road Management', 'West of Chord Arterial Road Section', 'Rajajinagar 1st Block to Mahalakshmi Layout, Bengaluru', '080-22942666', '080-22942222', '24/7 Monitored', 'Good Condition', 'Reinforced manhole covers installed, reflective lane markings repainted, zero reported potholes.', 13.0078, 77.5519),
            ('Road Management', 'Bannerghatta Main Road Transit Stretch', 'Dairy Circle to Sagar Hospital Junction, Bengaluru', '080-22942777', '080-22942222', 'Caution / Metro Digging', 'Caution Advised', 'Underground utility pipeline work near Guruguntepalya junction. Commuters urged to follow diversions.', 12.9321, 77.5982)
        ]

        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for fac in facilities_data:
            cursor.execute('''
            INSERT INTO facilities (category, name, address, contact_number, emergency_contact, operating_hours, status, details, latitude, longitude, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*fac, now))

    # Check if announcements exist
    cursor.execute('SELECT COUNT(*) as count FROM announcements')
    if cursor.fetchone()['count'] == 0:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        announcements_data = [
            ('Door-to-Door Wet & Dry Waste Segregation Drive', 'Waste Management', 'Citizens are requested to segregate waste into dry, wet, and sanitary categories before 7:30 AM handover. Free green composting bins are available at ward offices.', 'Important', 1, now),
            ('24/7 Emergency Hospital & Cardiac Desks Operational', 'Hospital Services', 'All city government hospitals have updated emergency contact desks and ambulance units. In any critical health emergency, call 108 or direct hospital helplines immediately.', 'Emergency', 1, now),
            ('Night Resurfacing & Pothole Repair on Old Airport Road', 'Road Management', 'Road maintenance teams are carrying out nocturnal asphalt resurfacing from 11:00 PM to 5:00 AM. Commuters are advised to exercise caution and heed detour signs.', 'Important', 1, now),
            ('Monsoon Road Drainage Clearing & Pothole Alert Portal', 'Road Management', 'SmartCity Connect portal enables instant pothole reporting with photo geotagging. Emergency road teams deployed for 48-hour resolution of critical potholes.', 'Normal', 1, now)
        ]
        for ann in announcements_data:
            cursor.execute('''
            INSERT INTO announcements (title, category, content, priority, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', ann)

    # Check if sample complaints exist
    cursor.execute('SELECT COUNT(*) as count FROM complaints')
    if cursor.fetchone()['count'] == 0:
        sample_complaints = [
            ('SCC-WST-20261101-1001', 'Overflowing community garbage dumpster on 4th Main', 'Waste Management', 'Waste Management', 98.5, 'Large community dumpster overflowing for two consecutive days. Stray dogs scattering garbage onto walking path.', 'Near 4th Main Junction, Koramangala 3rd Block', 12.9344, 77.6211, None, 'Ramesh Kumar', '9876543210', 'Resolved', 'Sanitation truck #KA-01-EA-4412 cleared 1.5 tons of garbage and sanitized the spot with lime powder.', None, '2026-11-01 09:15:00', '2026-11-02 11:30:00'),
            ('SCC-HSP-20261103-1002', 'Outdated emergency contact number on hospital card', 'Hospital Services', 'Hospital Services', 97.2, 'The emergency room telephone number listed for Jayanagar General casualty was ringing dead during emergency.', 'Jayanagar General Hospital premises', 12.9234, 77.5902, None, 'Dr. Ananya Rao', '9845112233', 'Resolved', 'Hospital administrative liaison verified the landline wiring fault and updated primary line to 080-26563355.', None, '2026-11-03 14:20:00', '2026-11-04 10:10:00'),
            ('SCC-ROD-20261105-1003', 'Deep pothole after rain near metro pillar 142', 'Road Management', 'Road Management', 99.4, 'Dangerous crater-like pothole in middle lane causing sudden braking and two-wheeler skids in rain.', 'Outer Ring Road near Bellandur EcoSpace', 12.9288, 77.6845, None, 'Vikram Simha', '9900112244', 'In Progress', 'Assigned to Ward Road Maintenance Unit 4. Cold-mix asphalt patch scheduled for evening lull.', None, '2026-11-05 16:45:00', '2026-11-06 09:00:00'),
            ('SCC-WST-20261107-1004', 'Commercial restaurant waste dumped in public alley', 'Waste Management', 'Waste Management', 95.8, 'Illegal dumping of food waste bags behind supermarket. Severe odor and flies in residential area.', 'HAL 2nd Stage, Indiranagar', 12.9790, 77.6415, None, 'Sangeetha B', '9880011223', 'Assigned', 'Sanitation inspector assigned to inspect premises and issue compliance notice to business owner.', None, '2026-11-07 10:10:00', '2026-11-07 11:00:00'),
            ('SCC-ROD-20261108-1005', 'Broken manhole slab near bus shelter', 'Road Management', 'Road Management', 96.1, 'Concrete manhole cover broken and left partially uncovered, hazardous for pedestrians walking at dusk.', 'Margosa Road, Malleshwaram 15th Cross', 12.9989, 77.5715, None, 'Kishore Hegde', '9740123456', 'Under Review', 'Civil engineer visiting site for measurement and replacement with heavy-duty cast iron cover.', None, '2026-11-08 08:30:00', '2026-11-08 09:15:00'),
            ('SCC-HSP-20261109-1006', 'Request for private clinic medical billing dispute', 'Hospital Services', 'Hospital Services', 88.0, 'Dispute regarding private clinic consultation fee charges for routine checkup.', 'Private Clinic, MG Road', 12.9750, 77.6070, None, 'Anonymous', '9123456789', 'Rejected', None, 'Private billing grievances outside municipal jurisdiction. Directed complainant to State Consumer Redressal Forum.', '2026-11-09 11:00:00', '2026-11-09 12:00:00')
        ]

        for cmp in sample_complaints:
            cursor.execute('''
            INSERT INTO complaints (tracking_id, title, category, predicted_category, confidence, description, location_name, latitude, longitude, image_path, citizen_name, citizen_contact, status, admin_notes, rejection_reason, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', cmp)

    conn.commit()
    conn.close()

# Helper queries
def get_all_complaints(category=None, status=None, search=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM complaints WHERE 1=1'
    params = []
    
    if category and category != 'All':
        query += ' AND category = ?'
        params.append(category)
        
    if status and status != 'All':
        query += ' AND status = ?'
        params.append(status)
        
    if search:
        query += ' AND (tracking_id LIKE ? OR title LIKE ? OR description LIKE ? OR location_name LIKE ?)'
        term = f'%{search}%'
        params.extend([term, term, term, term])
        
    query += ' ORDER BY id DESC'
    cursor.execute(query, params)
    complaints = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return complaints

def get_complaint_by_tracking_id(tracking_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM complaints WHERE tracking_id = ?', (tracking_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_complaint_by_id(complaint_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def insert_complaint(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
    INSERT INTO complaints (
        tracking_id, title, category, predicted_category, confidence,
        description, location_name, latitude, longitude, image_path,
        citizen_name, citizen_contact, status, admin_notes, rejection_reason,
        created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['tracking_id'],
        data['title'],
        data['category'],
        data.get('predicted_category', data['category']),
        data.get('confidence', 0.0),
        data['description'],
        data['location_name'],
        data.get('latitude'),
        data.get('longitude'),
        data.get('image_path'),
        data.get('citizen_name', 'Anonymous Citizen'),
        data.get('citizen_contact', ''),
        data.get('status', 'Submitted'),
        data.get('admin_notes', ''),
        data.get('rejection_reason', ''),
        now,
        now
    ))
    complaint_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return complaint_id

def update_complaint_status(complaint_id, status, admin_notes=None, rejection_reason=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
    UPDATE complaints
    SET status = ?, admin_notes = COALESCE(?, admin_notes), rejection_reason = ?, updated_at = ?
    WHERE id = ?
    ''', (status, admin_notes, rejection_reason, now, complaint_id))
    
    conn.commit()
    conn.close()

def get_facilities(category=None, search=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM facilities WHERE 1=1'
    params = []
    
    if category and category != 'All':
        query += ' AND category = ?'
        params.append(category)
        
    if search:
        query += ' AND (name LIKE ? OR address LIKE ? OR details LIKE ?)'
        term = f'%{search}%'
        params.extend([term, term, term])
        
    query += ' ORDER BY id ASC'
    cursor.execute(query, params)
    facilities = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return facilities

def get_facility_by_id(facility_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM facilities WHERE id = ?', (facility_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def insert_facility(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO facilities (category, name, address, contact_number, emergency_contact, operating_hours, status, details, latitude, longitude, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['category'],
        data['name'],
        data['address'],
        data.get('contact_number', ''),
        data.get('emergency_contact', ''),
        data.get('operating_hours', 'Regular Hours'),
        data.get('status', 'Operational'),
        data.get('details', ''),
        data.get('latitude', Config.DEFAULT_MAP_LAT),
        data.get('longitude', Config.DEFAULT_MAP_LNG),
        now
    ))
    fid = cursor.lastrowid
    conn.commit()
    conn.close()
    return fid

def update_facility(facility_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE facilities
    SET category = ?, name = ?, address = ?, contact_number = ?, emergency_contact = ?,
        operating_hours = ?, status = ?, details = ?, latitude = ?, longitude = ?
    WHERE id = ?
    ''', (
        data['category'],
        data['name'],
        data['address'],
        data.get('contact_number', ''),
        data.get('emergency_contact', ''),
        data.get('operating_hours', 'Regular Hours'),
        data.get('status', 'Operational'),
        data.get('details', ''),
        data.get('latitude', Config.DEFAULT_MAP_LAT),
        data.get('longitude', Config.DEFAULT_MAP_LNG),
        facility_id
    ))
    conn.commit()
    conn.close()

def delete_facility(facility_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM facilities WHERE id = ?', (facility_id,))
    conn.commit()
    conn.close()

def get_announcements(category=None, active_only=True):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM announcements WHERE 1=1'
    params = []
    
    if active_only:
        query += ' AND is_active = 1'
        
    if category and category != 'All':
        query += ' AND (category = ? OR category = "General")'
        params.append(category)
        
    query += ' ORDER BY id DESC'
    cursor.execute(query, params)
    announcements = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return announcements

def insert_announcement(title, category, content, priority='Normal'):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO announcements (title, category, content, priority, is_active, created_at)
    VALUES (?, ?, ?, ?, 1, ?)
    ''', (title, category, content, priority, now))
    aid = cursor.lastrowid
    conn.commit()
    conn.close()
    return aid

def delete_announcement(announcement_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM announcements WHERE id = ?', (announcement_id,))
    conn.commit()
    conn.close()

def get_analytics_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total counts
    cursor.execute('SELECT COUNT(*) as total FROM complaints')
    total_complaints = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as resolved FROM complaints WHERE status = 'Resolved'")
    resolved_complaints = cursor.fetchone()['resolved']

    cursor.execute("SELECT COUNT(*) as pending FROM complaints WHERE status NOT IN ('Resolved', 'Rejected')")
    pending_complaints = cursor.fetchone()['pending']

    cursor.execute('SELECT COUNT(*) as facilities_count FROM facilities')
    total_facilities = cursor.fetchone()['facilities_count']

    # By category
    cursor.execute('''
    SELECT category, COUNT(*) as count 
    FROM complaints 
    GROUP BY category
    ''')
    by_category = {row['category']: row['count'] for row in cursor.fetchall()}
    # Ensure all 3 categories exist
    for cat in ['Waste Management', 'Hospital Services', 'Road Management']:
        by_category.setdefault(cat, 0)

    # By status
    cursor.execute('''
    SELECT status, COUNT(*) as count 
    FROM complaints 
    GROUP BY status
    ''')
    by_status = {row['status']: row['count'] for row in cursor.fetchall()}
    for st in ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Rejected']:
        by_status.setdefault(st, 0)

    conn.close()
    return {
        'total': total_complaints,
        'resolved': resolved_complaints,
        'pending': pending_complaints,
        'facilities_count': total_facilities,
        'by_category': by_category,
        'by_status': by_status
    }
