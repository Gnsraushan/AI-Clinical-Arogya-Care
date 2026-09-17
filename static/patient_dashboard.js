/* =========================================================
   PATIENT DASHBOARD — behaviour
   Vanilla JS only. Page must render and work without any
   of the API calls below succeeding.
========================================================= */

// Placeholder endpoints for future backend wiring.
// Not called automatically — isolated here so they are easy
// to find and connect later.
const API = {
  patientDetails: "/api/patient/details",
  recentCase: "/api/patient/recent-case",
  recentActivity: "/api/patient/recent-activity"
};

document.addEventListener("DOMContentLoaded", initializeDashboard);

function initializeDashboard() {
  const menuBtn = document.getElementById("menuBtn");
  const sidebarClose = document.getElementById("sidebarClose");
  const backdrop = document.getElementById("sidebarBackdrop");
  const logoutBtn = document.getElementById("logoutBtn");

  if (menuBtn) {
    menuBtn.addEventListener("click", openNavigation);
  }
  if (sidebarClose) {
    sidebarClose.addEventListener("click", closeNavigation);
  }
  if (backdrop) {
    backdrop.addEventListener("click", closeNavigation);
  }
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeNavigation();
    }
  });

  document.querySelectorAll(".nav-item").forEach((link) => {
    link.addEventListener("click", () => {
      const section = link.getAttribute("data-section");
      if (section) {
        navigateToSection(section);
      }
      // Close the drawer on mobile after choosing a destination.
      closeNavigation();
    });
  });

  if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
  }
}

function openNavigation() {
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  const menuBtn = document.getElementById("menuBtn");

  if (!sidebar) return;

  sidebar.classList.add("is-open");
  if (backdrop) backdrop.classList.add("is-visible");
  if (menuBtn) menuBtn.setAttribute("aria-expanded", "true");
}

function closeNavigation() {
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  const menuBtn = document.getElementById("menuBtn");

  if (!sidebar) return;

  sidebar.classList.remove("is-open");
  if (backdrop) backdrop.classList.remove("is-visible");
  if (menuBtn) menuBtn.setAttribute("aria-expanded", "false");
}

// Hook for future in-page section tracking / active-state
// syncing once the other patient pages exist. Currently the
// links navigate via normal href, so this only updates the
// visual active state for same-page use.
function navigateToSection(section) {
  document.querySelectorAll(".nav-item").forEach((link) => {
    link.classList.toggle("is-active", link.getAttribute("data-section") === section);
  });
}

function logout() {
  // Wire this up to the real logout route once available,
  // e.g. window.location.href = "/logout";
  console.log("Logout requested.");
}