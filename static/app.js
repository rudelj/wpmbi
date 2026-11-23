// ETSI WPM Unified Suite - Client Application
// Integrates WPM.exe Secretariat Back-Office & WPM Web Public Portal
// Design System: ETSI Directory Services 2.0

let currentItems = [];
let selectedWkiId = null;
let activeTab = "catalog";
let onlyFavoritesFilter = false;
const API_BASE = window.location.pathname.replace(/\/(index\.html)?$/, '').replace(/\/+$/, '');

// Progress Bar Helper
function startProgress() {
  const bar = document.getElementById("top-progress-bar");
  if (bar) {
    bar.style.opacity = "1";
    bar.style.width = "40%";
  }
}

function finishProgress() {
  const bar = document.getElementById("top-progress-bar");
  if (bar) {
    bar.style.width = "100%";
    setTimeout(() => {
      bar.style.opacity = "0";
      bar.style.width = "0%";
    }, 250);
  }
}

// Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  let iconName = "info";
  if (type === "success") iconName = "check-circle";
  if (type === "error") iconName = "alert-circle";
  if (type === "warning") iconName = "alert-triangle";

  toast.innerHTML = `
    <i data-lucide="${iconName}" style="width:18px; height:18px;"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  lucide.createIcons();

  setTimeout(() => {
    toast.style.animation = "toastOut 0.3s forwards";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Navigation Tabs
function switchTab(tabId) {
  activeTab = tabId;
  const tabs = ["catalog", "admin", "numbering", "clone", "schedule", "freq"];

  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const view = document.getElementById(`view-${t}`);
    if (btn) btn.classList.toggle("active", t === tabId);
    if (view) view.style.display = (t === tabId) ? "block" : "none";
  });

  if (tabId === "numbering") {
    runNumberGenerator();
  } else if (tabId === "clone") {
    populateCloneDropdown();
  } else if (tabId === "schedule") {
    const today = new Date().toISOString().split("T")[0];
    const dateInput = document.getElementById("plan-start-date");
    if (dateInput && !dateInput.value) {
      dateInput.value = today;
    }
  } else if (tabId === "freq") {
    loadFrequenciesAndMandates();
  } else if (tabId === "admin") {
    renderAdminTable(currentItems);
  }

  lucide.createIcons();
}

// Fetch KPI Metrics
async function fetchKPIs() {
  try {
    const res = await fetch(`${API_BASE}/api/kpis`);
    if (!res.ok) return;
    const data = await res.json();

    const totalEl = document.getElementById("kpi-total-items");
    const tbsEl = document.getElementById("kpi-tbs");
    const pubEl = document.getElementById("kpi-published");
    const appEl = document.getElementById("kpi-approval");
    const stopEl = document.getElementById("kpi-stopped");

    if (totalEl) totalEl.textContent = data.total_active_items ?? "-";
    if (tbsEl) tbsEl.textContent = data.total_technical_bodies ?? "10";
    if (pubEl) pubEl.textContent = data.published_count ?? "-";
    if (appEl) appEl.textContent = data.approval_count ?? "-";
    if (stopEl) stopEl.textContent = data.stopped_count ?? "-";
  } catch (err) {
    console.error("Failed to load KPIs:", err);
  }
}

// Search & Catalog
async function executeSearch(resetOffset = true) {
  startProgress();
  try {
    const q = document.getElementById("filter-q")?.value || "";
    const docType = document.getElementById("filter-type")?.value || "";
    const tb = document.getElementById("filter-tb")?.value || "";
    const status = document.getElementById("filter-status")?.value || "";
    const includeStopped = document.getElementById("check-include-stopped")?.checked || false;

    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (docType) params.set("doc_type", docType);
    if (tb) params.set("tb", tb);
    if (status) params.set("status", status);
    if (includeStopped) params.set("include_stopped", "true");
    if (onlyFavoritesFilter) params.set("only_favorites", "true");
    params.set("limit", "100");

    const res = await fetch(`${API_BASE}/api/work-items?${params.toString()}`);
    if (!res.ok) throw new Error("Search query failed.");

    const data = await res.json();
    currentItems = data.items || [];

    const summaryEl = document.getElementById("table-summary-count");
    if (summaryEl) {
      summaryEl.textContent = `${data.total} deliverables found`;
    }

    renderTable(currentItems);
    renderAdminTable(currentItems);
  } catch (err) {
    console.error(err);
    showToast(err.message, "error");
  } finally {
    finishProgress();
  }
}

function resetSearchFilters() {
  document.getElementById("filter-q").value = "";
  document.getElementById("filter-type").value = "";
  document.getElementById("filter-tb").value = "";
  document.getElementById("filter-status").value = "";
  document.getElementById("check-include-stopped").checked = false;
  onlyFavoritesFilter = false;
  updateFavoritesBtnStyle();
  executeSearch(true);
}

function toggleFavoritesOnly() {
  onlyFavoritesFilter = !onlyFavoritesFilter;
  updateFavoritesBtnStyle();
  executeSearch(true);
}

function updateFavoritesBtnStyle() {
  const btn = document.getElementById("btn-toggle-favorites");
  const label = document.getElementById("fav-btn-label");
  if (!btn) return;
  if (onlyFavoritesFilter) {
    btn.style.background = "#fef3c7";
    btn.style.borderColor = "#f59e0b";
    btn.style.color = "#92400e";
    if (label) label.textContent = "★ Favorites Active";
  } else {
    btn.style.background = "";
    btn.style.borderColor = "";
    btn.style.color = "";
    if (label) label.textContent = "Favorites";
  }
}

// Render Public & Delegate Catalog Table
function renderTable(items) {
  const tbody = document.getElementById("items-table-body");
  if (!tbody) return;

  if (!items || items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align:center; padding:36px; color:var(--text-muted);">
          No ETSI deliverables match the search criteria.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = items.map(item => {
    let statusClass = "badge-drafting";
    const st = (item.status || "").toLowerCase();
    if (st.includes("publish")) statusClass = "badge-published";
    else if (st.includes("enquiry") || st.includes("approval") || st.includes("vote")) statusClass = "badge-enquiry";
    else if (st.includes("stop")) statusClass = "badge-stopped";

    const starColor = item.is_favorite ? "#f59e0b" : "#cbd5e1";
    const starFill = item.is_favorite ? "#f59e0b" : "none";

    let downloadButtons = `<span style="color:#cbd5e1; font-size:12px;">-</span>`;
    if (item.pdf_url) {
      downloadButtons = `
        <div style="display:inline-flex; gap:4px; align-items:center;">
          <a href="${item.pdf_url}" target="_blank" class="btn-download-pill pdf" title="Download Official Standard PDF">
            <i data-lucide="file-text" style="width:13px; height:13px;"></i>
            <span>PDF</span>
          </a>
      `;
      if (item.word_url) {
        downloadButtons += `
          <a href="${item.word_url}" target="_blank" class="btn-download-pill word" title="Editable Word Source ZIP Archive">
            <i data-lucide="archive" style="width:13px; height:13px;"></i>
            <span>ZIP</span>
          </a>
        `;
      }
      downloadButtons += `</div>`;
    }

    return `
      <tr class="${item.is_stopped ? 'row-stopped' : ''}">
        <td style="text-align:center;">
          <button class="btn-icon" onclick="toggleFavorite('${escapeHtml(item.wki_id)}', '${escapeHtml(item.doc_number)}', '${escapeHtml(item.title)}', '${escapeHtml(item.technical_body || '')}', '${escapeHtml(item.status || '')}')" title="${item.is_favorite ? 'Remove from favorites' : 'Add to favorites'}">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="${starFill}" stroke="${starColor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
          </button>
        </td>
        <td>
          <a href="javascript:void(0)" onclick="openDrawer('${escapeHtml(item.wki_id)}')" style="font-weight:700; color:var(--etsi-navy); text-decoration:none; font-size:0.92rem;">
            ${escapeHtml(item.reference || item.doc_number)}
          </a>
          <div style="font-size:11px; color:var(--text-muted); font-family:monospace; margin-top:2px;">${escapeHtml(item.wki_id)}</div>
        </td>
        <td>
          <span style="font-size:12px; font-weight:700; color:#475569; background:#f1f5f9; padding:2px 6px; border-radius:4px;">${escapeHtml(item.version || 'v1.1.1')}</span>
        </td>
        <td>
          <span class="badge" style="background:#e0f2fe; color:#0369a1; font-weight:700;">${escapeHtml(item.technical_body || 'ETSI')}</span>
        </td>
        <td>
          <div style="font-size:13px; font-weight:500; color:var(--text-main); line-height:1.45;">
            ${escapeHtml(item.title)}
          </div>
        </td>
        <td>
          <span class="badge ${statusClass}">${escapeHtml(item.status || 'Active')}</span>
          ${item.status_date ? `<div style="font-size:11px; color:var(--text-muted); margin-top:3px;">${escapeHtml(item.status_date)}</div>` : ''}
        </td>
        <td style="text-align:center;">
          ${downloadButtons}
        </td>
        <td style="text-align:right; white-space:nowrap;">
          <button class="btn-action-detail" onclick="openDrawer('${escapeHtml(item.wki_id)}')" title="View deliverable details and milestones">
            <i data-lucide="eye" style="width:13px; height:13px;"></i>
            <span>Detail</span>
            <i data-lucide="chevron-right" style="width:13px; height:13px;"></i>
          </button>
        </td>
      </tr>
    `;
  }).join("");

  lucide.createIcons();
}

// Render Secretariat Back-Office (WPM.exe) Table
function renderAdminTable(items) {
  const tbody = document.getElementById("admin-table-body");
  if (!tbody) return;

  if (!items || items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align:center; padding:36px; color:var(--text-muted);">
          No Work Items recorded in administrative database.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = items.map(item => {
    let statusClass = "badge-drafting";
    const st = (item.status || "").toLowerCase();
    if (st.includes("publish")) statusClass = "badge-published";
    else if (st.includes("enquiry") || st.includes("approval") || st.includes("vote")) statusClass = "badge-enquiry";
    else if (st.includes("stop")) statusClass = "badge-stopped";

    return `
      <tr>
        <td>
          <code style="font-weight:700; color:var(--etsi-navy); font-size:12px; background:#f1f5f9; padding:2px 6px; border-radius:4px;">${escapeHtml(item.wki_id)}</code>
        </td>
        <td>
          <div style="font-weight:700; font-size:0.9rem;">${escapeHtml(item.reference || item.doc_number)}</div>
          <div style="font-size:11px; color:var(--text-muted); margin-top:1px;">${escapeHtml(item.version || 'v1.1.1')}</div>
        </td>
        <td>
          <span class="badge" style="background:#e0f2fe; color:#0369a1; font-weight:700;">${escapeHtml(item.technical_body || 'ETSI')}</span>
        </td>
        <td>
          <div style="font-size:13px; line-height:1.45;">${escapeHtml(item.title)}</div>
        </td>
        <td>
          <span class="badge ${statusClass}">${escapeHtml(item.status || 'Active')}</span>
        </td>
        <td style="text-align:center;">
          ${item.is_stopped ? '<span class="badge badge-stopped">YES</span>' : '<span style="color:#94a3b8; font-size:12px;">No</span>'}
        </td>
        <td style="text-align:right; white-space:nowrap;">
          <div style="display:inline-flex; gap:6px;">
            <button class="btn-action-detail" onclick="openDrawer('${escapeHtml(item.wki_id)}')" title="Manage deliverable">
              <i data-lucide="sliders" style="width:12px; height:12px;"></i>
              <span>Manage</span>
            </button>
            <button class="btn-action-clone" onclick="quickClone('${escapeHtml(item.wki_id)}')" title="Revise / Clone">
              <i data-lucide="git-branch" style="width:12px; height:12px;"></i>
              <span>Revise</span>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join("");

  lucide.createIcons();
}

