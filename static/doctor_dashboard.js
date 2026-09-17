/* ==========================================================================
   CareSync — Doctor Dashboard
   Vanilla JS only. No fake data, no auto-called APIs.
   ========================================================================== */

const API = {
  searchPatients: "/api/doctor/patients/search",
  patientCase: "/api/doctor/patient"
};

/* ---------- element refs ---------- */
const els = {
  sidebar: document.getElementById('sidebar'),
  sidebarScrim: document.getElementById('sidebarScrim'),
  menuToggle: document.getElementById('menuToggle'),

  searchForm: document.getElementById('searchForm'),
  searchInput: document.getElementById('patientSearchInput'),

  resultsCount: document.getElementById('resultsCount'),
  patientList: document.getElementById('patientList'),
  emptyState: document.getElementById('emptyState'),
  noResultsState: document.getElementById('noResultsState'),
  loadingState: document.getElementById('loadingState'),
  patientCardTemplate: document.getElementById('patientCardTemplate'),

  casePanel: document.getElementById('casePanel'),
  casePlaceholder: document.getElementById('casePlaceholder'),
  backToPatients: document.getElementById('backToPatients'),
  patientIdentity: document.getElementById('patientIdentity'),
  historyGrid: document.getElementById('historyGrid'),
  redFlagCard: document.getElementById('redFlagCard'),
  conversationTimeline: document.getElementById('conversationTimeline'),
  toggleConversation: document.getElementById('toggleConversation'),
  verifyCaseBtn: document.getElementById('verifyCaseBtn'),
  reviewCaseBtn: document.getElementById('reviewCaseBtn'),

  logoutBtn: document.getElementById('logoutBtn'),
};

let currentPatientId = null;

/* ---------- mobile sidebar ---------- */
function openSidebar() {
  els.sidebar.classList.add('open');
  els.sidebarScrim.classList.add('show');
}
function closeSidebar() {
  els.sidebar.classList.remove('open');
  els.sidebarScrim.classList.remove('show');
}
els.menuToggle && els.menuToggle.addEventListener('click', openSidebar);
els.sidebarScrim && els.sidebarScrim.addEventListener('click', closeSidebar);

/* ---------- view state helpers ---------- */
function showLoading() {
  toggle(els.loadingState, true);
  toggle(els.emptyState, false);
  toggle(els.noResultsState, false);
  els.patientList.innerHTML = '';
}
function toggle(el, show) {
  if (!el) return;
  el.hidden = !show;
}

/* ---------- search ---------- */
els.searchForm.addEventListener('submit', function (e) {
  e.preventDefault();
  const query = els.searchInput.value.trim();
  if (!query) {
    els.searchInput.focus();
    return;
  }
  searchPatients(query);
});

async function searchPatients(query) {
  showLoading();
  els.resultsCount.textContent = 'Searching…';

  try {
    const response = await fetch(`${API.searchPatients}?q=${encodeURIComponent(query)}`);

    if (!response.ok) {
      throw new Error(`Search failed with status ${response.status}`);
    }

    const data = await response.json();
    const patients = Array.isArray(data) ? data : (data.patients || []);
    renderPatientList(patients, query);

  } catch (err) {
    // No backend connected yet, or a real network error — fail quietly with an empty state.
    console.warn('Patient search unavailable:', err.message);
    renderPatientList([], query);
  }
}

function renderPatientList(patients, query) {
  toggle(els.loadingState, false);
  els.patientList.innerHTML = '';

  if (!patients || patients.length === 0) {
    toggle(els.emptyState, false);
    toggle(els.noResultsState, true);
    els.resultsCount.textContent = `No results for "${query}"`;
    return;
  }

  toggle(els.noResultsState, false);
  els.resultsCount.textContent = `Found ${patients.length} patient${patients.length === 1 ? '' : 's'}`;

  patients.forEach(function (patient) {
    els.patientList.appendChild(buildPatientCard(patient));
  });
}

function buildPatientCard(patient) {
  const node = els.patientCardTemplate.content.firstElementChild.cloneNode(true);

  const name = patient.name || 'Unnamed patient';
  const initial = name.trim().charAt(0).toUpperCase() || 'P';
  const age = patient.age != null ? `${patient.age} yrs` : null;
  const gender = patient.gender || null;
  const demo = [age, gender].filter(Boolean).join(' · ') || 'Details not provided';

  node.querySelector('.avatar').textContent = initial;
  node.querySelector('.patient-name').textContent = name;
  node.querySelector('.patient-demo').textContent = demo;
  node.querySelector('.patient-mobile').textContent = patient.mobile || 'Mobile not provided';
  node.querySelector('.patient-abha').textContent = patient.abha_id ? `ABHA ${patient.abha_id}` : 'ABHA not linked';

  const statusPill = node.querySelector('.status-pill');
  const isRedFlag = !!patient.red_flag;
  statusPill.classList.add(isRedFlag ? 'redflag' : 'normal');
  statusPill.textContent = isRedFlag ? 'Red flag' : 'Normal';

  node.querySelector('.last-visit').textContent = patient.last_case_date
    ? `Last visit ${patient.last_case_date}`
    : 'No prior visits';

  const openCase = function () { loadPatientCase(patient.id, patient); };
  node.addEventListener('click', openCase);
  node.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openCase(); }
  });
  node.querySelector('.view-case-btn').addEventListener('click', function (e) {
    e.stopPropagation();
    openCase();
  });

  return node;
}

