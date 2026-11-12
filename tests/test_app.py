import os
import unittest
import json
import base64
import io
import datetime

from app import app
from models import db, User, AuthorityUser, Complaint, ComplaintHistory, Service, Announcement, Notification, OTPVerification, seed_initial_data
from ml.train_model import predict_complaint_category

class SmartCityConnectComprehensiveTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.test_db_path = os.path.join(app.config['INSTANCE_DIR'], 'test_smartcity.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.test_db_path}'
        app.config['SECRET_KEY'] = 'test-secret-key-2026'
        db.init_app(app)
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            seed_initial_data(app.config)

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        # Restore production database path
        prod_db_path = os.path.join(app.config['INSTANCE_DIR'], 'smartcity.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{prod_db_path}'
        db.init_app(app)

    def test_01_homepage_three_cards_only(self):
        """Verify homepage strictly renders only the 3 core service cards"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        self.assertIn('Waste Management', html)
        self.assertIn('Hospital Services', html)
        self.assertIn('Road Management', html)

        # Ensure no other service cards exist
        self.assertNotIn('Water Supply Management', html)
        self.assertNotIn('Drainage Management', html)
        self.assertNotIn('Streetlight Management', html)

    def test_02_citizen_registration_and_login_workflow(self):
        """Test registration and automatic direct login without OTP"""
        # Register new citizen
        reg_data = {
            'name': 'Priya Sharma',
            'mobile_number': '9845123456',
            'email': 'priya.sharma@example.com',
            'password': 'SecurePassword@2026',
            'confirm_password': 'SecurePassword@2026'
        }
        res_reg = self.client.post('/register', data=reg_data, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)
        self.assertIn('My Citizen Dashboard', res_reg.data.decode('utf-8'))
        self.assertIn('Priya Sharma', res_reg.data.decode('utf-8'))

        with app.app_context():
            # Check user was created and activated
            user = User.query.filter_by(mobile_number='9845123456').first()
            self.assertIsNotNone(user)
            self.assertTrue(user.is_verified)

    def test_03_citizen_mobile_login(self):
        """Test login with mobile number and password"""
        # Pre-seeded demo user: 9876543210 / CitizenPass@2026
        login_data = {
            'mobile_number': '9876543210',
            'password': 'CitizenPass@2026'
        }
        res = self.client.post('/login', data=login_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('My Citizen Dashboard', res.data.decode('utf-8'))
        self.assertIn('Ramesh Kumar', res.data.decode('utf-8'))

    def test_04_camera_and_gps_complaint_submission(self):
        """Test reporting an issue with simulated live camera capture (Base64) and GPS accuracy"""
        # Log in as demo citizen
        self.client.post('/login', data={'mobile_number': '9876543210', 'password': 'CitizenPass@2026'})

        # Simulated Base64 camera photo data
        fake_base64 = "data:image/jpeg;base64," + base64.b64encode(b"simulated-camera-raw-bytes").decode('utf-8')

        report_data = {
            'category': 'Waste Management',
            'title': 'Severe Garbage Overflow at Junction',
            'description': 'Dustbin broken and rotten wet waste spilling onto pedestrian pathway.',
            'readable_address': 'Indiranagar 100ft Road, Bengaluru',
            'latitude': '12.9784',
            'longitude': '77.6408',
            'location_accuracy': '8.5',
            'camera_captured_data': fake_base64
        }

        res = self.client.post('/report', data=report_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        self.assertIn('SCC-WST-', html)
        self.assertIn('Severe Garbage Overflow at Junction', html)

        with app.app_context():
            cmp = Complaint.query.filter_by(title='Severe Garbage Overflow at Junction').first()
            self.assertIsNotNone(cmp)
            self.assertEqual(cmp.location_accuracy, 8.5)
            self.assertTrue(cmp.image_path.startswith('cam_'))
            # Check history
            self.assertEqual(cmp.history.count(), 1)
            # Check notification
            notif = Notification.query.filter_by(user_id=cmp.user_id).order_by(Notification.created_at.desc()).first()
            self.assertIn('SCC-WST-', notif.message)

    def test_05_privacy_access_control(self):
        """Ensure a citizen cannot view another citizen's private complaint"""
        # Create a second citizen user
        with app.app_context():
            user2 = User(
                name='Sneha Patel',
                mobile_number='9123456780',
                is_verified=True
            )
            user2.set_password('SnehaPass@2026')
            db.session.add(user2)
            db.session.commit()

            # Find demo citizen's complaint
            demo_cmp = Complaint.query.filter_by(tracking_id='SCC-WST-20261102-1001').first()
            target_tracking_id = demo_cmp.tracking_id

        # Log in as user2
        self.client.post('/login', data={'mobile_number': '9123456780', 'password': 'SnehaPass@2026'})

        # Try to view demo citizen's complaint
        res = self.client.get(f'/track/{target_tracking_id}', follow_redirects=True)
        html = res.data.decode('utf-8')
        self.assertIn('Privacy Protection', html)

    def test_06_authority_portal_and_workflow(self):
        """Test authority login, status updates, history audit, and citizen notification"""
        # Authority Login
        auth_data = {
            'username': 'officer_admin',
            'password': 'AuthorityPass@2026'
        }
        res_login = self.client.post('/authority/login', data=auth_data, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn('Municipal Governance', res_login.data.decode('utf-8'))

        # Fetch complaint to update
        with app.app_context():
            cmp = Complaint.query.first()
            cmp_id = cmp.complaint_id
            user_id = cmp.user_id

        # Authority updates status to In Progress
        update_data = {
            'status': 'In Progress',
            'notes': 'Ward repair vehicle dispatched with asphalt mixture.',
            'rejection_reason': ''
        }
        res_upd = self.client.post(f'/authority/complaint/update/{cmp_id}', data=update_data, follow_redirects=True)
        self.assertEqual(res_upd.status_code, 200)

        with app.app_context():
            updated_cmp = Complaint.query.get(cmp_id)
            self.assertEqual(updated_cmp.status, 'In Progress')
            
            # Check citizen received notification
            notif = Notification.query.filter_by(user_id=user_id, complaint_id=cmp_id).order_by(Notification.created_at.desc()).first()
            self.assertIn('In Progress', notif.message)

    def test_07_ai_complaint_categorization(self):
        """Test Scikit-Learn TF-IDF + Logistic Classifier"""
        res_waste = predict_complaint_category("garbage dumpster is full of rotten organic food waste")
        self.assertEqual(res_waste['category'], 'Waste Management')

        res_hosp = predict_complaint_category("emergency ICU department phone number is not answering")
        self.assertEqual(res_hosp['category'], 'Hospital Services')

        res_road = predict_complaint_category("deep pothole on main road causing severe tyre punctures")
        self.assertEqual(res_road['category'], 'Road Management')

    def test_08_core_service_pages_and_apis(self):
        """Test core service views and JSON APIs"""
        self.assertEqual(self.client.get('/waste').status_code, 200)
        self.assertEqual(self.client.get('/hospitals').status_code, 200)
        self.assertEqual(self.client.get('/roads').status_code, 200)
        self.assertEqual(self.client.get('/map').status_code, 200)

        # Facilities API
        res_fac = self.client.get('/api/facilities')
        self.assertEqual(res_fac.status_code, 200)
        fac_list = json.loads(res_fac.data)
        self.assertGreater(len(fac_list), 0)

        # Complaints Map API (generalized coordinates)
        res_cmp_map = self.client.get('/api/complaints-map')
        self.assertEqual(res_cmp_map.status_code, 200)

if __name__ == '__main__':
    unittest.main()