// Favorites Toggle
async function toggleFavorite(wkiId, docNumber, title, tb, status) {
  try {
    const res = await fetch(`${API_BASE}/api/favorites/toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        wki_id: wkiId,
        doc_number: docNumber,
        title: title,
        technical_body: tb,
        status: status
      })
    });
    if (!res.ok) throw new Error("Could not update favorite status.");
    const data = await res.json();

    // Update in currentItems
    const it = currentItems.find(x => x.wki_id === wkiId);
    if (it) it.is_favorite = data.is_favorite;

    renderTable(currentItems);
    showToast(data.is_favorite ? "Added to favorites ★" : "Removed from favorites", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Drawer: Open / Close & Content rendering
async function openDrawer(wkiId) {
  selectedWkiId = wkiId;
  const drawer = document.getElementById("drawer-panel");
  const backdrop = document.getElementById("drawer-backdrop");
  const body = document.getElementById("drawer-body");

  if (drawer && backdrop) {
    backdrop.style.display = "block";
    drawer.classList.add("open");
  }

  body.innerHTML = `<div style="text-align:center; padding:32px; color:var(--text-muted);"><i data-lucide="loader" class="spin"></i> Loading deliverable...</div>`;
  lucide.createIcons();

  try {
    const res = await fetch(`${API_BASE}/api/work-items/${encodeURIComponent(wkiId)}`);
    if (!res.ok) throw new Error("Deliverable not found.");
    const wi = await res.json();

    document.getElementById("drawer-ref-title").textContent = wi.reference || wi.doc_number;
    document.getElementById("drawer-version-pill").textContent = wi.latest_version || "v1.1.1";

    let statusClass = "badge-drafting";
    const st = (wi.current_status || "").toLowerCase();
    if (st.includes("publish")) statusClass = "badge-published";
    else if (st.includes("enquiry") || st.includes("approval") || st.includes("vote")) statusClass = "badge-enquiry";
    else if (st.includes("stop")) statusClass = "badge-stopped";

    document.getElementById("drawer-status-pill").innerHTML = `
      <span class="badge ${statusClass}">${escapeHtml(wi.current_status || 'Drafting')}</span>
      ${wi.status_date ? `<span style="font-size:12px; color:var(--text-muted); margin-left:8px;">as of ${escapeHtml(wi.status_date)}</span>` : ''}
    `;

    // Download buttons in drawer header
    const pdfBtn = document.getElementById("drawer-pdf-link");
    const wordBtn = document.getElementById("drawer-word-link");
    if (wi.pdf_url) {
      pdfBtn.href = wi.pdf_url;
      pdfBtn.style.display = "inline-flex";
    } else {
      pdfBtn.style.display = "none";
    }
    if (wi.word_url) {
      wordBtn.href = wi.word_url;
      wordBtn.style.display = "inline-flex";
    } else {
      wordBtn.style.display = "none";
    }

    // Star icon update
    const favBtn = document.getElementById("drawer-fav-btn");
    if (favBtn) {
      favBtn.style.color = wi.is_favorite ? "#f59e0b" : "var(--text-muted)";
    }

    // Schedule Timeline HTML
    const scheduleHtml = (wi.schedule && wi.schedule.length > 0) ? `
      <div class="timeline-stepper">
        ${wi.schedule.map(s => {
          let stepClass = "step-pending";
          if (s.status === "ACHIEVED") stepClass = "step-achieved";
          else if (s.status === "IN_PROGRESS") stepClass = "step-progress";

          return `
            <div class="timeline-item ${stepClass}">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <strong style="font-size:13px; color:var(--etsi-navy);">${escapeHtml(s.mls_name)} - ${escapeHtml(s.mls_code)}</strong>
                  <span class="badge" style="font-size:10px;">${escapeHtml(s.status)}</span>
                </div>
                <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">
                  Target: <b>${escapeHtml(s.target_date || 'N/A')}</b> &bull; Statutory Duration: ${s.duration_days} days
                </div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    ` : `<p style="color:var(--text-muted); font-size:13px;">No statutory milestones configured.</p>`;

    // Frequencies HTML
    const freqsHtml = (wi.frequencies && wi.frequencies.length > 0) ? `
      <table class="etsi-table" style="font-size:12px;">
        <thead>
          <tr>
            <th>Frequency Band</th>
            <th>Radio Service RED</th>
          </tr>
        </thead>
        <tbody>
          ${wi.frequencies.map(f => `
            <tr>
              <td><b>${f.low_freq} &ndash; ${f.high_freq} ${escapeHtml(f.unit)}</b></td>
              <td>${escapeHtml(f.service_app || 'N/A')}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    ` : `<p style="color:var(--text-muted); font-size:13px;">No radio frequency band allocated.</p>`;

    // Mandates HTML
    const mandatesHtml = (wi.mandates && wi.mandates.length > 0) ? `
      <div style="display:flex; flex-direction:column; gap:8px;">
        ${wi.mandates.map(m => `
          <div style="padding:10px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; font-size:12px;">
            <div style="font-weight:700; color:#166534;">EC Mandate: ${escapeHtml(m.mandate_code)} - ${escapeHtml(m.directive_ref || 'RED Directive')}</div>
            <div style="color:#14532d; margin-top:2px;">${escapeHtml(m.descript || '')}</div>
          </div>
        `).join("")}
      </div>
    ` : `<p style="color:var(--text-muted); font-size:13px;">No European Commission mandate recorded.</p>`;

    // Remarks HTML
    const remarksHtml = (wi.remarks && wi.remarks.length > 0) ? wi.remarks.map(r => `
      <div style="padding:12px; background:#f8fafc; border:1px solid var(--border-color); border-radius:8px; margin-bottom:8px; font-size:12px;">
        <div style="display:flex; justify-content:space-between; color:var(--text-muted); margin-bottom:4px;">
          <span><b>${escapeHtml(r.author || 'Admin')}</b> [${escapeHtml(r.remark_type || 'NOTE')}]</span>
          <span>${escapeHtml(r.created_at ? r.created_at.substring(0, 16) : '')}</span>
        </div>
        <div style="color:var(--text-main); line-height:1.45;">${escapeHtml(r.remark_text)}</div>
      </div>
    `).join("") : `<p style="color:var(--text-muted); font-size:13px;">No administrative remarks recorded.</p>`;

    // Full Drawer Body HTML
    body.innerHTML = `
      <div class="drawer-section">
        <h4 style="color:var(--etsi-navy); margin-bottom:12px;">Statutory Identity &amp; Metadata</h4>
        <div class="drawer-meta-grid" style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:13px;">
          <div><span style="color:var(--text-muted);">Work Item ID:</span> <b>${escapeHtml(wi.wki_id)}</b></div>
          <div><span style="color:var(--text-muted);">Technical Body:</span> <b>${escapeHtml(wi.technical_body || 'ETSI')}</b></div>
          <div><span style="color:var(--text-muted);">Deliverable Type:</span> <b>${escapeHtml(wi.doc_type || 'EN')} - ${escapeHtml(wi.deliv_class || 'Standard')}</b></div>
          <div><span style="color:var(--text-muted);">Standstill:</span> <b>${escapeHtml(wi.standstill || 'NO')}</b></div>
          <div><span style="color:var(--text-muted);">Harmonised Standard:</span> <b>${escapeHtml(wi.harmonised_standard || 'No')}</b></div>
          <div><span style="color:var(--text-muted);">Creation Date:</span> <b>${escapeHtml(wi.creation_date || 'N/A')}</b></div>
        </div>

        ${wi.parent_wki_id ? `
          <div style="margin-top:12px; padding:10px 14px; background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; font-size:12px;">
            <i data-lucide="git-branch" style="width:14px; height:14px; color:#1d4999; vertical-align:middle;"></i>
            Derived from parent deliverable: <a href="javascript:void(0)" onclick="openDrawer('${escapeHtml(wi.parent_wki_id)}')" style="font-weight:700; color:#1d4999;">${escapeHtml(wi.parent_reference || wi.parent_wki_id)}</a>
          </div>
        ` : ''}
      </div>

      <div class="drawer-section">
        <h4 style="color:var(--etsi-navy); margin-bottom:8px;">Project Officers</h4>
        <div style="font-size:13px; line-height:1.6;">
          <div><b>Rapporteur:</b> ${escapeHtml(wi.rapporteur_name || 'Not assigned')} ${wi.rapporteur_email ? `&bull; <a href="mailto:${escapeHtml(wi.rapporteur_email)}">${escapeHtml(wi.rapporteur_email)}</a>` : ''}</div>
          <div><b>Technical Officer:</b> ${escapeHtml(wi.technical_officer_name || 'Secretariat General')} ${wi.technical_officer_email ? `&bull; <a href="mailto:${escapeHtml(wi.technical_officer_email)}">${escapeHtml(wi.technical_officer_email)}</a>` : ''}</div>
        </div>
      </div>

      <div class="drawer-section">
        <h4 style="color:var(--etsi-navy); margin-bottom:8px;">Scope &amp; Official Title</h4>
        <div style="font-size:13px; font-weight:600; color:var(--text-main); margin-bottom:8px;">
          ${escapeHtml(wi.title)}
        </div>
        <p style="font-size:12px; color:var(--text-muted); line-height:1.5;">
          ${escapeHtml(wi.scope_remarks || 'No detailed scope description recorded.')}
        </p>
      </div>

      <div class="drawer-section">
        <h4 style="color:var(--etsi-navy); margin-bottom:12px;">Statutory Milestones &amp; Waterfall Schedule</h4>
        ${scheduleHtml}
      </div>

      <div class="drawer-section">
        <h4 style="color:var(--etsi-navy); margin-bottom:12px;">Radio Frequency Spectrum RED Directive 2014/53/EU</h4>
        ${freqsHtml}
      </div>

      <div class="drawer-section">
        <h4 style="color:var(--etsi-navy); margin-bottom:12px;">European Commission Mandates</h4>
        ${mandatesHtml}
      </div>

      <div class="drawer-section">
        <h4 style="color:var(--etsi-navy); margin-bottom:12px;">Audit Trail &amp; Administrative Remarks</h4>
        <div id="drawer-remarks-list">
          ${remarksHtml}
        </div>

        <form onsubmit="event.preventDefault(); submitDrawerRemark('${escapeHtml(wi.wki_id)}');" style="margin-top:16px;">
          <div class="form-group">
            <label for="new-remark-text" style="font-size:12px;">Add an administrative audit note</label>
            <textarea id="new-remark-text" rows="2" placeholder="Enter an official remark or decision..." required style="font-size:12px;"></textarea>
          </div>
          <div style="display:flex; justify-content:flex-end; margin-top:8px;">
            <button type="submit" class="btn btn-primary" style="font-size:12px; padding:6px 14px;">
              <i data-lucide="send" style="width:13px; height:13px;"></i>
              <span>Post Remark</span>
            </button>
          </div>
        </form>
      </div>
    `;

    lucide.createIcons();
  } catch (err) {
    body.innerHTML = `<div style="color:var(--danger); padding:24px;">Failed to load deliverable: ${escapeHtml(err.message)}</div>`;
  }
}

function closeDrawer() {
  const drawer = document.getElementById("drawer-panel");
  const backdrop = document.getElementById("drawer-backdrop");
  if (drawer && backdrop) {
    drawer.classList.remove("open");
    backdrop.style.display = "none";
  }
  selectedWkiId = null;
}

async function toggleCurrentDrawerFavorite() {
  if (!selectedWkiId) return;
  const item = currentItems.find(x => x.wki_id === selectedWkiId);
  if (item) {
    await toggleFavorite(item.wki_id, item.doc_number, item.title, item.technical_body, item.status);
    openDrawer(selectedWkiId);
  }
}

function cloneCurrentFromDrawer() {
  if (!selectedWkiId) return;
  const targetId = selectedWkiId;
  closeDrawer();
  switchTab("clone");
  setTimeout(() => {
    const sel = document.getElementById("clone-source-wki");
    if (sel) {
      sel.value = targetId;
      prefillCloneModal();
    }
  }, 100);
}

function quickClone(wkiId) {
  switchTab("clone");
  setTimeout(() => {
    const sel = document.getElementById("clone-source-wki");
    if (sel) {
      sel.value = wkiId;
      prefillCloneModal();
    }
  }, 100);
}

// Drawer: Submit Remark
async function submitDrawerRemark(wkiId) {
  const textEl = document.getElementById("new-remark-text");
  if (!textEl || !textEl.value.trim()) return;

  try {
    const res = await fetch(`${API_BASE}/api/work-items/${encodeURIComponent(wkiId)}/remarks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        remark_type: "ADMIN",
        remark_text: textEl.value.trim(),
        author: "Secretariat Officer"
      })
    });
    if (!res.ok) throw new Error("Failed to post administrative remark.");

    showToast("Administrative remark posted successfully.", "success");
    openDrawer(wkiId);
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Number Generator (frmNextETSINumber)
async function runNumberGenerator() {
  const docType = document.getElementById("num-doc-type")?.value || "EN";
  const tb = document.getElementById("num-tb")?.value || "CYBER";

  try {
    const res = await fetch(`${API_BASE}/api/numbering/next`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ doc_type: docType, technical_body: tb })
    });
    if (!res.ok) throw new Error("Failed to generate ETSI number.");

    const data = await res.json();
    document.getElementById("gen-assigned-number").textContent = data.assigned_number;
    document.getElementById("gen-formatted-ref").textContent = data.formatted_reference;
    document.getElementById("gen-rule-applied").innerHTML = `<b>Statutory Rule:</b> ${escapeHtml(data.rule_applied)}`;

    const pillsContainer = document.getElementById("gen-candidate-pills");
    if (pillsContainer) {
      pillsContainer.innerHTML = (data.candidate_numbers || []).map(num => `
        <button class="btn btn-secondary" onclick="selectCandidateNumber('${num}')" style="padding:5px 12px; font-family:monospace; font-weight:700;">
          ${num}
        </button>
      `).join("");
    }
  } catch (err) {
    console.error(err);
  }
}