/* ---------- patient case ---------- */
async function loadPatientCase(patientId, knownPatient) {
  currentPatientId = patientId;

  showPatientCase({
    patient: knownPatient || { id: patientId },
    history: null,
    conversation: [],
    loading: true
  });

  try {
    const response = await fetch(`${API.patientCase}/${encodeURIComponent(patientId)}`);
    if (!response.ok) throw new Error(`Case fetch failed with status ${response.status}`);
    const data = await response.json();
    showPatientCase(data);
  } catch (err) {
    console.warn('Patient case unavailable:', err.message);
    // Keep the panel open with whatever list data we already had.
    showPatientCase({
      patient: knownPatient || { id: patientId },
      history: null,
      conversation: []
    });
  }
}

function showPatientCase(data) {
  const patient = data.patient || {};
  const history = data.history || null;
  const conversation = data.conversation || [];

  toggle(els.casePlaceholder, false);
  toggle(els.casePanel, true);
  els.casePanel.scrollIntoView({ behavior: 'smooth', block: 'start' });

  renderPatientIdentity(patient);
  renderClinicalHistory(history);
  renderRedFlag(history);
  renderConversation(conversation);
  setActiveTab('history');
}

function fieldOrPlaceholder(value) {
  return (value && String(value).trim().length > 0) ? value : null;
}

function renderPatientIdentity(patient) {
  const name = fieldOrPlaceholder(patient.name) || 'Patient name not available';
  const initial = name.trim().charAt(0).toUpperCase() || 'P';
  const age = fieldOrPlaceholder(patient.age) ? `${patient.age} years` : null;
  const gender = fieldOrPlaceholder(patient.gender);
  const mobile = fieldOrPlaceholder(patient.mobile);
  const abha = fieldOrPlaceholder(patient.abha_id);

  const metaParts = [];
  if (age) metaParts.push(`<span>${escapeHtml(age)}</span>`);
  if (gender) metaParts.push(`<span>${escapeHtml(gender)}</span>`);
  if (mobile) metaParts.push(`<span>${escapeHtml(mobile)}</span>`);
  if (abha) metaParts.push(`<span>ABHA ${escapeHtml(abha)}</span>`);

  els.patientIdentity.innerHTML = `
    <div class="pi-left">
      <div class="avatar avatar-lg">${escapeHtml(initial)}</div>
      <div>
        <div class="pi-name">${escapeHtml(name)}</div>
        <div class="pi-meta">${metaParts.join('') || '<span>Additional details not provided</span>'}</div>
      </div>
    </div>
  `;
}

const HISTORY_FIELDS = [
  { key: 'main_problem', label: 'Main problem', icon: 'problem' },
  { key: 'duration', label: 'Duration', icon: 'duration' },
  { key: 'symptoms', label: 'Symptoms', icon: 'symptoms' },
  { key: 'medical_history', label: 'Medical history', icon: 'history' },
  { key: 'medicines', label: 'Current medicines', icon: 'medicines' },
  { key: 'allergies', label: 'Allergies', icon: 'allergies' },
  { key: 'summary', label: 'AI summary', icon: 'summary', wide: true },
];

const HISTORY_ICONS = {
  problem: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.4"/><path d="M8 5.2v3.4M8 10.6h.01" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>',
  duration: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.4"/><path d="M8 4.8V8l2.4 1.4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  symptoms: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2 14 13H2L8 2Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M8 6.6v2.6M8 11h.01" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>',
  history: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="3" y="2.4" width="10" height="11.2" rx="1.2" stroke="currentColor" stroke-width="1.4"/><path d="M5.4 5.6h5.2M5.4 8h5.2M5.4 10.4h3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>',
  medicines: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2.6" y="6.4" width="10.8" height="6.2" rx="2" stroke="currentColor" stroke-width="1.4"/><path d="M8 6.4v6.2" stroke="currentColor" stroke-width="1.4"/><path d="M4.6 6.4V4.2a1.8 1.8 0 0 1 3.6 0v2.2" stroke="currentColor" stroke-width="1.4"/></svg>',
  allergies: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2.6c1.6 1.8 4 4.2 4 6.7a4 4 0 1 1-8 0c0-2.5 2.4-4.9 4-6.7Z" stroke="currentColor" stroke-width="1.4"/></svg>',
  summary: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 1.6 9.6 5.8 14 7.4 9.6 9 8 13.2 6.4 9 2 7.4 6.4 5.8 8 1.6Z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>',
};

