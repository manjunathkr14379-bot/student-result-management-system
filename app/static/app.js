/* Student Management System — frontend
   Talks to the same-origin FastAPI backend under /auth, /students,
   /courses, /enrollments. No build step, no framework — plain fetch. */

const API = ""; // same origin, so relative paths work both locally and on Render
let TOKEN = localStorage.getItem("sms_token") || null;
let ROLE = localStorage.getItem("sms_role") || null;
let EMAIL = localStorage.getItem("sms_email") || null;

let studentsPage = 1;
const PAGE_SIZE = 8;

// ---------- fetch helper ----------
async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && TOKEN) headers["Authorization"] = `Bearer ${TOKEN}`;

  const res = await fetch(API + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try { data = await res.json(); } catch (_) { /* no body */ }

  if (!res.ok) {
    const message = (data && (data.detail || JSON.stringify(data.errors))) || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

// login uses OAuth2 form-encoded body, not JSON
async function loginRequest(email, password) {
  const res = await fetch(API + "/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Login failed");
  return data;
}

// ---------- toast ----------
let toastTimer;
function toast(message, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.toggle("error", isError);
  el.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add("hidden"), 3200);
}

// ---------- session ----------
function setSession(token, role, email) {
  TOKEN = token; ROLE = role; EMAIL = email;
  localStorage.setItem("sms_token", token);
  localStorage.setItem("sms_role", role);
  localStorage.setItem("sms_email", email);
  renderSession();
}

function clearSession() {
  TOKEN = ROLE = EMAIL = null;
  localStorage.removeItem("sms_token");
  localStorage.removeItem("sms_role");
  localStorage.removeItem("sms_email");
  renderSession();
}

function renderSession() {
  const authView = document.getElementById("auth-view");
  const appView = document.getElementById("app-view");
  const sessionInfo = document.getElementById("session-info");

  if (TOKEN) {
    authView.classList.add("hidden");
    appView.classList.remove("hidden");
    sessionInfo.classList.remove("hidden");
    document.getElementById("session-email").textContent = EMAIL;
    document.getElementById("session-role").textContent = ROLE;

    // Gate admin/teacher-only controls
    document.querySelectorAll("[data-role-gate]").forEach((el) => {
      const allowed = el.dataset.roleGate.split(",");
      el.classList.toggle("hidden", !allowed.includes(ROLE));
    });

    loadStudents();
    loadCourses();
  } else {
    authView.classList.remove("hidden");
    appView.classList.add("hidden");
    sessionInfo.classList.add("hidden");
  }
}

// ---------- auth forms ----------
document.querySelectorAll(".auth-tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".auth-tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const isLogin = btn.dataset.tab === "login";
    document.getElementById("login-form").classList.toggle("hidden", !isLogin);
    document.getElementById("register-form").classList.toggle("hidden", isLogin);
  });
});

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("login-error");
  errEl.textContent = "";
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  try {
    const data = await loginRequest(email, password);
    const meRes = await fetch(API + "/auth/me", { headers: { Authorization: `Bearer ${data.access_token}` } });
    const meData = await meRes.json();
    setSession(data.access_token, meData.role, meData.email);
    toast(`Welcome back, ${meData.email}`);
  } catch (err) {
    errEl.textContent = err.message;
  }
});

document.getElementById("register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("register-error");
  errEl.textContent = "";
  const email = document.getElementById("register-email").value;
  const password = document.getElementById("register-password").value;
  const role = document.getElementById("register-role").value;
  try {
    await api("/auth/register", { method: "POST", auth: false, body: { email, password, role } });
    toast("Account created — signing you in…");
    const data = await loginRequest(email, password);
    const meRes = await fetch(API + "/auth/me", { headers: { Authorization: `Bearer ${data.access_token}` } });
    const meData = await meRes.json();
    setSession(data.access_token, meData.role, meData.email);
  } catch (err) {
    errEl.textContent = err.message;
  }
});

document.getElementById("logout-btn").addEventListener("click", () => {
  clearSession();
  toast("Signed out");
});

