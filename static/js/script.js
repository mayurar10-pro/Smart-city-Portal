/**
 * SmartCity Connect - Core JavaScript
 * Features:
 * 1. Bilingual Switcher (English <-> Kannada ಕನ್ನಡ)
 * 2. Real-time AI Complaint Categorization
 * 3. Leaflet Map Markers & Location Picker
 * 4. Image Preview
 */

// --- 1. TRANSLATION DICTIONARY (English & Kannada) ---
const TRANSLATIONS = {
  en: {
    portal_title: "SmartCity Connect",
    portal_subtitle: "Smart City Information and Civic Issue Management Portal",
    home: "Home",
    services: "Services",
    waste_mgmt: "Waste Management",
    hospital_services: "Hospital Services",
    road_mgmt: "Road Management",
    city_map: "Interactive Map",
    report_issue: "Report an Issue",
    track_complaint: "Track Complaint",
    announcements: "Announcements",
    admin_login: "Admin Portal",
    admin_dashboard: "Admin Dashboard",
    logout: "Logout",
    
    // Hero
    hero_title: "Empowering Citizens, Connecting Civic Services",
    hero_desc: "A unified smart city platform for city cleanliness, verified healthcare facilities, and smooth road infrastructure.",
    search_placeholder: "Search waste collection points, hospitals, or road conditions...",
    search_btn: "Search",
    
    // Service Cards
    services_heading: "Core City Services",
    services_subheading: "Access real-time information, locate facilities, and report issues for our three primary municipal sectors.",
    card_waste_title: "Waste Management",
    card_waste_desc: "Daily garbage collection schedules, ward recycling centers, and uncollected trash reporting.",
    card_hospital_title: "Hospital Services",
    card_hospital_desc: "Verified 24/7 emergency departments, nearby hospitals, OPD schedules, and casualty helplines.",
    card_road_title: "Road Management",
    card_road_desc: "Pothole reporting, damaged road alerts, live road repair updates, and maintenance announcements.",
    view_details: "Explore Service",
    report_this_issue: "Report Problem",

    // Features
    feat_waste_1: "Waste collection schedules & routes",
    feat_waste_2: "Segregation points & bio-compost centers",
    feat_waste_3: "Garbage overflow & cleanup reports",
    feat_hosp_1: "24/7 Verified Emergency & Trauma care",
    feat_hosp_2: "Nearby hospital locator & directions",
    feat_hosp_3: "OPD hours & blood bank availability",
    feat_road_1: "Live road surface condition alerts",
    feat_road_2: "Damaged road & pothole geotagging",
    feat_road_3: "Night maintenance & detour notices",

    // Tracking & Reporting
    complaint_form_title: "Civic Issue Reporting System",
    form_category: "Service Category",
    form_title: "Complaint Title / Summary",
    form_desc: "Issue Description (Details)",
    form_location: "Location / Landmark / Street",
    form_photo: "Attach Photograph (Optional)",
    form_submit: "Submit Complaint & Get Tracking ID",
    ai_suggested: "AI Suggested Category:",
    click_to_apply: "Click to apply",

    // Statuses
    status_submitted: "Submitted",
    status_under_review: "Under Review",
    status_assigned: "Assigned",
    status_in_progress: "In Progress",
    status_resolved: "Resolved",
    status_rejected: "Rejected",

    // Quick Stats
    stat_total_reports: "Total Reports Handled",
    stat_resolved: "Resolved Issues",
    stat_facilities: "Active Facilities",
    stat_satisfaction: "Average Resolution Rate",

    // Footer
    emergency_title: "Emergency Helplines",
    emergency_ambulance: "Ambulance: 108",
    emergency_police: "Police: 112",
    emergency_civic: "Civic Control Room: 1533",
    copyright: "SmartCity Connect. Built for Urban Governance & Citizen Empowerment."
  },
  kn: {
    portal_title: "ಸ್ಮಾರ್ಟ್‌ಸಿಟಿ ಕನೆಕ್ಟ್",
    portal_subtitle: "ಸ್ಮಾರ್ಟ್ ಸಿಟಿ ಮಾಹಿತಿ ಮತ್ತು ನಾಗರಿಕ ಸಮಸ್ಯೆ ನಿರ್ವಹಣಾ ಪೋರ್ಟಲ್",
    home: "ಮುಖಪುಟ",
    services: "ಸೇವೆಗಳು",
    waste_mgmt: "ಕಸ ನಿರ್ವಹಣೆ",
    hospital_services: "ಆಸ್ಪತ್ರೆ ಸೇವೆಗಳು",
    road_mgmt: "ರಸ್ತೆ ನಿರ್ವಹಣೆ",
    city_map: "ನಗರದ ನಕ್ಷೆ",
    report_issue: "ಸಮಸ್ಯೆ ವರದಿ ಮಾಡಿ",
    track_complaint: "ದೂರು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ",
    announcements: "ಪ್ರಕಟಣೆಗಳು",
    admin_login: "ಅಡ್ಮಿನ್ ಲಾಗಿನ್",
    admin_dashboard: "ಅಡ್ಮಿನ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
    logout: "ನಿರ್ಗಮಿಸಿ",

    // Hero
    hero_title: "ನಾಗರಿಕರ ಸಬಲೀಕರಣ, ಪೌರ ಸೇವೆಗಳ ಸಮನ್ವಯ",
    hero_desc: "ನಗರದ ನೈರ್ಮಲ್ಯ, ಪರಿಶೀಲಿಸಿದ ಆರೋಗ್ಯ ಸೇವೆಗಳು ಮತ್ತು ಸುಗಮ ರಸ್ತೆ ಮೂಲಸೌಕರ್ಯಕ್ಕಾಗಿ ಏಕೀಕೃತ ಪೋರ್ಟಲ್.",
    search_placeholder: "ಕಸ ವಿಲೇವಾರಿ, ಆಸ್ಪತ್ರೆಗಳು ಅಥವಾ ರಸ್ತೆ ಸ್ಥಿತಿಯನ್ನು ಹುಡುಕಿ...",
    search_btn: "ಹುಡುಕಿ",

    // Service Cards
    services_heading: "ಪ್ರಮುಖ ನಗರ ಸೇವೆಗಳು",
    services_subheading: "ನಮ್ಮ ಮೂರು ಮುಖ್ಯ ಕ್ಷೇತ್ರಗಳ ಮಾಹಿತಿ ಪಡೆಯಿರಿ, ಸೌಲಭ್ಯಗಳನ್ನು ಗುರುತಿಸಿ ಮತ್ತು ಸಮಸ್ಯೆಗಳನ್ನು ವರದಿ ಮಾಡಿ.",
    card_waste_title: "ಕಸ ನಿರ್ವಹಣೆ",
    card_waste_desc: "ದೈನಂದಿನ ಕಸ ಸಂಗ್ರಹಣೆ ವೇಳಾಪಟ್ಟಿ, ಮರುಬಳಕೆ ಕೇಂದ್ರಗಳು ಮತ್ತು ಸಂಗ್ರಹವಾಗದ ಕಸದ ದೂರು ಸಲ್ಲಿಕೆ.",
    card_hospital_title: "ಆಸ್ಪತ್ರೆ ಸೇವೆಗಳು",
    card_hospital_desc: "ಪರಿಶೀಲಿಸಿದ 24/7 ತುರ್ತು ಚಿಕಿತ್ಸೆ, ಸಮೀಪದ ಆಸ್ಪತ್ರೆಗಳು, ತಜ್ಞ ವೈದ್ಯರ ಲಭ್ಯತೆ ಮತ್ತು ಸಹಾಯವಾಣಿಗಳು.",
    card_road_title: "ರಸ್ತೆ ನಿರ್ವಹಣೆ",
    card_road_desc: "ಗುಂಡಿ ಬಿದ್ದ ರಸ್ತೆಗಳ ವರದಿ, ಹಾಳಾದ ರಸ್ತೆ ಎಚ್ಚರಿಕೆಗಳು, ದುರಸ್ತಿ ಮಾಹಿತಿ ಮತ್ತು ಪ್ರಕಟಣೆಗಳು.",
    view_details: "ಮಾಹಿತಿ ನೋಡಿ",
    report_this_issue: "ದೂರು ಸಲ್ಲಿಸಿ",

    // Features
    feat_waste_1: "ಕಸ ಸಂಗ್ರಹಣಾ ವೇಳಾಪಟ್ಟಿ ಮತ್ತು ಮಾರ್ಗಗಳು",
    feat_waste_2: "ಕಸ ವಿಂಗಡಣಾ ಕೇಂದ್ರಗಳು ಮತ್ತು ಗೊಬ್ಬರ ಘಟಕಗಳು",
    feat_waste_3: "ಕಸ ತುಂಬಿ ತುಳುಕುವ ದೂರುಗಳ ಪರಿಹಾರ",
    feat_hosp_1: "24/7 ಪರಿಶೀಲಿಸಿದ ತುರ್ತು ಮತ್ತು ಅಪಘಾತ ಚಿಕಿತ್ಸೆ",
    feat_hosp_2: "ಸಮೀಪದ ಆಸ್ಪತ್ರೆಗಳ ನಕ್ಷೆ ಮತ್ತು ಮಾರ್ಗದರ್ಶನ",
    feat_hosp_3: "ಹೊರರೋಗಿ ಸಮಯ ಮತ್ತು ರಕ್ತನಿಧಿ ವಿವರಗಳು",
    feat_road_1: "ರಸ್ತೆ ಸ್ಥಿತಿಗತಿ ಲೈವ್ ಎಚ್ಚರಿಕೆಗಳು",
    feat_road_2: "ಗುಂಡಿ ಬಿದ್ದ ರಸ್ತೆಗಳ ಫೋಟೋ ಸಹಿತ ವರದಿ",
    feat_road_3: "ರಾತ್ರಿ ದುರಸ್ತಿ ಮತ್ತು ಬದಲಿ ಮಾರ್ಗ ಮಾಹಿತಿ",

    // Tracking & Reporting
    complaint_form_title: "ಸಾರ್ವಜನಿಕ ಸಮಸ್ಯೆ ದೂರು ನಮೂನೆ",
    form_category: "ಸೇವಾ ವರ್ಗ",
    form_title: "ದೂರಿನ ಶೀರ್ಷಿಕೆ / ಸಾರಾಂಶ",
    form_desc: "ಸಮಸ್ಯೆಯ ವಿವರಣೆ",
    form_location: "ಸ್ಥಳ / ರಸ್ತೆ / ಪ್ರಮುಖ ಗುರುತು",
    form_photo: "ಫೋಟೋ ಲಗತ್ತಿಸಿ (ಐಚ್ಛಿಕ)",
    form_submit: "ದೂರು ಸಲ್ಲಿಸಿ ಮತ್ತು ಟ್ರ್ಯಾಕಿಂಗ್ ಐಡಿ ಪಡೆಯಿರಿ",
    ai_suggested: "AI ಶಿಫಾರಸು ಮಾಡಿದ ವರ್ಗ:",
    click_to_apply: "ಆಯ್ಕೆ ಮಾಡಲು ಕ್ಲಿಕ್ ಮಾಡಿ",

    // Statuses
    status_submitted: "ಸಲ್ಲಿಸಲಾಗಿದೆ",
    status_under_review: "ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ",
    status_assigned: "ನಿಯೋಜಿಸಲಾಗಿದೆ",
    status_in_progress: "ಪ್ರಗತಿಯಲ್ಲಿದೆ",
    status_resolved: "ಪರಿಹರಿಸಲಾಗಿದೆ",
    status_rejected: "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ",

    // Quick Stats
    stat_total_reports: "ಸ್ವೀಕರಿಸಲಾದ ಒಟ್ಟು ದೂರುಗಳು",
    stat_resolved: "ಪರಿಹರಿಸಲಾದ ಸಮಸ್ಯೆಗಳು",
    stat_facilities: "ಸಕ್ರಿಯ ನಾಗರಿಕ ಸೌಲಭ್ಯಗಳು",
    stat_satisfaction: "ದೂರು ಪರಿಹಾರ ದರ",

    // Footer
    emergency_title: "ತುರ್ತು ಸಹಾಯವಾಣಿಗಳು",
    emergency_ambulance: "ಆಂಬ್ಯುಲೆನ್ಸ್: 108",
    emergency_police: "ಪೊಲೀಸ್: 112",
    emergency_civic: "ಪಾಲಿಕೆ ನಿಯಂತ್ರಣ ಕೊಠಡಿ: 1533",
    copyright: "ಸ್ಮಾರ್ಟ್‌ಸಿಟಿ ಕನೆಕ್ಟ್. ನಗರ ಆಡಳಿತ ಮತ್ತು ನಾಗರಿಕರ ಸಬಲೀಕರಣಕ್ಕಾಗಿ ನಿರ್ಮಿಸಲಾಗಿದೆ."
  }
};

