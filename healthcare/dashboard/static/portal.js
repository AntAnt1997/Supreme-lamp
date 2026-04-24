/* Shared JavaScript utilities for the Healthcare Patient Portal */

// ── Auth helpers ───────────────────────────────────────────────────────────────

function getToken() {
  return localStorage.getItem('hc_token');
}

function setToken(token, role, userId) {
  localStorage.setItem('hc_token', token);
  localStorage.setItem('hc_role', role);
  localStorage.setItem('hc_user_id', userId);
  updateNavAuth();
}

function clearToken() {
  localStorage.removeItem('hc_token');
  localStorage.removeItem('hc_role');
  localStorage.removeItem('hc_user_id');
  localStorage.removeItem('hc_chat_session');
  updateNavAuth();
}

function updateNavAuth() {
  const nav = document.getElementById('navAuth');
  if (!nav) return;
  const token = getToken();
  if (token) {
    nav.innerHTML = `
      <span style="color:#64748b;font-size:.9rem">Signed in</span>
      <button onclick="signOut()" class="btn btn-outline btn-sm">Sign Out</button>
    `;
  } else {
    nav.innerHTML = `
      <button onclick="showLoginModal()" class="btn btn-outline">Sign In</button>
      <button onclick="showRegisterModal()" class="btn btn-primary">Register</button>
    `;
  }
}

function signOut() {
  clearToken();
  window.location.href = '/';
}

// ── Modal helpers ──────────────────────────────────────────────────────────────

function showModal(id) {
  document.getElementById(id).classList.remove('hidden');
}

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
}

function showLoginModal() {
  if (document.getElementById('loginModal')) {
    closeModal('registerModal');
    showModal('loginModal');
  } else {
    window.location.href = '/?signin=1';
  }
}

function showRegisterModal() {
  if (document.getElementById('registerModal')) {
    closeModal('loginModal');
    showModal('registerModal');
  } else {
    window.location.href = '/?register=1';
  }
}

// ── Auth handlers ──────────────────────────────────────────────────────────────

async function handleLogin(event) {
  event.preventDefault();
  const email = document.getElementById('loginEmail').value;
  const password = document.getElementById('loginPassword').value;

  const formData = new FormData();
  formData.append('username', email);
  formData.append('password', password);

  try {
    const r = await fetch('/api/auth/token', { method: 'POST', body: formData });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Login failed');

    if (data.role === 'mfa_required') {
      // Show MFA section
      setToken(data.access_token, 'mfa_pending', data.user_id);
      document.getElementById('mfaSection').classList.remove('hidden');
      document.getElementById('loginForm').classList.add('hidden');
      return;
    }

    setToken(data.access_token, data.role, data.user_id);
    closeModal('loginModal');
    window.location.reload();
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

async function submitMFA() {
  const code = document.getElementById('mfaCode').value;
  const token = getToken();
  try {
    const r = await fetch('/api/auth/mfa/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ code }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Invalid code');
    setToken(data.access_token, data.role, data.user_id);
    closeModal('loginModal');
    window.location.reload();
  } catch (e) {
    alert('MFA Error: ' + e.message);
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const body = {
    email: document.getElementById('regEmail').value,
    password: document.getElementById('regPassword').value,
    first_name: document.getElementById('regFirst').value,
    last_name: document.getElementById('regLast').value,
    date_of_birth: document.getElementById('regDob').value,
    phone: document.getElementById('regPhone').value || null,
  };
  try {
    const r = await fetch('/api/auth/register/patient', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Registration failed');
    setToken(data.access_token, data.role, data.user_id);
    closeModal('registerModal');
    window.location.reload();
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

// ── Initialise on load ─────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  updateNavAuth();

  // Auto-open modal from URL param
  const params = new URLSearchParams(window.location.search);
  if (params.get('signin')) showLoginModal();
  if (params.get('register')) showRegisterModal();
});
