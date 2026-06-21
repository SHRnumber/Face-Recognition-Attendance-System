// camera_add_student.js
const saveInfoBtn = document.getElementById("saveInfoBtn");
const startCaptureBtn = document.getElementById("startCaptureBtn");
const addStudentBtn = document.getElementById("addStudentBtn");
const video = document.getElementById("video");
const captureStatus = document.getElementById("captureStatus");
const progressBar = document.getElementById("progressBar");

let student_id = null;
let captured = 0;
const maxImages = 50;
let images = [];
let stream = null;
let isCapturing = false;

document.getElementById("studentForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  
  // Validate required fields
  const name = fd.get('name');
  if (!name || name.trim() === '') {
    alert('Student name is required');
    return;
  }
  
  try {
    const res = await fetch("/add_student", { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json();
      alert("Failed to save student info: " + (err.error || 'Unknown error'));
      return;
    }
    const j = await res.json();
    student_id = j.student_id;
    alert("✅ Student info saved. Click 'Start Capture' to capture face images.");
    startCaptureBtn.disabled = false;
    saveInfoBtn.disabled = true;
    saveInfoBtn.innerText = '✅ Saved';
  } catch (err) {
    alert("Error: " + err.message);
  }
});

startCaptureBtn.addEventListener("click", async () => {
  if (isCapturing) return;
  isCapturing = true;
  startCaptureBtn.disabled = true;
  startCaptureBtn.innerText = '📷 Capturing...';
  
  // Reset state
  captured = 0;
  images = [];
  captureStatus.innerText = `Captured 0 / ${maxImages}`;
  progressBar.style.width = '0%';
  
  try {
    stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'user'
      } 
    });
    video.srcObject = stream;
    await video.play();
    await captureImagesLoop();
  } catch (err) {
    alert("Camera access error: " + err.message);
    startCaptureBtn.disabled = false;
    startCaptureBtn.innerText = 'Start Capture (50)';
    isCapturing = false;
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
  }
});

async function captureImagesLoop() {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");

  // Take photos with variation (different angles, expressions)
  while (captured < maxImages) {
    // Small random delay for variation
    await new Promise(r => setTimeout(r, 150 + Math.random() * 150));
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise(res => canvas.toBlob(res, "image/jpeg", 0.9));
    images.push(blob);
    captured++;
    
    captureStatus.innerText = `📸 Captured ${captured} / ${maxImages}`;
    const pct = (captured / maxImages) * 100;
    progressBar.style.width = `${pct}%`;
    progressBar.innerText = `${Math.round(pct)}%`;
  }

  // Upload all images
  captureStatus.innerText = '📤 Uploading images...';
  
  try {
    const form = new FormData();
    form.append("student_id", student_id);
    images.forEach((b, i) => form.append("images[]", b, `img_${i}.jpg`));
    
    const resp = await fetch("/upload_face", { method: "POST", body: form });
    const result = await resp.json();
    
    if (resp.ok && result.saved > 0) {
      captureStatus.innerText = `✅ Uploaded ${result.saved} images successfully!`;
      addStudentBtn.disabled = false;
      addStudentBtn.className = 'btn btn-success';
    } else {
      throw new Error(result.error || 'Upload failed');
    }
  } catch (err) {
    captureStatus.innerText = `❌ Upload failed: ${err.message}`;
    alert("Failed to upload images. Please try again.");
    // Allow retry
    startCaptureBtn.disabled = false;
    startCaptureBtn.innerText = '🔄 Retry Capture';
    isCapturing = false;
    return;
  }

  // Stop camera
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  video.srcObject = null;
  
  startCaptureBtn.disabled = false;
  startCaptureBtn.innerText = '✅ Complete';
  isCapturing = false;
}

addStudentBtn.addEventListener("click", () => {
  alert("✅ Student record complete! Returning to dashboard.");
  window.location.href = "/";
});