// Current active language
let currentLang = localStorage.getItem('scc_language') || 'en';

function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('scc_language', lang);
  
  const dict = TRANSLATIONS[lang] || TRANSLATIONS.en;
  
  // Translate all elements with data-i18n attribute
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.setAttribute('placeholder', dict[key]);
      } else {
        el.textContent = dict[key];
      }
    }
  });

  // Update language toggle button label
  const toggleBtn = document.getElementById('lang-toggle-btn');
  if (toggleBtn) {
    toggleBtn.innerHTML = lang === 'en' 
      ? '<i class="fa-solid fa-language me-1"></i> ಕನ್ನಡ' 
      : '<i class="fa-solid fa-language me-1"></i> English';
  }
}

function toggleLanguage() {
  const nextLang = currentLang === 'en' ? 'kn' : 'en';
  applyLanguage(nextLang);
}

// --- 2. REAL-TIME AI COMPLAINT CATEGORIZATION ---
let typingTimer;
function setupAICategorization() {
  const descInput = document.getElementById('complaint-description');
  const titleInput = document.getElementById('complaint-title');
  const aiBadge = document.getElementById('ai-category-badge');
  const aiContainer = document.getElementById('ai-recommendation-box');
  const categorySelect = document.getElementById('complaint-category');

  if (!descInput || !aiBadge) return;

  function checkPrediction() {
    clearTimeout(typingTimer);
    const combinedText = ((titleInput ? titleInput.value : '') + ' ' + descInput.value).trim();

    if (combinedText.length < 8) {
      if (aiContainer) aiContainer.style.display = 'none';
      return;
    }

    typingTimer = setTimeout(() => {
      fetch('/api/predict-category', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: combinedText })
      })
      .then(res => res.json())
      .then(data => {
        if (data && data.category) {
          if (aiContainer) aiContainer.style.display = 'flex';
          const icon = data.category === 'Waste Management' ? '🗑️' : (data.category === 'Hospital Services' ? '🏥' : '🛣️');
          aiBadge.innerHTML = `<strong>${icon} ${data.category}</strong> <span class="badge bg-primary ms-1">${data.confidence}% match</span>`;
          
          // Clicking the suggestion applies it to the select box
          if (categorySelect) {
            aiContainer.onclick = function() {
              categorySelect.value = data.category;
              aiBadge.classList.add('animate__animated', 'animate__pulse');
            };
          }
        }
      })
      .catch(err => console.log('AI prediction call error:', err));
    }, 400); // 400ms debounce
  }

  descInput.addEventListener('input', checkPrediction);
  if (titleInput) titleInput.addEventListener('input', checkPrediction);
}

