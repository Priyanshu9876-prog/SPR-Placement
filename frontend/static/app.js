// frontend static JS: interacts with Flask API
// async function request(path, opts={}) {
//   const res = await fetch('/api'+path, Object.assign({
//     headers:{'Content-Type':'application/json'}
//   }, opts));
//   return res.json();
// }
const API = "https://spr-placement.onrender.com/api";

async function request(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts
  });
  return res.json();
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
async function viewStudent(id){
  const s = await request('/students/'+id);
  const offers = s.offers.map(o => `${o.company} - ${o.role} [${o.status}]`).join('\n');
  const interns = s.internships.map(i => `${i.company} - ${i.role} [${i.status}]`).join('\n');
  alert(`${s.name} (${s.roll_no})\nDept: ${s.dept}\nEmail: ${s.email}\n----\nOffers:\n${offers || 'None'}\n----\nInternships:\n${interns || 'None'}`);
}

// Delete student
async function deleteStudent(id){
  if(!confirm('Delete student and all related records?')) return;
  await fetch('/api/students/'+id, {method:'DELETE'});
  loadStudents();
  loadDashboard();
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
  await fetch('/api/students', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  f.reset();
  loadStudents();
  loadDashboard();
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
  await fetch('/api/offers', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  f.reset();
  loadDashboard();
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
  await fetch('/api/internships', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  f.reset();
  loadDashboard();
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
loadStudents();
loadDashboard();
