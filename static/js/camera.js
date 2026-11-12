/**
 * SmartCity Connect - Camera Access & Verification Module
 * Uses browser MediaDevices API (getUserMedia)
 * Supports Mobile & Desktop cameras with environment/user fallback.
 */

let videoStream = null;
let capturedBlob = null;

function initCameraModal() {
  const openCameraBtn = document.getElementById('btn-open-camera');
  const cameraModalElem = document.getElementById('cameraModal');
  const videoElem = document.getElementById('camera-video');
  const canvasElem = document.getElementById('camera-canvas');
  const captureBtn = document.getElementById('btn-capture-photo');
  const retakeBtn = document.getElementById('btn-retake-photo');
  const confirmBtn = document.getElementById('btn-confirm-photo');
  const cameraErrorAlert = document.getElementById('camera-error');
  const previewContainer = document.getElementById('image-preview-container');
  const previewImg = document.getElementById('image-preview');
  const manualFileInput = document.getElementById('complaint-image');
  const cameraCapturedField = document.getElementById('camera-captured-data');

  if (!openCameraBtn || !cameraModalElem) return;

  const bsModal = new bootstrap.Modal(cameraModalElem);

  // 1. Open Camera and Request Permission
  openCameraBtn.addEventListener('click', async function() {
    cameraErrorAlert.style.display = 'none';
    videoElem.style.display = 'block';
    canvasElem.style.display = 'none';
    captureBtn.style.display = 'inline-block';
    retakeBtn.style.display = 'none';
    confirmBtn.style.display = 'none';

    bsModal.show();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showCameraError('Your browser does not support live camera access. Please use the manual file upload option below.');
      return;
    }

    try {
      // Prefer rear environment camera on mobile phones
      const constraints = {
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };
      videoStream = await navigator.mediaDevices.getUserMedia(constraints);
      videoElem.srcObject = videoStream;
      videoElem.play();
    } catch (err) {
      console.warn('Rear camera unavailable, attempting default camera:', err);
      try {
        videoStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        videoElem.srcObject = videoStream;
        videoElem.play();
      } catch (finalErr) {
        showCameraError('Camera permission denied or camera not found. You can still manually upload a photograph below.');
      }
    }
  });

  // 2. Capture Photograph onto Canvas
  captureBtn.addEventListener('click', function() {
    if (!videoStream) return;

    const width = videoElem.videoWidth || 640;
    const height = videoElem.videoHeight || 480;

    canvasElem.width = width;
    canvasElem.height = height;

    const ctx = canvasElem.getContext('2d');
    ctx.drawImage(videoElem, 0, 0, width, height);

    // Stop video stream display and show canvas
    videoElem.style.display = 'none';
    canvasElem.style.display = 'block';

    captureBtn.style.display = 'none';
    retakeBtn.style.display = 'inline-block';
    confirmBtn.style.display = 'inline-block';
  });

  // 3. Retake Photograph
  retakeBtn.addEventListener('click', function() {
    videoElem.style.display = 'block';
    canvasElem.style.display = 'none';
    captureBtn.style.display = 'inline-block';
    retakeBtn.style.display = 'none';
    confirmBtn.style.display = 'none';
  });

  // 4. Confirm Photograph & Associate with Form
  confirmBtn.addEventListener('click', function() {
    const dataUrl = canvasElem.toDataURL('image/jpeg', 0.88);
    
    // Store in hidden input for backend consumption
    if (cameraCapturedField) {
      cameraCapturedField.value = dataUrl;
    }

    // Show preview
    if (previewContainer && previewImg) {
      previewImg.src = dataUrl;
      previewContainer.style.display = 'block';
    }

    // Show verification badge
    const badge = document.getElementById('photo-evidence-badge');
    if (badge) {
      badge.innerHTML = '<span class="badge bg-success"><i class="fa-solid fa-camera me-1"></i> Live Camera Photograph Captured</span>';
    }

    stopCameraStream();
    bsModal.hide();
  });

  // When modal closes, always shut off hardware camera light
  cameraModalElem.addEventListener('hidden.bs.modal', function() {
    stopCameraStream();
  });

  function stopCameraStream() {
    if (videoStream) {
      videoStream.getTracks().forEach(track => track.stop());
      videoStream = null;
    }
  }

  function showCameraError(msg) {
    cameraErrorAlert.textContent = msg;
    cameraErrorAlert.style.display = 'block';
    videoElem.style.display = 'none';
    captureBtn.style.display = 'none';
  }
}

document.addEventListener('DOMContentLoaded', initCameraModal);
