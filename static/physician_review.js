/* ============================================================
   ArogyaCare — Physician Review (Patient view)
   Vanilla JS only. No fake network calls, no fabricated data.
   ============================================================ */

(function () {
  "use strict";

  /* ---------- Mobile navigation drawer ---------- */
  function initMobileNav() {
    var toggle = document.getElementById("navToggle");
    var nav = document.getElementById("primaryNav");
    var scrim = document.getElementById("navScrim");

    if (!toggle || !nav || !scrim) return;

    function openNav() {
      nav.classList.add("is-open");
      scrim.hidden = false;
      requestAnimationFrame(function () {
        scrim.classList.add("is-visible");
      });
      toggle.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";
    }

    function closeNav() {
      nav.classList.remove("is-open");
      scrim.classList.remove("is-visible");
      toggle.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
      window.setTimeout(function () {
        if (!nav.classList.contains("is-open")) {
          scrim.hidden = true;
        }
      }, 280);
    }

    toggle.addEventListener("click", function () {
      var isOpen = nav.classList.contains("is-open");
      if (isOpen) {
        closeNav();
      } else {
        openNav();
      }
    });

    scrim.addEventListener("click", closeNav);

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        closeNav();
        toggle.focus();
      }
    });

    // Close the drawer automatically if the viewport grows back to desktop.
    window.addEventListener("resize", function () {
      if (window.innerWidth > 860 && nav.classList.contains("is-open")) {
        closeNav();
      }
    });
  }

  /* ---------- Expand / collapse the AI summary text ---------- */
  function initSummaryToggle() {
    var text = document.getElementById("aiSummaryText");
    var toggleBtn = document.getElementById("aiSummaryToggle");

    if (!text || !toggleBtn) return;

    // Only show the toggle if the content actually overflows the clamp.
    var needsToggle = text.scrollHeight > text.clientHeight + 4;
    if (!needsToggle) {
      toggleBtn.hidden = true;
      return;
    }

    toggleBtn.hidden = false;

    toggleBtn.addEventListener("click", function () {
      var isCollapsed = text.getAttribute("data-collapsed") === "true";
      if (isCollapsed) {
        text.setAttribute("data-collapsed", "false");
        toggleBtn.textContent = "Show less";
        toggleBtn.setAttribute("aria-expanded", "true");
      } else {
        text.setAttribute("data-collapsed", "true");
        toggleBtn.textContent = "Show more";
        toggleBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- Safe placeholder navigation ----------
     Links marked data-fallback="true" point to pages that may not
     yet have a live Flask route wired up. If the href resolves to
     a real, non-placeholder URL, let the browser navigate normally.
     Otherwise, prevent a dead click and let the user know. */
  function initSafeNavigation() {
    var fallbackLinks = document.querySelectorAll('[data-fallback="true"]');

    fallbackLinks.forEach(function (link) {
      link.addEventListener("click", function (event) {
        var href = link.getAttribute("href");
        if (!href || href === "#") {
          event.preventDefault();
          announce(link.textContent.trim() + " isn't connected yet.");
        }
        // If href is a real route provided by Flask/Jinja, the browser
        // will navigate normally — no extra JS needed.
      });
    });
  }

  /* ---------- Small, accessible status message for placeholder taps ---------- */
  var liveRegion = null;
  function announce(message) {
    if (!liveRegion) {
      liveRegion = document.createElement("div");
      liveRegion.setAttribute("role", "status");
      liveRegion.setAttribute("aria-live", "polite");
      liveRegion.className = "visually-hidden";
      document.body.appendChild(liveRegion);
    }
    liveRegion.textContent = message;
  }

  /* ---------- Init ---------- */
  document.addEventListener("DOMContentLoaded", function () {
    initMobileNav();
    initSummaryToggle();
    initSafeNavigation();
  });
})();