import os
import unittest
import json
import io
import sqlite3

# Import application components
from app import app
import models
from ml.train_model import predict_complaint_category

class SmartCityConnectTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key-2026'
        self.client = app.test_client()

        with app.app_context():
            models.init_db()
            models.seed_db()

    def test_01_ml_predictions(self):
        """Test AI Complaint Categorization on all 3 classes"""
        waste_res = predict_complaint_category("Garbage is not collected from street, overflowing bin")
        self.assertEqual(waste_res['category'], 'Waste Management')
        self.assertGreater(waste_res['confidence'], 50.0)

        hospital_res = predict_complaint_category("Hospital emergency telephone number is not reachable")
        self.assertEqual(hospital_res['category'], 'Hospital Services')
        self.assertGreater(hospital_res['confidence'], 50.0)

        road_res = predict_complaint_category("Road has severe deep potholes after heavy rain")
        self.assertEqual(road_res['category'], 'Road Management')
        self.assertGreater(road_res['confidence'], 50.0)

    def test_02_homepage_three_service_cards(self):
        """Test that homepage renders and strictly contains only the three core service cards"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        
        # Verify the three main service cards are present
        self.assertIn('Waste Management', content)
        self.assertIn('Hospital Services', content)
        self.assertIn('Road Management', content)

        # Verify no extraneous service cards like water, streetlights, drainage as main service cards
        self.assertNotIn('Water Supply Management', content)
        self.assertNotIn('Streetlight Management', content)
        self.assertNotIn('Drainage Management', content)

    def test_03_service_pages(self):
        """Test the 3 dedicated service pages"""
        r_waste = self.client.get('/waste')
        self.assertEqual(r_waste.status_code, 200)
        self.assertIn('Waste Collection', r_waste.data.decode('utf-8'))

        r_hosp = self.client.get('/hospitals')
        self.assertEqual(r_hosp.status_code, 200)
        self.assertIn('108', r_hosp.data.decode('utf-8'))

        r_roads = self.client.get('/roads')
        self.assertEqual(r_roads.status_code, 200)
        self.assertIn('Road Corridors', r_roads.data.decode('utf-8'))

    def test_04_map_and_apis(self):
        """Test Map view and JSON APIs for Leaflet markers"""
        r_map = self.client.get('/map')
        self.assertEqual(r_map.status_code, 200)

        r_fac = self.client.get('/api/facilities')
        self.assertEqual(r_fac.status_code, 200)
        facilities = json.loads(r_fac.data)
        self.assertIsInstance(facilities, list)
        self.assertGreater(len(facilities), 0)

        # Test predict API
        r_predict = self.client.post('/api/predict-category', json={'text': 'trash bin broken on street'})
        self.assertEqual(r_predict.status_code, 200)
        pred = json.loads(r_predict.data)
        self.assertEqual(pred['category'], 'Waste Management')

    def test_05_complaint_workflow_with_image(self):
        """Test complaint submission, image upload, unique tracking ID, and tracking"""
        complaint_data = {
            'title': 'Test Pothole on 100ft Road',
            'category': 'Road Management',
            'description': 'Large pothole causing vehicle damage near junction',
            'location_name': '100ft Road, Indiranagar',
            'citizen_name': 'Test Citizen',
            'citizen_contact': '9876543210',
            'latitude': '12.9780',
            'longitude': '77.6400',
            'image': (io.BytesIO(b"fake-image-bytes-header"), 'pothole.jpg')
        }

        response = self.client.post('/report', data=complaint_data, follow_redirects=True, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        page_content = response.data.decode('utf-8')

        # Check tracking page contains complaint details
        self.assertIn('Test Pothole on 100ft Road', page_content)
        self.assertIn('SCC-ROD-', page_content)
        self.assertIn('Submitted', page_content)

    def test_06_admin_authentication_and_dashboard(self):
        """Test Admin login and access control"""
        # Unauthorized access redirects to login
        res_unauth = self.client.get('/admin', follow_redirects=False)
        self.assertEqual(res_unauth.status_code, 302)

        # Login with correct credentials
        res_login = self.client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn('Analytics Dashboard', res_login.data.decode('utf-8'))

        # Check complaints management page
        res_complaints = self.client.get('/admin/complaints')
        self.assertEqual(res_complaints.status_code, 200)
        self.assertIn('Civic Grievance Management', res_complaints.data.decode('utf-8'))

    def test_07_admin_status_update_and_rejection(self):
        """Test Admin updating complaint status and rejecting with reason"""
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'admin'

        # Get a complaint
        conn = models.get_db_connection()
        cmp = conn.execute('SELECT id FROM complaints ORDER BY id DESC LIMIT 1').fetchone()
        conn.close()
        cmp_id = cmp['id']

        # Update to Rejected with required explanation
        res_update = self.client.post(f'/admin/complaint/update/{cmp_id}', data={
            'status': 'Rejected',
            'admin_notes': 'Verified by field inspector.',
            'rejection_reason': 'Location is inside a private residential society, not on public roadway.'
        }, follow_redirects=True)
        self.assertEqual(res_update.status_code, 200)

        # Verify DB update
        updated_cmp = models.get_complaint_by_id(cmp_id)
        self.assertEqual(updated_cmp['status'], 'Rejected')
        self.assertEqual(updated_cmp['rejection_reason'], 'Location is inside a private residential society, not on public roadway.')

    def test_08_admin_facility_management(self):
        """Test Admin adding and deleting a service facility"""
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        # Add facility
        fac_data = {
            'category': 'Waste Management',
            'name': 'Test New Biogas Depot',
            'address': 'Test Ward 99, Smart City',
            'contact_number': '080-99998888',
            'emergency_contact': '1800-425-5001',
            'operating_hours': 'Daily 6 AM - 12 PM',
            'status': 'Operational',
            'details': 'Pilot wet waste composting plant',
            'latitude': '12.9800',
            'longitude': '77.6000'
        }
        res_add = self.client.post('/admin/facility/add', data=fac_data, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)

        # Verify in DB
        facilities = models.get_facilities(category='Waste Management', search='Test New Biogas Depot')
        self.assertEqual(len(facilities), 1)
        fac_id = facilities[0]['id']

        # Delete facility
        res_del = self.client.post(f'/admin/facility/delete/{fac_id}', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        facilities_after = models.get_facilities(category='Waste Management', search='Test New Biogas Depot')
        self.assertEqual(len(facilities_after), 0)

    def test_09_announcements_workflow(self):
        """Test public viewing, admin publishing, and deleting announcements"""
        with self.client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        # Post new announcement
        ann_data = {
            'title': 'Test Monsoon Pothole Advisory',
            'category': 'Road Management',
            'priority': 'Important',
            'content': 'Special road repair teams deployed for rainy season.'
        }
        res_post = self.client.post('/admin/announcement/add', data=ann_data, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)

        # Verify on public announcements page
        res_public = self.client.get('/announcements?category=Road Management')
        self.assertIn('Test Monsoon Pothole Advisory', res_public.data.decode('utf-8'))

if __name__ == '__main__':
    unittest.main()
