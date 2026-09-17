document.addEventListener('DOMContentLoaded', function () {
  // ---------- Mobile navigation drawer ----------
  var menuBtn = document.getElementById('mobileMenuBtn');
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    sidebar.classList.add('open');
    overlay.classList.add('visible');
    menuBtn.setAttribute('aria-expanded', 'true');
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('visible');
    menuBtn.setAttribute('aria-expanded', 'false');
  }

  if (menuBtn && sidebar && overlay) {
    menuBtn.addEventListener('click', function () {
      var isOpen = sidebar.classList.contains('open');
      isOpen ? closeSidebar() : openSidebar();
    });

    overlay.addEventListener('click', closeSidebar);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeSidebar();
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 768) closeSidebar();
    });
  }

  // ---------- Copy ABHA ID ----------
  var copyBtn = document.getElementById('copyAbhaBtn');

  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var value = copyBtn.getAttribute('data-value');
      if (!value) return;

      var doCopiedFeedback = function () {
        var label = copyBtn.querySelector('span');
        var originalText = label ? label.textContent : '';
        copyBtn.classList.add('copied');
        if (label) label.textContent = 'Copied';
        copyBtn.setAttribute('aria-label', 'ABHA ID copied');

        setTimeout(function () {
          copyBtn.classList.remove('copied');
          if (label) label.textContent = originalText;
          copyBtn.setAttribute('aria-label', 'Copy ABHA ID');
        }, 1800);
      };

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value).then(doCopiedFeedback).catch(function () {
          fallbackCopy(value, doCopiedFeedback);
        });
      } else {
        fallbackCopy(value, doCopiedFeedback);
      }
    });
  }

  function fallbackCopy(text, onSuccess) {
    var textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    try {
      document.execCommand('copy');
      onSuccess();
    } catch (err) {
      /* silently ignore — copy is a convenience, not critical */
    }
    document.body.removeChild(textarea);
  }

  // ---------- Edit Details (future-ready, no fake API call) ----------
  var editBtn = document.getElementById('editDetailsBtn');
  if (editBtn && editBtn.disabled) {
    editBtn.addEventListener('click', function (e) {
      e.preventDefault();
    });
  }
});