// --- 3. PHOTO PREVIEW ---
function setupImagePreview() {
  const imageInput = document.getElementById('complaint-image');
  const previewBox = document.getElementById('image-preview-container');
  const previewImg = document.getElementById('image-preview');

  if (imageInput && previewBox && previewImg) {
    imageInput.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(evt) {
          previewImg.src = evt.target.result;
          previewBox.style.display = 'block';
        };
        reader.readAsDataURL(file);
      } else {
        previewBox.style.display = 'none';
      }
    });
  }
}

// --- 4. GEOLOCATION GPS BUTTON ---
function setupGPSLocator() {
  const gpsBtn = document.getElementById('btn-get-location');
  const locInput = document.getElementById('complaint-location');
  const latInput = document.getElementById('complaint-lat');
  const lngInput = document.getElementById('complaint-lng');

  if (gpsBtn && locInput) {
    gpsBtn.addEventListener('click', function() {
      if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
      }
      gpsBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Locating...';
      gpsBtn.disabled = true;

      navigator.geolocation.getCurrentPosition(
        function(pos) {
          const lat = pos.coords.latitude.toFixed(6);
          const lng = pos.coords.longitude.toFixed(6);
          if (latInput) latInput.value = lat;
          if (lngInput) lngInput.value = lng;
          locInput.value = `GPS Location: Lat ${lat}, Lng ${lng} (Bengaluru)`;
          gpsBtn.innerHTML = '<i class="fa-solid fa-check text-success me-1"></i> Located';
          gpsBtn.disabled = false;
        },
        function(err) {
          gpsBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs me-1"></i> Auto-Detect';
          gpsBtn.disabled = false;
          alert('Could not fetch exact GPS location: ' + err.message);
        },
        { timeout: 8000 }
      );
    });
  }
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', function() {
  applyLanguage(currentLang);
  setupAICategorization();
  setupImagePreview();
  setupGPSLocator();
});