// ---------- app tabs ----------
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`panel-${btn.dataset.panel}`).classList.add("active");
  });
});

// ---------- students ----------
async function loadStudents() {
  const search = document.getElementById("student-search").value.trim();
  const dept = document.getElementById("student-dept-filter").value.trim();
  const params = new URLSearchParams({ page: studentsPage, page_size: PAGE_SIZE });
  if (search) params.set("search", search);
  if (dept) params.set("department", dept);

  try {
    const data = await api(`/students?${params.toString()}`);
    const tbody = document.getElementById("students-tbody");
    tbody.innerHTML = "";
    if (data.items.length === 0) {
      tbody.innerHTML = `<tr class="empty-row"><td colspan="6">No students found.</td></tr>`;
    } else {
      data.items.forEach((s) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td class="mono">${s.roll_number}</td>
          <td>${s.first_name} ${s.last_name}</td>
          <td>${s.email}</td>
          <td>${s.department}</td>
          <td>${s.year_of_study}</td>
          <td class="row-actions">
            <button class="btn-ghost" data-action="delete-student" data-id="${s.id}" data-role-gate="admin">Delete</button>
          </td>`;
        tbody.appendChild(tr);
      });
    }
    const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
    document.getElementById("students-page-info").textContent = `Page ${data.page} of ${totalPages} — ${data.total} student(s)`;
    document.getElementById("students-prev").disabled = data.page <= 1;
    document.getElementById("students-next").disabled = data.page >= totalPages;

    document.querySelectorAll("[data-action='delete-student']").forEach((btn) => {
      btn.classList.toggle("hidden", ROLE !== "admin");
      btn.addEventListener("click", () => deleteStudent(btn.dataset.id));
    });
  } catch (err) {
    toast(err.message, true);
  }
}

async function deleteStudent(id) {
  if (!confirm("Delete this student record?")) return;
  try {
    await api(`/students/${id}`, { method: "DELETE" });
    toast("Student deleted");
    loadStudents();
  } catch (err) {
    toast(err.message, true);
  }
}

document.getElementById("student-search-btn").addEventListener("click", () => { studentsPage = 1; loadStudents(); });
document.getElementById("student-search").addEventListener("keydown", (e) => { if (e.key === "Enter") { studentsPage = 1; loadStudents(); } });
document.getElementById("students-prev").addEventListener("click", () => { if (studentsPage > 1) { studentsPage--; loadStudents(); } });
document.getElementById("students-next").addEventListener("click", () => { studentsPage++; loadStudents(); });

// New student modal
const studentModal = document.getElementById("student-modal");
document.getElementById("student-new-btn").addEventListener("click", () => studentModal.classList.remove("hidden"));
document.getElementById("student-modal-cancel").addEventListener("click", () => studentModal.classList.add("hidden"));
document.getElementById("student-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("student-form-error");
  errEl.textContent = "";
  const body = {
    roll_number: document.getElementById("s-roll").value,
    first_name: document.getElementById("s-first").value,
    last_name: document.getElementById("s-last").value,
    email: document.getElementById("s-email").value,
    department: document.getElementById("s-dept").value,
    year_of_study: Number(document.getElementById("s-year").value),
  };
  try {
    await api("/students", { method: "POST", body });
    studentModal.classList.add("hidden");
    e.target.reset();
    toast("Student added");
    loadStudents();
  } catch (err) {
    errEl.textContent = err.message;
  }
});

// ---------- courses ----------
async function loadCourses() {
  try {
    const courses = await api("/courses");
    const tbody = document.getElementById("courses-tbody");
    tbody.innerHTML = "";
    if (courses.length === 0) {
      tbody.innerHTML = `<tr class="empty-row"><td colspan="5">No courses yet.</td></tr>`;
    } else {
      courses.forEach((c) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td class="mono">${c.code}</td>
          <td>${c.title}</td>
          <td>${c.credits}</td>
          <td>${c.department}</td>
          <td class="row-actions">
            <button class="btn-ghost" data-action="delete-course" data-id="${c.id}" data-role-gate="admin">Delete</button>
          </td>`;
        tbody.appendChild(tr);
      });
    }
    document.querySelectorAll("[data-action='delete-course']").forEach((btn) => {
      btn.classList.toggle("hidden", ROLE !== "admin");
      btn.addEventListener("click", () => deleteCourse(btn.dataset.id));
    });
  } catch (err) {
    toast(err.message, true);
  }
}

