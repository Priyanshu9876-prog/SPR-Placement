// frontend static JS: interacts with Render-hosted Flask API

const API = "https://spr-placement.onrender.com/api";

async function request(path, opts = {}) {
  try {
    const res = await fetch(`${API}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...opts
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    // Some endpoints may return empty body on delete - handle that
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) return res.json();
    return null;
  } catch (err) {
    console.error("API request failed:", err);
    alert("API error: " + err.message);
    throw err;
  }
}

// Load students and populate lists
async function loadStudents(){
  const students = await request('/students');
  const list = document.getElementById('students-list');
  const offerSel = document.getElementById('offer-student');
  const internSel = document.getElementById('intern-student');
  list.innerHTML = '';
  offerSel.innerHTML = '';
  internSel.innerHTML = '';
  students.forEach(s => {
    const div = document.createElement('div');
    div.className = 'student-item';
    div.innerHTML = `<div><strong>${s.roll_no}</strong> — ${s.name} <br/><small>${s.dept || ''} ${s.year || ''}</small></div>
      <div>
        <button onclick="viewStudent(${s.id})">View</button>
        <button onclick="deleteStudent(${s.id})">Delete</button>
      </div>`;
    list.appendChild(div);

    const opt = document.createElement('option');
    opt.value = s.id; opt.text = `${s.name} (${s.roll_no})`;
    offerSel.appendChild(opt.cloneNode(true));
    internSel.appendChild(opt.cloneNode(true));
  });
}

// View student detail in alert (quick)
// --- Modal helpers ---
function showModal(title, htmlContent) {
  const modal = document.getElementById('student-modal');
  const body = document.getElementById('student-modal-body');
  const titleEl = document.getElementById('student-modal-title');
  titleEl.textContent = title || 'Details';
  body.innerHTML = htmlContent || '';
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');

  // put focus on close button for accessibility
  document.getElementById('student-modal-close').focus();
}

// close modal
function closeModal() {
  const modal = document.getElementById('student-modal');
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
}

// wire up modal close handlers (click backdrop, close button, ESC)
document.addEventListener('click', (e) => {
  const modal = document.getElementById('student-modal');
  if (!modal) return;
  if (e.target.id === 'student-modal-backdrop' || e.target.id === 'student-modal-close') closeModal();
});
document.getElementById('student-modal-ok').addEventListener('click', closeModal);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

// --- Updated viewStudent: uses modal instead of alert ---
async function viewStudent(id){
  try {
    const s = await request('/students/'+id);
    const offers = (s.offers || []).map(o => `<li>${o.company} — ${o.role} <small>[${o.status}]</small></li>`).join('') || '<li>None</li>';
    const interns = (s.internships || []).map(i => `<li>${i.company} — ${i.role} <small>[${i.status}]</small></li>`).join('') || '<li>None</li>';

    const html = `
      <div class="modal-row">
        <p><strong>${s.name} (${s.roll_no})</strong></p>
        <p class="meta">Dept: ${s.dept || '—'} &nbsp;•&nbsp; Year: ${s.year || '—'}</p>
        <p><strong>Email:</strong> ${s.email || '—'}</p>

        <hr/>

        <p><strong>Offers</strong></p>
        <ul style="margin:4px 0 10px 18px;padding:0;">${offers}</ul>

        <p><strong>Internships</strong></p>
        <ul style="margin:4px 0 0 18px;padding:0;">${interns}</ul>
      </div>
    `;

    showModal(`${s.name} — ${s.roll_no}`, html);
  } catch (err) {
    console.error('Failed to load student for modal:', err);
    alert('Could not load student details.');
  }
}


// Delete student
async function deleteStudent(id){
  if(!confirm('Delete student and all related records?')) return;
  await request(`/students/${id}`, { method: 'DELETE' });
  await loadStudents();
  await loadDashboard();
}

// Add student
document.getElementById('student-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target;
  const data = {
    roll_no: f.roll_no.value,
    name: f.name.value,
    dept: f.dept.value,
    year: f.year.value,
    email: f.email.value
  };
  await request('/students', { method: 'POST', body: JSON.stringify(data) });
  f.reset();
  await loadStudents();
  await loadDashboard();
});

// Add offer
document.getElementById('offer-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target;
  const data = {
    student_id: parseInt(document.getElementById('offer-student').value),
    company: f.company.value,
    role: f.role.value,
    ctc: f.ctc.value,
    date: f.date.value || null,
    status: f.status.value
  };
  await request('/offers', { method: 'POST', body: JSON.stringify(data) });
  f.reset();
  await loadDashboard();
});

// Add internship
document.getElementById('intern-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target;
  const data = {
    student_id: parseInt(document.getElementById('intern-student').value),
    company: f.company.value,
    role: f.role.value,
    start_date: f.start_date.value || null,
    end_date: f.end_date.value || null,
    status: f.status.value
  };
  await request('/internships', { method: 'POST', body: JSON.stringify(data) });
  f.reset();
  await loadDashboard();
});

// Dashboard
async function loadDashboard(){
  const d = await request('/dashboard/summary');
  const el = document.getElementById('dashboard');
  el.innerHTML = `
    <div>Total Students: <strong>${d.total_students}</strong></div>
    <div>Total Offers: <strong>${d.total_offers}</strong></div>
    <div>Accepted Offers: <strong>${d.accepted_offers}</strong></div>
    <div>Joined Offers: <strong>${d.joined_offers}</strong></div>
    <div>Ongoing Internships: <strong>${d.ongoing_internships}</strong></div>
  `;
}

// Init
(async function init(){
  try {
    await loadStudents();
    await loadDashboard();
  } catch (e) {
    console.error("Initialization error:", e);
  }
})();
