/**
 * SmartCity Connect - GPS & Location Management Module
 * Uses browser Geolocation API and Reverse Geocoding
 */

let reportMap = null;
let reportMarker = null;

function initLocationServices() {
  const gpsBtn = document.getElementById('btn-get-location');
  const latInput = document.getElementById('complaint-lat');
  const lngInput = document.getElementById('complaint-lng');
  const accuracyInput = document.getElementById('complaint-accuracy');
  const addressInput = document.getElementById('complaint-location');
  const accuracyBadge = document.getElementById('location-accuracy-badge');
  const mapContainer = document.getElementById('picker-map');

  // Initialize interactive Leaflet map for location selection
  if (mapContainer && typeof L !== 'undefined') {
    let initialLat = parseFloat(latInput ? latInput.value : 12.9716) || 12.9716;
    let initialLng = parseFloat(lngInput ? lngInput.value : 77.5946) || 77.5946;

    reportMap = L.map('picker-map').setView([initialLat, initialLng], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(reportMap);

    reportMarker = L.marker([initialLat, initialLng], { draggable: true }).addTo(reportMap);

    // When citizen drags pin, update coordinates and trigger reverse geocode
    reportMarker.on('dragend', function(e) {
      const pos = e.target.getLatLng();
      applyCoordinates(pos.lat, pos.lng, null);
      fetchReverseGeocode(pos.lat, pos.lng);
    });

    // When citizen clicks on map, drop pin at clicked point
    reportMap.on('click', function(e) {
      reportMarker.setLatLng(e.latlng);
      applyCoordinates(e.latlng.lat, e.latlng.lng, null);
      fetchReverseGeocode(e.latlng.lat, e.latlng.lng);
    });
  }

  // "Use My Current Location" GPS Button
  if (gpsBtn) {
    gpsBtn.addEventListener('click', function() {
      if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser. Please select the location manually on the map.');
        return;
      }

      gpsBtn.disabled = true;
      gpsBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Acquiring GPS...';

      const geoOptions = {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 0
      };

      navigator.geolocation.getCurrentPosition(
        function(pos) {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          const accuracy = pos.coords.accuracy ? Math.round(pos.coords.accuracy) : null;

          applyCoordinates(lat, lng, accuracy);

          if (reportMap && reportMarker) {
            reportMarker.setLatLng([lat, lng]);
            reportMap.setView([lat, lng], 16);
          }

          fetchReverseGeocode(lat, lng);

          gpsBtn.disabled = false;
          gpsBtn.innerHTML = '<i class="fa-solid fa-check text-success me-1"></i> GPS Locked';
        },
        function(err) {
          gpsBtn.disabled = false;
          gpsBtn.innerHTML = '<i class="fa-solid fa-location-crosshairs me-1"></i> Use My Current Location';
          
          let errMsg = 'Unable to retrieve location.';
          if (err.code === err.PERMISSION_DENIED) {
            errMsg = 'Location permission was denied. You can manually drag the pin on the map or type your address.';
          } else if (err.code === err.TIMEOUT) {
            errMsg = 'GPS request timed out. Please select your location on the map.';
          }
          alert(errMsg);
        },
        geoOptions
      );
    });
  }

  function applyCoordinates(lat, lng, accuracy) {
    if (latInput) latInput.value = lat.toFixed(6);
    if (lngInput) lngInput.value = lng.toFixed(6);
    if (accuracyInput && accuracy) accuracyInput.value = accuracy;

    if (accuracyBadge) {
      if (accuracy) {
        accuracyBadge.innerHTML = `<span class="badge bg-info-subtle text-info-emphasis border border-info-subtle"><i class="fa-solid fa-satellite-dish me-1"></i> GPS Accuracy: ±${accuracy}m</span>`;
      } else {
        accuracyBadge.innerHTML = `<span class="badge bg-light text-muted border">Coordinates: ${lat.toFixed(4)}, ${lng.toFixed(4)}</span>`;
      }
    }
  }

  // Reverse Geocode: Convert Coordinates -> Street Address
  async function fetchReverseGeocode(lat, lng) {
    if (!addressInput) return;
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`;
      const response = await fetch(url, { headers: { 'Accept': 'application/json' } });
      if (response.ok) {
        const data = await response.json();
        if (data && data.display_name) {
          addressInput.value = data.display_name;
        }
      }
    } catch (err) {
      console.log('Reverse geocoding note: using coordinate representation', err);
      if (!addressInput.value || addressInput.value.startsWith('GPS Location:')) {
        addressInput.value = `Location near (${lat.toFixed(5)}, ${lng.toFixed(5)})`;
      }
    }
  }
}

document.addEventListener('DOMContentLoaded', initLocationServices);