function selectCandidateNumber(num) {
  document.getElementById("gen-assigned-number").textContent = num;
  const docType = document.getElementById("num-doc-type").value;
  document.getElementById("gen-formatted-ref").textContent = `ETSI ${docType} ${num}`;
  showToast(`Number ${num} selected for allocation.`, "info");
}

function useGeneratedNumberInCreation() {
  const docType = document.getElementById("num-doc-type").value;
  const docNum = document.getElementById("gen-assigned-number").textContent;
  const tb = document.getElementById("num-tb").value;

  openCreateModal();
  document.getElementById("c-doc-type").value = docType;
  document.getElementById("c-doc-number").value = docNum;
  document.getElementById("c-tb").value = tb;
}

// Clone Work Item (frmCloneWI)
function populateCloneDropdown() {
  const sel = document.getElementById("clone-source-wki");
  if (!sel) return;

  sel.innerHTML = `<option value="">Select a source Work Item...</option>` +
    currentItems.map(item => `
      <option value="${escapeHtml(item.wki_id)}">${escapeHtml(item.reference || item.doc_number)} - ${escapeHtml(item.title.substring(0, 50))} - ${item.wki_id}</option>
    `).join("");
}

function prefillCloneModal() {
  const wkiId = document.getElementById("clone-source-wki")?.value;
  if (!wkiId) return;

  const item = currentItems.find(x => x.wki_id === wkiId);
  if (item) {
    document.getElementById("clone-new-tb").value = item.technical_body || "";
    document.getElementById("clone-new-docnum").value = item.doc_number || "";
    document.getElementById("clone-new-title").value = item.title ? item.title.split(";")[1]?.trim() || item.title : "";
  }
}

