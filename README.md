# SmartCity Connect – Smart City Information and Civic Issue Management Portal

**SmartCity Connect** is a complete, full-stack municipal information and civic issue redressal portal designed for urban citizens and municipal authorities.

The portal focuses strictly on **three primary city services**:
1. 🗑️ **Waste Management**
2. 🏥 **Hospital Services**
3. 🛣️ **Road Management**

Citizens can access service schedules, locate nearby facilities on an interactive map, register using their mobile number and SMS OTP verification, report civic grievances with live camera captures and high-precision GPS, and track their complaints privately through their personalized citizen dashboard. Authorized officers manage complaints, update statuses with resolution notes, publish announcements, and review real-time civic analytics.

---

## 🌟 Key Features

### 1. Exactly Three Core Service Cards
- **🗑️ Waste Management**: Collection schedules, disposal points, recycling hubs, garbage overflow reporting, and segregation guidelines.
- **🏥 Hospital Services**: Verified 24/7 emergency departments, prominent emergency helplines (**108 Ambulance**, **112 Police**, **1533 Civic Control**), and department searches.
- **🛣️ Road Management**: Real-time road condition advisories, pothole reporting, maintenance bulletins, and repair status updates.

### 2. Mobile Number-Based Citizen Authentication
- **Individual Citizen Registration**: Name, 10-digit mobile number, password, and optional email.
- **Direct Citizen Account Activation**: Instant registration and automatic login without tedious OTP steps.
- **Secure Password Hashing**: Werkzeug scrypt hashing.
- **Privacy Access Control**: Citizens only have access to their own complaints. URL manipulation to access other citizens' complaints is blocked with strict access control.
- **No Admin Login on Citizen Homepage**: The citizen portal is clean; authority portal login is accessible discreetly via the footer.

### 3. Live Device Camera Integration & GPS Geolocation
- **In-Browser Camera (`getUserMedia`)**: Capture live photo evidence of civic problems directly on desktop and mobile browsers, with live preview, retake, and confirm workflows.
- **GPS Location Detection**: High-accuracy browser geolocation with GPS accuracy radius tracking (e.g. ±10m) and reverse geocoding via OpenStreetMap Nominatim.
- **Interactive Map Picker**: Fallback pinpoint selection on Leaflet interactive map.

### 4. 🤖 AI-Powered Grievance Classification
- Trained with **Scikit-Learn TF-IDF Feature Extraction + Logistic Regression**.
- Automatically predicts whether a reported issue is Waste Management, Hospital Services, or Road Management as the user types, displaying match confidence.

### 5. 🌐 Bilingual Support (English & Kannada - ಕನ್ನಡ)
- Instant client-side language switcher in the top navigation bar (`[EN | ಕನ್ನಡ]`).
- Dynamically translates UI elements, hero section, service cards, and forms without page reloads.

### 6. 🗺️ Interactive Maps & Analytics Dashboard
- **Leaflet + OpenStreetMap**: Layer filtering for Waste facilities, Hospitals, Roads, and reported issues.
- **Authority Portal**:
  - Interactive **Chart.js** visualizations (Category doughnut breakdown, Status pipeline bar chart).
  - Status pipeline: `Submitted → Under Review → Assigned → In Progress → Resolved` (or `Rejected` with mandatory explanation).
  - Audit trail in `complaint_history` and real-time citizen notifications.

---

## 🔑 Demo Credentials

### Citizen Account
- **Mobile Number**: `9876543210`
- **Password**: `CitizenPass@2026`
*(Or click "Citizen Registration" to create a new account with any 10-digit number; registration activates instantly with no OTP).*

### Authority Officer Account
- **Access Link**: Footer link `"Authority Portal Setup"` or `/authority/login`
- **Username**: `officer_admin`
- **Password**: `AuthorityPass@2026`

---

## 💻 Technology Stack

| Component | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), FontAwesome 6 |
| **UI Framework** | Bootstrap 5.3 |
| **Backend** | Python Flask 3.x, Flask-Login, Werkzeug |
| **Database** | SQLite3 with custom pure-Python ORM layer |
| **Maps** | Leaflet.js 1.9 + OpenStreetMap & Nominatim |
| **Visualizations** | Chart.js 4.x |
| **Machine Learning** | Scikit-learn (TF-IDF + Logistic Regression) |
| **Testing** | Python `unittest` (8 comprehensive test suites) |

---

## 🚀 How to Run the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Database & Seed Initial Data
The database tables and initial sample data seed automatically on first run.

### 3. Run Automated Tests
```bash
python -m unittest discover -s tests -v
```

### 4. Start the Application
```bash
python app.py
```
Open your browser and navigate to:
**`http://127.0.0.1:5000`**