async function deleteCourse(id) {
  if (!confirm("Delete this course?")) return;
  try {
    await api(`/courses/${id}`, { method: "DELETE" });
    toast("Course deleted");
    loadCourses();
  } catch (err) {
    toast(err.message, true);
  }
}

const courseModal = document.getElementById("course-modal");
document.getElementById("course-new-btn").addEventListener("click", () => courseModal.classList.remove("hidden"));
document.getElementById("course-modal-cancel").addEventListener("click", () => courseModal.classList.add("hidden"));
document.getElementById("course-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("course-form-error");
  errEl.textContent = "";
  const body = {
    code: document.getElementById("c-code").value,
    title: document.getElementById("c-title").value,
    credits: Number(document.getElementById("c-credits").value),
    department: document.getElementById("c-dept").value,
  };
  try {
    await api("/courses", { method: "POST", body });
    courseModal.classList.add("hidden");
    e.target.reset();
    toast("Course added");
    loadCourses();
  } catch (err) {
    errEl.textContent = err.message;
  }
});

// ---------- enrollments ----------
document.getElementById("enroll-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("enroll-error");
  errEl.textContent = "";
  const body = {
    student_id: Number(document.getElementById("enroll-student-id").value),
    course_id: Number(document.getElementById("enroll-course-id").value),
  };
  try {
    const res = await api("/enrollments", { method: "POST", body });
    toast(`Enrolled — enrollment ID ${res.id}`);
    e.target.reset();
  } catch (err) {
    errEl.textContent = err.message;
  }
});

document.getElementById("grade-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errEl = document.getElementById("grade-error");
  errEl.textContent = "";
  const id = document.getElementById("grade-enrollment-id").value;
  const grade = Number(document.getElementById("grade-value").value);
  try {
    await api(`/enrollments/${id}/grade`, { method: "PATCH", body: { grade } });
    toast("Grade recorded");
    e.target.reset();
  } catch (err) {
    errEl.textContent = err.message;
  }
});

// ---------- transcript ----------
document.getElementById("transcript-fetch-btn").addEventListener("click", async () => {
  const id = document.getElementById("transcript-student-id").value;
  const resultEl = document.getElementById("transcript-result");
  if (!id) { toast("Enter a student ID", true); return; }
  try {
    const t = await api(`/students/${id}/transcript`);
    const rows = t.courses.map((c) => `
      <tr>
        <td class="mono">${c.course.code}</td>
        <td>${c.course.title}</td>
        <td>${c.course.credits}</td>
        <td>${c.grade ?? "—"}</td>
      </tr>`).join("");

    resultEl.innerHTML = `
      <div class="transcript-card">
        <div class="transcript-header">
          <h3>${t.first_name} ${t.last_name} <span class="mono" style="font-size:13px;color:var(--ink-soft)">(${t.roll_number})</span></h3>
          <div style="text-align:right">
            <div class="gpa-badge">${t.gpa ?? "—"}</div>
            <div class="gpa-label">GPA · ${t.total_credits} credits</div>
          </div>
        </div>
        <table class="ledger">
          <thead><tr><th>Code</th><th>Course</th><th>Credits</th><th>Grade</th></tr></thead>
          <tbody>${rows || `<tr class="empty-row"><td colspan="4">No enrollments yet.</td></tr>`}</tbody>
        </table>
      </div>`;
  } catch (err) {
    resultEl.innerHTML = "";
    toast(err.message, true);
  }
});

// ---------- init ----------
renderSession();