async function submitCloneWorkItem() {
  const sourceWki = document.getElementById("clone-source-wki")?.value;
  if (!sourceWki) {
    showToast("Please select a source Work Item.", "warning");
    return;
  }

  const cloneType = document.getElementById("clone-type-select").value;
  const schedOption = document.getElementById("clone-sched-option").value;
  const newTb = document.getElementById("clone-new-tb").value.trim();
  const newDocNum = document.getElementById("clone-new-docnum").value.trim();
  const newTitle = document.getElementById("clone-new-title").value.trim();
  const retainComments = document.getElementById("clone-retain-comments").checked;

  startProgress();
  try {
    const res = await fetch(`${API_BASE}/api/work-items/${encodeURIComponent(sourceWki)}/clone`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clone_type: cloneType,
        schedule_option: schedOption,
        new_tb: newTb || null,
        new_doc_number: newDocNum || null,
        new_title_part1: newTitle || null,
        retain_comments: retainComments
      })
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Statutory derivation failed.");
    }

    const cloned = await res.json();
    showToast(`Derivation successful! New deliverable created: ${cloned.reference}`, "success");
    fetchKPIs();
    executeSearch();
    switchTab("catalog");
    setTimeout(() => openDrawer(cloned.wki_id), 300);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    finishProgress();
  }
}

