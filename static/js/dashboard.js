// dashboard.js
document.addEventListener("DOMContentLoaded", () => {
  const trainBtn = document.getElementById("trainBtn");
  const trainProgress = document.getElementById("trainProgress");
  const trainMsg = document.getElementById("trainMsg");
  const studentList = document.getElementById("studentList");

  // Load students
  async function loadStudents() {
    try {
      const res = await fetch("/students");
      const data = await res.json();
      if (data.students && data.students.length > 0) {
        let html = '<ul class="list-group list-group-flush">';
        data.students.forEach(s => {
          html += `<li class="list-group-item d-flex justify-content-between align-items-center">
            <div>
              <strong>${s.name}</strong>
              <span class="text-muted small"> (ID: ${s.id})</span>
              ${s.roll ? `<span class="badge bg-secondary">${s.roll}</span>` : ''}
            </div>
            <button class="btn btn-sm btn-danger delete-student" data-id="${s.id}">🗑️</button>
          </li>`;
        });
        html += '</ul>';
        studentList.innerHTML = html;
        
        // Add delete handlers
        document.querySelectorAll('.delete-student').forEach(btn => {
          btn.addEventListener('click', async function() {
            const id = this.dataset.id;
            if (confirm('Delete this student and all their data?')) {
              const res = await fetch(`/students/${id}`, { method: 'DELETE' });
              if (res.ok) {
                loadStudents();
                updateChart();
              } else {
                alert('Failed to delete student');
              }
            }
          });
        });
      } else {
        studentList.innerHTML = '<div class="text-muted small">No students registered yet</div>';
      }
    } catch (e) {
      studentList.innerHTML = '<div class="text-danger small">Error loading students</div>';
    }
  }

  async function pollStatus() {
    try {
      const res = await fetch("/train_status");
      const data = await res.json();
      trainProgress.style.width = data.progress + "%";
      trainProgress.innerText = data.progress + "%";
      trainMsg.innerText = data.message || "";
      
      // Update progress bar color based on status
      if (data.progress >= 100) {
        trainProgress.className = 'progress-bar bg-success';
      } else if (data.running) {
        trainProgress.className = 'progress-bar bg-warning progress-bar-striped progress-bar-animated';
      } else {
        trainProgress.className = 'progress-bar bg-info';
      }
      return data;
    } catch (e) {
      console.error(e);
      return null;
    }
  }

  trainBtn.addEventListener("click", async () => {
    trainBtn.disabled = true;
    trainBtn.innerText = 'Training...';
    trainMsg.innerText = 'Starting training...';
    trainProgress.className = 'progress-bar bg-warning progress-bar-striped progress-bar-animated';
    
    try {
      const start = await fetch("/train_model");
      if (!start.ok && start.status !== 202) {
        alert("Failed to start training");
        trainBtn.disabled = false;
        trainBtn.innerText = 'Train Now';
        return;
      }
      
      trainMsg.innerText = "Training in progress...";
      
      // Poll until progress==100 or not running
      const t = setInterval(async () => {
        const s = await pollStatus();
        if (s && (s.progress >= 100 || !s.running)) {
          clearInterval(t);
          trainBtn.disabled = false;
          trainBtn.innerText = 'Train Now';
          if (s.progress >= 100) {
            trainMsg.innerText = '✅ Training completed successfully!';
            trainProgress.className = 'progress-bar bg-success';
          } else {
            trainMsg.innerText = '⚠️ Training stopped';
            trainProgress.className = 'progress-bar bg-danger';
          }
        }
      }, 1500);
    } catch (e) {
      alert('Error: ' + e.message);
      trainBtn.disabled = false;
      trainBtn.innerText = 'Train Now';
    }
  });

  // Chart
  let chart = null;
  async function updateChart() {
    try {
      const res = await fetch("/attendance_stats");
      const data = await res.json();
      const ctx = document.getElementById("attendanceChart").getContext("2d");
      
      if (!chart) {
        chart = new Chart(ctx, {
          type: "bar",
          data: {
            labels: data.dates,
            datasets: [{
              label: "Attendance Count",
              data: data.counts,
              backgroundColor: "rgba(59,130,246,0.7)",
              borderColor: "rgba(59,130,246,1)",
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: { stepSize: 1 }
              }
            }
          }
        });
      } else {
        chart.data.labels = data.dates;
        chart.data.datasets[0].data = data.counts;
        chart.update();
      }
    } catch (e) {
      console.error('Chart update error:', e);
    }
  }

  // Initial load
  loadStudents();
  pollStatus();
  updateChart();
  
  // Auto-refresh every 30 seconds
  setInterval(updateChart, 30000);
  setInterval(loadStudents, 60000);
});