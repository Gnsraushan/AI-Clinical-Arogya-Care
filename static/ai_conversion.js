/**
 * ArogyaCare - AI Conversation Interface Interactions
 * Standard: Vanilla JavaScript (No Frameworks)
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileNavigation();
  initAutoScrollStream();
  initSummaryCollapse();
  initCopySummary();
});

/**
 * Mobile Navigation Drawer Toggle
 */
function initMobileNavigation() {
  const toggleBtn = document.getElementById('mobileMenuToggle');
  const drawer = document.getElementById('mobileDrawer');

  if (!toggleBtn || !drawer) return;

  toggleBtn.addEventListener('click', () => {
    const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
    toggleBtn.setAttribute('aria-expanded', !isExpanded);
    
    if (isExpanded) {
      drawer.classList.remove('open');
      drawer.setAttribute('aria-hidden', 'true');
    } else {
      drawer.classList.add('open');
      drawer.setAttribute('aria-hidden', 'false');
    }
  });
}

/**
 * Auto-Scroll Conversation Stream to Latest Message on Load
 */
function initAutoScrollStream() {
  const stream = document.getElementById('conversationStream');
  if (stream) {
    stream.scrollTop = stream.scrollHeight;
  }
}

/**
 * Truncate/Expand Long AI Summaries
 */
function initSummaryCollapse() {
  const toggleBtn = document.getElementById('toggleSummaryExpand');
  const summaryText = document.getElementById('summaryText');

  if (!toggleBtn || !summaryText) return;

  const fullText = summaryText.textContent.trim();
  const maxLength = 250;

  if (fullText.length > maxLength) {
    const truncatedText = fullText.slice(0, maxLength) + '...';
    summaryText.textContent = truncatedText;

    toggleBtn.addEventListener('click', () => {
      const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';

      if (isExpanded) {
        summaryText.textContent = truncatedText;
        toggleBtn.textContent = 'Show more';
        toggleBtn.setAttribute('aria-expanded', 'false');
      } else {
        summaryText.textContent = fullText;
        toggleBtn.textContent = 'Show less';
        toggleBtn.setAttribute('aria-expanded', 'true');
      }
    });
  } else {
    toggleBtn.style.display = 'none';
  }
}

/**
 * Copy AI Summary Text to Clipboard with Visual Feedback
 */
function initCopySummary() {
  const copyBtn = document.getElementById('copySummaryBtn');
  const summaryText = document.getElementById('summaryText');

  if (!copyBtn || !summaryText) return;

  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(summaryText.textContent.trim());
      
      const originalHTML = copyBtn.innerHTML;
      copyBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        Copied
      `;
      copyBtn.style.borderColor = 'var(--color-primary-brand)';

      setTimeout(() => {
        copyBtn.innerHTML = originalHTML;
        copyBtn.style.borderColor = '';
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  });
}