// Plan Parfait Simulator (compute_perfect_plan)
async function calculatePlan() {
  const docType = document.getElementById("plan-doc-type").value;
  const startDate = document.getElementById("plan-start-date").value || new Date().toISOString().split("T")[0];

  try {
    const res = await fetch(`${API_BASE}/api/schedule/perfect-plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ doc_type: docType, start_date: startDate })
    });
    if (!res.ok) throw new Error("Failed to compute statutory schedule.");

    const data = await res.json();
    const tbody = document.getElementById("plan-results-body");
    if (!tbody) return;

    tbody.innerHTML = (data.plan || []).map(p => `
      <tr>
        <td style="font-weight:700;">${p.sched_position}</td>
        <td><code>${escapeHtml(p.mls_code)}</code></td>
        <td><b>${escapeHtml(p.mls_name)}</b></td>
        <td style="text-align:center;">${p.duration_days} days</td>
        <td style="color:var(--etsi-navy); font-weight:700;">${p.target_date}</td>
      </tr>
    `).join("");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Load Frequencies & Mandates
async function loadFrequenciesAndMandates() {
  const freqTbody = document.getElementById("freq-table-body");
  const mandTbody = document.getElementById("mandates-table-body");
  if (!freqTbody || !mandTbody) return;

  try {
    const details = await Promise.all(
      currentItems.slice(0, 15).map(it => fetch(`${API_BASE}/api/work-items/${encodeURIComponent(it.wki_id)}`).then(r => r.json()))
    );

    let allFreqs = [];
    let allMandates = [];
    details.forEach(wi => {
      (wi.frequencies || []).forEach(f => allFreqs.push({ ...f, ref: wi.reference, wki_id: wi.wki_id }));
      (wi.mandates || []).forEach(m => allMandates.push({ ...m, ref: wi.reference, wki_id: wi.wki_id }));
    });

    if (allFreqs.length === 0) {
      freqTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:20px; color:var(--text-muted);">No radio frequency bands recorded.</td></tr>`;
    } else {
      freqTbody.innerHTML = allFreqs.map(f => `
        <tr>
          <td><a href="javascript:void(0)" onclick="openDrawer('${escapeHtml(f.wki_id)}')" style="font-weight:700; color:var(--etsi-navy);">${escapeHtml(f.ref)}</a></td>
          <td><b>${f.low_freq}</b></td>
          <td><b>${f.high_freq}</b></td>
          <td>${escapeHtml(f.unit)}</td>
          <td>${escapeHtml(f.service_app || 'N/A')}</td>
        </tr>
      `).join("");
    }

    if (allMandates.length === 0) {
      mandTbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:20px; color:var(--text-muted);">No European Commission mandates recorded.</td></tr>`;
    } else {
      mandTbody.innerHTML = allMandates.map(m => `
        <tr>
          <td><a href="javascript:void(0)" onclick="openDrawer('${escapeHtml(m.wki_id)}')" style="font-weight:700; color:var(--etsi-navy);">${escapeHtml(m.ref)}</a></td>
          <td><span class="badge" style="background:#dcfce7; color:#166534; font-weight:700;">${escapeHtml(m.mandate_code)}</span></td>
          <td><b>${escapeHtml(m.directive_ref || 'RED 2014/53/EU')}</b></td>
          <td>${escapeHtml(m.descript || '')}</td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Failed to load freqs and mandates:", err);
  }
}

// Add Frequency Modal
function openAddFreqModal() {
  const sel = document.getElementById("freq-wki-select");
  if (sel) {
    sel.innerHTML = currentItems.map(it => `
      <option value="${escapeHtml(it.wki_id)}">${escapeHtml(it.reference || it.doc_number)} - ${escapeHtml(it.title.substring(0, 40))}</option>
    `).join("");
  }
  document.getElementById("modal-freq-backdrop").style.display = "flex";
}

function closeAddFreqModal() {
  document.getElementById("modal-freq-backdrop").style.display = "none";
}

async function submitAddFrequency() {
  const wkiId = document.getElementById("freq-wki-select").value;
  const low = parseFloat(document.getElementById("freq-low").value);
  const high = parseFloat(document.getElementById("freq-high").value);
  const unit = document.getElementById("freq-unit").value;
  const app = document.getElementById("freq-app").value.trim();

  try {
    const res = await fetch(`${API_BASE}/api/work-items/${encodeURIComponent(wkiId)}/frequencies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        low_freq: low,
        high_freq: high,
        unit: unit,
        service_app: app
      })
    });
    if (!res.ok) {
      const d = await res.json();
      throw new Error(d.detail || "Failed to allocate frequency band.");
    }

    showToast("Radio frequency allocation saved successfully.", "success");
    closeAddFreqModal();
    loadFrequenciesAndMandates();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Create Work Item Modal
