# SmartCity Connect – Smart City Information and Civic Issue Management Portal

**SmartCity Connect** is a centralized, web-based municipal information and civic issue redressal portal designed for urban citizens and municipal administrators.

The portal focuses specifically on **three primary city services**:
1. 🗑️ **Waste Management**
2. 🏥 **Hospital Services**
3. 🛣️ **Road Management**

Citizens can access service schedules, locate nearby facilities on an interactive map, report civic grievances with geotags and photographs, and track complaint resolution transparently using unique tracking IDs. Administrators can manage service records, review and update complaint statuses, publish official announcements, and inspect real-time civic analytics.

---

## 🌟 Key Features

### 1. Exactly Three Core Service Modules
- **🗑️ Waste Management**:
  - Daily waste collection schedules and routes
  - Recycling centers, disposal points, and bio-digesters
  - Overflowing dustbin and uncollected garbage reporting
  - Mandatory 3-way segregation guidelines (Green: Wet, Blue: Dry, Red: Sanitary)
- **🏥 Hospital Services**:
  - Verified 24/7 emergency departments and trauma centers
  - Prominent emergency alert with direct links to call **108 (Ambulance)** and **112 (Emergency)**
  - Hospital directory searchable by specialized department (ICU, Cardiology, Pediatrics, Maternity, Blood Bank)
  - Outdated hospital info and casualty helpline grievance reporting
- **🛣️ Road Management**:
  - Live arterial road condition monitoring (Good, Moderate, Under Maintenance, Caution)
  - Damaged road and pothole reporting with photo geotagging
  - 48-Hour rapid pothole patching municipal initiative
  - Night resurfacing notices, maintenance bulletins, and traffic detours

### 2. Common Complaint Reporting System
- Unified complaint form covering all 3 categories: Waste, Hospitals, and Roads.
- Generates a **Unique Tracking ID** upon submission (e.g. `SCC-WST-20261109-1001`).
- **Interactive Location Picker**: Click directly on the Leaflet map to drop a pin or click **"Auto-Detect GPS"** to fetch browser coordinates.
- **Photo Upload**: Attach photographs of potholes, overflowing trash bins, or damaged infrastructure.

### 3. Complaint Status Redressal Workflow
```
Citizen Submits Complaint
          ↓
Complaint Saved in Database (SQLite)
          ↓
Unique Tracking ID Generated (e.g. SCC-ROD-20261109-7482)
          ↓
Admin Reviews Complaint & Verifies AI Suggestion
          ↓
Status Updated (Submitted → Under Review → Assigned → In Progress → Resolved)
          ↓
Citizen Checks Tracking ID & Views Stepper Progress & Resolution Notes
```
*Note: Rejected complaints include an administrative explanation.*

### 4. 🤖 Real-Time AI Complaint Categorization
- Built with **TF-IDF Feature Extraction** and **Logistic Classification**.
- As the citizen types their issue title or description, the portal suggests the category in real-time with an animated match percentage badge (e.g., `🗑️ Waste Management (98.5% match)`). Clicking the suggestion applies it instantly.
- In the Admin Portal, the AI-predicted category is presented alongside the citizen's choice to verify and audit routing.

### 5. 🌐 Bilingual Support (English & Kannada - ಕನ್ನಡ)
- Instant client-side language switcher in the navigation bar (`[EN | ಕನ್ನಡ]`).
- Translates navigation links, hero banner, service cards, complaint forms, and status badges dynamically with zero page reloads.

### 6. 🗺️ Interactive Maps (Leaflet + OpenStreetMap)
- Filterable map layers: Waste facilities, Hospitals, Road conditions, and Reported civic complaints.
- Custom color-coded pin markers (Green for Waste, Red for Hospitals, Amber for Roads, Purple for Complaints).

### 7. 🛡️ Admin Portal & Analytics Dashboard
- Secure login for municipal administrators and ward engineers.
- **Chart.js Analytics**:
  - Doughnut chart of complaints distributed across the 3 categories.
  - Bar chart of complaints by status pipeline.
- **Complaint Management**: Filter by category, status, or search; update status; add official resolution notes or rejection explanations.
- **Service Information Management**: Add and delete waste collection depots, hospitals, and road repair zones.
- **Announcements Management**: Publish and manage civic bulletins.

---

## 💻 Technology Stack

| Component | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), FontAwesome 6 |
| **UI Framework** | Bootstrap 5.3 |
| **Backend** | Python Flask 3.x |
| **Database** | SQLite3 |
| **Maps** | Leaflet.js + OpenStreetMap |
| **Data Visualizations** | Chart.js 4.x |
| **Machine Learning** | Scikit-learn / TF-IDF Vectorizer + Logistic Classifier |
| **Testing** | Python `unittest` |

---

## 📁 Project Folder Structure

```
smartcity-connect/
│
├── app.py                     # Main Flask application and API routes
├── models.py                  # SQLite database schema, seeding, and queries
├── config.py                  # Application configuration and settings
├── requirements.txt           # Project dependencies
├── smartcity.db               # SQLite database file
│
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Master layout with navbar, footer, and language toggle
│   ├── index.html             # Homepage with strictly the 3 main service cards
│   ├── services.html          # Three core services overview
│   ├── waste.html             # Dedicated Waste Management page
│   ├── hospitals.html         # Dedicated Hospital Services page
│   ├── roads.html             # Dedicated Road Management page
│   ├── map.html               # Interactive full-screen Leaflet city map
│   ├── report_issue.html      # Civic issue reporting form with AI assist & map picker
│   ├── track_issue.html       # Visual progress stepper tracking by ID
│   ├── announcements.html     # Municipal announcements bulletin
│   ├── admin_login.html       # Admin authentication page
│   ├── admin_dashboard.html   # Admin metrics and Chart.js analytics
│   └── manage_complaints.html # Admin grievance management and status updater
│
├── static/
│   ├── css/
│   │   └── style.css          # Custom municipal theme styling
│   ├── js/
│   │   └── script.js          # Bilingual engine (EN/KN), AI caller, image preview
│   └── images/
│
├── ml/
│   ├── train_model.py         # AI complaint classifier trainer and predictor
│   └── complaint_model.json   # Trained model weights and vocabulary
│
├── uploads/                   # Uploaded citizen issue photographs
│
└── tests/
    └── test_app.py            # Automated test suite (9 test cases)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- Pip package manager

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Train AI Model (Optional, pre-trained model included)
```bash
python ml/train_model.py
```

### 4. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔐 Administrative Access Credentials

To log in to the Admin Portal:
- **URL**: `http://127.0.0.1:5000/admin/login`
- **Username**: `admin`
- **Password**: `admin123`

---

## 🧪 Running Automated Tests

Run the test suite using Python's built-in `unittest`:
```bash
python -m unittest tests/test_app.py
```
All 9 test cases will verify database initialization, model predictions, strictly 3 service cards on the homepage, service pages, maps and JSON APIs, complaint workflow with images, admin authentication, status updates, and announcement workflows.
