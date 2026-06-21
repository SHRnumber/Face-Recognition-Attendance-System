// camera_mark.js
const startMarkBtn = document.getElementById("startMarkBtn");
const stopMarkBtn = document.getElementById("stopMarkBtn");
const markVideo = document.getElementById("markVideo");
const markStatus = document.getElementById("markStatus");
const recognizedList = document.getElementById("recognizedList");

let markStream = null;
let markInterval = null;
let recognizedData = new Map(); // Store student data with count
let isMarking = false;

startMarkBtn.addEventListener("click", async () => {
  if (isMarking) return;
  isMarking = true;
  startMarkBtn.disabled = true;
  startMarkBtn.innerText = '📷 Starting...';
  stopMarkBtn.disabled = false;
  recognizedData.clear();
  recognizedList.innerHTML = '';
  
  try {
    markStream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'user'
      } 
    });
    markVideo.srcObject = markStream;
    await markVideo.play();
    markStatus.innerText = "🔍 Scanning for faces...";
    markStatus.className = 'mt-2 text-info';
    startMarkBtn.innerText = '✅ Running';
    
    if (markInterval) clearInterval(markInterval);
    markInterval = setInterval(captureAndRecognize, 800); // Faster recognition
  } catch (err) {
    alert("Camera error: " + err.message);
    startMarkBtn.disabled = false;
    startMarkBtn.innerText = 'Start';
    stopMarkBtn.disabled = true;
    isMarking = false;
  }
});

stopMarkBtn.addEventListener("click", () => {
  stopAttendance();
});

function stopAttendance() {
  isMarking = false;
  if (markInterval) {
    clearInterval(markInterval);
    markInterval = null;
  }
  if (markStream) {
    markStream.getTracks().forEach(t => t.stop());
    markStream = null;
  }
  markVideo.srcObject = null;
  startMarkBtn.disabled = false;
  startMarkBtn.innerText = 'Start';
  stopMarkBtn.disabled = true;
  markStatus.innerText = `⏹️ Stopped - Total: ${recognizedData.size} students recognized`;
  markStatus.className = 'mt-2 text-muted';
}

async function captureAndRecognize() {
  if (!markVideo.videoWidth || !markVideo.videoHeight) return;
  
  try {
    const canvas = document.createElement("canvas");
    canvas.width = markVideo.videoWidth || 640;
    canvas.height = markVideo.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(markVideo, 0, 0, canvas.width, canvas.height);
    
    const blob = await new Promise(r => canvas.toBlob(r, "image/jpeg", 0.85));
    const fd = new FormData();
    fd.append("image", blob, "snap.jpg");
    
    const res = await fetch("/recognize_face", { method: "POST", body: fd });
    const j = await res.json();
    
    if (j.recognized) {
      const confPct = Math.round(j.confidence * 100);
      
      // Update or add student in the map
      if (!recognizedData.has(j.student_id)) {
        recognizedData.set(j.student_id, {
          name: j.name,
          count: 1,
          lastTime: new Date().toLocaleTimeString(),
          confidence: confPct
        });
      } else {
        const data = recognizedData.get(j.student_id);
        data.count += 1;
        data.lastTime = new Date().toLocaleTimeString();
        data.confidence = confPct;
        recognizedData.set(j.student_id, data);
      }
      
      // Update UI
      updateRecognizedList();
      
      const data = recognizedData.get(j.student_id);
      markStatus.innerText = `✅ ${j.name} marked (${data.count}x today) - ${confPct}%`;
      markStatus.className = 'mt-2 text-success';
      
    } else {
      if (j.error) {
        markStatus.innerText = `⚠️ ${j.error}`;
        markStatus.className = 'mt-2 text-warning';
      } else {
        markStatus.innerText = "❌ No face recognized";
        markStatus.className = 'mt-2 text-danger';
      }
    }
  } catch (err) {
    console.error('Recognition error:', err);
    markStatus.innerText = "⚠️ Recognition error";
    markStatus.className = 'mt-2 text-danger';
  }
}

function updateRecognizedList() {
  recognizedList.innerHTML = '';
  
  // Sort by count (highest first)
  const sorted = Array.from(recognizedData.entries())
    .sort((a, b) => b[1].count - a[1].count);
  
  sorted.forEach(([id, data]) => {
    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";
    li.innerHTML = `
      <div>
        <strong>${data.name}</strong>
        <span class="badge bg-primary ms-2">${data.count}x</span>
        <span class="badge bg-success ms-1">${data.confidence}%</span>
      </div>
      <small class="text-muted">Last: ${data.lastTime}</small>
    `;
    recognizedList.appendChild(li);
  });
  
  // Limit to 20 items
  while (recognizedList.children.length > 20) {
    recognizedList.removeChild(recognizedList.lastChild);
  }
}

// Clean up when leaving page
window.addEventListener('beforeunload', () => {
  if (markInterval) clearInterval(markInterval);
  if (markStream) markStream.getTracks().forEach(t => t.stop());
});