function openCreateModal() {
  document.getElementById("modal-create-backdrop").style.display = "flex";
  handleCreateTypeChange();
}

function closeCreateModal() {
  document.getElementById("modal-create-backdrop").style.display = "none";
}

function handleCreateTypeChange() {
  const docType = document.getElementById("c-doc-type").value;
  const standstill = document.getElementById("c-standstill");
  if (standstill) {
    standstill.value = (docType === "EN") ? "YES" : "NO";
  }
}

async function submitCreateWorkItem() {
  const docType = document.getElementById("c-doc-type").value;
  const docNumber = document.getElementById("c-doc-number").value.trim();
  const tb = document.getElementById("c-tb").value;
  const title1 = document.getElementById("c-title-part1").value.trim();
  const title2 = document.getElementById("c-title-part2").value.trim();
  const title3 = document.getElementById("c-title-part3").value.trim();
  const rapName = document.getElementById("c-rapporteur-name").value.trim();
  const rapEmail = document.getElementById("c-rapporteur-email").value.trim();
  const supName = document.getElementById("c-support-name").value.trim();
  const supEmail = document.getElementById("c-support-email").value.trim();
  const standstill = document.getElementById("c-standstill").value;
  const version = document.getElementById("c-version").value.trim() || "v1.1.1";
  const mandate = document.getElementById("c-mandate").value.trim();
  const scope = document.getElementById("c-scope").value.trim();
  const harmonized = document.getElementById("c-harmonized").checked;

  startProgress();
  try {
    const res = await fetch(`${API_BASE}/api/work-items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doc_type: docType,
        doc_number: docNumber,
        technical_body: tb,
        title_part1: title1,
        title_part2: title2 || null,
        title_part3: title3 || null,
        rapporteur_name: rapName,
        rapporteur_email: rapEmail || null,
        support_officer_name: supName,
        support_officer_email: supEmail || null,
        standstill_status: standstill,
        version: version,
        ec_mandate: mandate || null,
        scope: scope || null,
        harmonized_flag: harmonized
      })
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to create work item.");
    }

    const created = await res.json();
    showToast(`Work Item ${created.reference} created successfully!`, "success");
    closeCreateModal();
    fetchKPIs();
    executeSearch();
    setTimeout(() => openDrawer(created.wki_id), 300);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    finishProgress();
  }
}

// Live Portal Sync
async function triggerPortalSync() {
  startProgress();
  showToast("Querying official portal portal.etsi.org...", "info");
  try {
    const q = document.getElementById("filter-q")?.value || "";
    const tb = document.getElementById("filter-tb")?.value || "";
    const docType = document.getElementById("filter-type")?.value || "";

    const params = new URLSearchParams();
    if (q) params.set("query", q);
    if (tb) params.set("tb", tb);
    if (docType) params.set("doc_type", docType);

    const res = await fetch(`${API_BASE}/api/sync/portal?${params.toString()}`, { method: "POST" });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message, "success");
    } else {
      showToast(data.message, "warning");
    }
    fetchKPIs();
    executeSearch();
  } catch (err) {
    showToast("Portal synchronization failed.", "error");
  } finally {
    finishProgress();
  }
}

// Export Data (CSV or JSON)
function exportData(format = "csv") {
  const tb = document.getElementById("filter-tb")?.value || "";
  const docType = document.getElementById("filter-type")?.value || "";
  const status = document.getElementById("filter-status")?.value || "";
  const includeStopped = document.getElementById("check-include-stopped")?.checked || false;

  const params = new URLSearchParams();
  params.set("format", format);
  if (tb) params.set("tb", tb);
  if (docType) params.set("doc_type", docType);
  if (status) params.set("status", status);
  if (includeStopped) params.set("include_stopped", "true");

  window.open(`${API_BASE}/api/export?${params.toString()}`, "_blank");
}

// Utility: Escape HTML
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Load Technical Bodies dynamically
async function loadTechnicalBodies() {
  try {
    const res = await fetch(`${API_BASE}/api/technical-bodies`);
    if (!res.ok) return;
    const tbs = await res.json();
    if (!Array.isArray(tbs) || tbs.length === 0) return;

    // Filter dropdown
    const filterTb = document.getElementById("filter-tb");
    if (filterTb) {
      const cur = filterTb.value;
      filterTb.innerHTML = `<option value="">All Technical Bodies</option>` +
        tbs.map(t => {
          const cleanDesc = (t.name || '').replace(new RegExp('^' + t.code + '\\s*-\\s*'), '');
          return `<option value="${escapeHtml(t.code)}">${escapeHtml(t.code)} &bull; ${escapeHtml(cleanDesc || t.code)}</option>`;
        }).join("");
      if (cur) filterTb.value = cur;
    }

    // Numbering modal TB dropdown
    const numTb = document.getElementById("num-tb");
    if (numTb) {
      const cur = numTb.value;
      numTb.innerHTML = tbs.map(t => `<option value="${escapeHtml(t.code)}">${escapeHtml(t.code)} - ${escapeHtml(t.name || t.code)}</option>`).join("");
      if (cur) numTb.value = cur;
    }

    // Schedule TB dropdown
    const schedTb = document.getElementById("plan-tb");
    if (schedTb) {
      const cur = schedTb.value;
      schedTb.innerHTML = tbs.map(t => `<option value="${escapeHtml(t.code)}">${escapeHtml(t.code)} - ${escapeHtml(t.name || t.code)}</option>`).join("");
      if (cur) schedTb.value = cur;
    }
  } catch (err) {
    console.error("Failed to load technical bodies:", err);
  }
}

// Global Initialization
window.addEventListener("DOMContentLoaded", () => {
  loadTechnicalBodies();
  fetchKPIs();
  executeSearch(true);
});
