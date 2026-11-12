/**
 * SmartCity Connect - Interactive City Map Module
 * Uses Leaflet & OpenStreetMap tiles
 */

document.addEventListener('DOMContentLoaded', function() {
  const mapElement = document.getElementById('full-map');
  if (!mapElement || typeof L === 'undefined') return;

  const map = L.map('full-map').setView([12.9716, 77.5946], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors | SmartCity Connect'
  }).addTo(map);

  let facilityMarkers = [];
  let complaintMarkers = [];

  function createMarkerIcon(bgColor, emoji) {
    return L.divIcon({
      html: `<div style="background:${bgColor}; color:#fff; width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 3px 8px rgba(0,0,0,0.35); font-size:17px; border:2.5px solid #fff;">${emoji}</div>`,
      className: 'custom-map-icon',
      iconSize: [36, 36],
      iconAnchor: [18, 18],
      popupAnchor: [0, -18]
    });
  }

  // Fetch Services & Facilities
  fetch('/api/facilities')
    .then(res => res.json())
    .then(services => {
      services.forEach(srv => {
        let color = '#059669';
        let emoji = '🗑️';
        if (srv.category === 'Hospital Services') {
          color = '#dc2626';
          emoji = '🏥';
        } else if (srv.category === 'Road Management') {
          color = '#d97706';
          emoji = '🛣️';
        }

        const marker = L.marker([srv.latitude, srv.longitude], {
          icon: createMarkerIcon(color, emoji)
        });
        marker.category = srv.category;

        const popupContent = `
          <div style="min-width: 220px;">
            <span class="badge ${srv.category === 'Waste Management' ? 'badge-waste' : (srv.category === 'Hospital Services' ? 'badge-hospital' : 'badge-road')} mb-1">${srv.category}</span>
            <h6 class="fw-bold mb-1">${srv.service_name}</h6>
            <p class="small text-muted mb-1"><i class="fa-solid fa-location-dot me-1"></i> ${srv.address}</p>
            <div class="small p-2 bg-light rounded mb-2">${srv.description || ''}</div>
            <div class="d-flex justify-content-between align-items-center small">
              <span class="text-success"><i class="fa-regular fa-clock me-1"></i> ${srv.operating_hours || 'N/A'}</span>
              <a href="tel:${srv.contact}" class="fw-bold text-decoration-none"><i class="fa-solid fa-phone me-1"></i> Call</a>
            </div>
          </div>
        `;
        marker.bindPopup(popupContent);
        marker.addTo(map);
        facilityMarkers.push(marker);
      });
    })
    .catch(err => console.log('Facilities load error:', err));

  // Fetch Anonymized Civic Issues for Public Awareness
  fetch('/api/complaints-map')
    .then(res => res.json())
    .then(complaints => {
      complaints.forEach(cmp => {
        const marker = L.marker([cmp.latitude, cmp.longitude], {
          icon: createMarkerIcon('#7c3aed', '⚠️')
        });
        marker.category = 'complaints';

        const popupContent = `
          <div style="min-width: 220px;">
            <span class="badge bg-purple text-white mb-1" style="background:#7c3aed;">Reported Civic Issue</span>
            <span class="badge bg-light text-dark border mb-1">${cmp.status}</span>
            <h6 class="fw-bold mb-1">${cmp.title}</h6>
            <p class="small text-muted mb-1"><i class="fa-solid fa-location-dot me-1"></i> ${cmp.readable_address}</p>
            <p class="small text-secondary mb-0">${cmp.description}</p>
          </div>
        `;
        marker.bindPopup(popupContent);
        marker.addTo(map);
        complaintMarkers.push(marker);
      });
    })
    .catch(err => console.log('Complaints map load error:', err));

  // Layer Filter Buttons
  document.querySelectorAll('.filter-pill').forEach(btn => {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      this.classList.add('active');

      const selectedLayer = this.getAttribute('data-layer');

      facilityMarkers.forEach(m => {
        if (selectedLayer === 'all' || m.category === selectedLayer) {
          map.addLayer(m);
        } else {
          map.removeLayer(m);
        }
      });

      complaintMarkers.forEach(m => {
        if (selectedLayer === 'all' || selectedLayer === 'complaints') {
          map.addLayer(m);
        } else {
          map.removeLayer(m);
        }
      });
    });
  });

  // Locate User GPS
  const locateBtn = document.getElementById('btn-locate-user');
  if (locateBtn) {
    locateBtn.addEventListener('click', function() {
      if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
      }
      navigator.geolocation.getCurrentPosition(function(pos) {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        map.setView([lat, lng], 14);
        L.marker([lat, lng], {
          icon: createMarkerIcon('#2563eb', '📍')
        }).bindPopup("<b>Your Current Location</b>").addTo(map).openPopup();
      });
    });
  }
});