function renderClinicalHistory(history) {
  els.historyGrid.innerHTML = '';

  HISTORY_FIELDS.forEach(function (field) {
    const value = history ? fieldOrPlaceholder(history[field.key]) : null;

    const item = document.createElement('div');
    item.className = 'history-item' + (field.wide ? ' wide' : '');
    item.innerHTML = `
      <div class="history-icon">${HISTORY_ICONS[field.icon] || ''}</div>
      <div>
        <div class="history-item-label">${escapeHtml(field.label)}</div>
        <div class="history-item-value${value ? '' : ' empty'}">${value ? escapeHtml(value) : 'Not provided'}</div>
      </div>
    `;
    els.historyGrid.appendChild(item);
  });
}

function renderRedFlag(history) {
  const hasRedFlag = !!(history && history.red_flag);

  if (hasRedFlag) {
    els.redFlagCard.className = 'redflag-card alert';
    els.redFlagCard.innerHTML = `
      <div class="redflag-head">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2.4 16 15.6H2L9 2.4Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M9 7.4v3.2M9 12.6h.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        <span class="redflag-title">Important attention</span>
      </div>
      <p class="redflag-body">Potential red flag identified from the patient's intake responses. Clinical evaluation by the doctor is required.</p>
      <span class="redflag-tag">AI-generated attention alert</span>
    `;
  } else {
    els.redFlagCard.className = 'redflag-card clear';
    els.redFlagCard.innerHTML = `
      <div class="redflag-head">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M6 9.2 8.2 11.4 12.3 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span class="redflag-title">No red flag detected</span>
      </div>
      <p class="redflag-body">No immediate AI red flag detected from the intake conversation.</p>
      <span class="redflag-tag">AI-generated attention alert</span>
    `;
  }
}

function renderConversation(conversation) {
  els.conversationTimeline.innerHTML = '';

  if (!conversation || conversation.length === 0) {
    const empty = document.createElement('li');
    empty.className = 'docs-empty';
    empty.textContent = 'No conversation recorded for this intake yet.';
    els.conversationTimeline.appendChild(empty);
    return;
  }

  conversation.forEach(function (msg) {
    const isPatient = (msg.sender || '').toLowerCase() === 'patient';
    const li = document.createElement('li');
    li.className = 'convo-item ' + (isPatient ? 'patient' : 'ai');
    li.innerHTML = `
      <div class="convo-avatar">${isPatient ? 'P' : 'AI'}</div>
      <div class="convo-bubble">
        <div class="convo-sender">${isPatient ? 'Patient' : 'CareSync AI'}</div>
        <div class="convo-text">${escapeHtml(msg.message || '')}</div>
        ${msg.created_at ? `<div class="convo-time">${escapeHtml(msg.created_at)}</div>` : ''}
      </div>
    `;
    els.conversationTimeline.appendChild(li);
  });
}

/* ---------- tabs ---------- */
document.querySelectorAll('.case-tab').forEach(function (tab) {
  tab.addEventListener('click', function () { setActiveTab(tab.dataset.tab); });
});
function setActiveTab(tabName) {
  document.querySelectorAll('.case-tab').forEach(function (t) {
    const active = t.dataset.tab === tabName;
    t.classList.toggle('active', active);
    t.setAttribute('aria-selected', active ? 'true' : 'false');
  });
  document.querySelectorAll('.case-tab-panel').forEach(function (p) {
    p.classList.toggle('active', p.dataset.panel === tabName);
  });
}

/* ---------- conversation expand toggle ---------- */
els.toggleConversation && els.toggleConversation.addEventListener('click', function () {
  const collapsed = els.conversationTimeline.classList.toggle('collapsed');
  els.toggleConversation.textContent = collapsed ? 'Expand' : 'Collapse';
});

/* ---------- back to patients ---------- */
els.backToPatients.addEventListener('click', function () {
  currentPatientId = null;
  toggle(els.casePanel, false);
  toggle(els.casePlaceholder, true);
});

/* ---------- review / verify actions ---------- */
els.reviewCaseBtn.addEventListener('click', function () {
  setActiveTab('history');
  els.casePanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

els.verifyCaseBtn.addEventListener('click', function () {
  verifyCase(currentPatientId);
});

async function verifyCase(patientId) {
  if (!patientId) return;

  const btn = els.verifyCaseBtn;
  const originalLabel = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = 'Verifying…';

  try {
    const response = await fetch(`${API.patientCase}/${encodeURIComponent(patientId)}/verify`, {
      method: 'POST'
    });

    if (!response.ok) throw new Error(`Verify failed with status ${response.status}`);

    btn.innerHTML = 'Case verified';
    setTimeout(function () { btn.innerHTML = originalLabel; btn.disabled = false; }, 2200);

  } catch (err) {
    // No backend connected yet — do not claim the case was saved.
    console.warn('Verification not saved (no backend yet):', err.message);
    btn.innerHTML = 'Verification pending backend';
    setTimeout(function () { btn.innerHTML = originalLabel; btn.disabled = false; }, 2400);
  }
}

/* ---------- logout ---------- */
function logout() {
  window.location.href = '/logout';
}

/* ---------- utilities ---------- */
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}