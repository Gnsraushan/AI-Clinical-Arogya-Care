/**
 * ArogyaCare - Patient History Script
 * Handles real-time timeline filtering, sorting, and dynamic record modal view.
 */

document.addEventListener('DOMContentLoaded', () => {
    initSearchAndFilter();
    initModalAccessibility();
});

/**
 * Mobile Navigation Drawer Toggle
 */
function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar && overlay) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
    }
}

/**
 * Search & Sorting Engine
 */
function initSearchAndFilter() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    const sortOrder = document.getElementById('sortOrder');
    
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.trim();
            if (clearBtn) {
                clearBtn.style.display = query.length > 0 ? 'flex' : 'none';
            }
            filterRecords();
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', resetSearch);
    }

    if (sortOrder) {
        sortOrder.addEventListener('change', sortTimeline);
    }
}

function resetSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    if (searchInput) {
        searchInput.value = '';
    }
    if (clearBtn) {
        clearBtn.style.display = 'none';
    }
    filterRecords();
}

function filterRecords() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const items = document.querySelectorAll('.timeline-item');
    const noResults = document.getElementById('noSearchResults');
    let visibleCount = 0;

    items.forEach(item => {
        const problem = item.getAttribute('data-problem') || '';
        const symptoms = item.getAttribute('data-symptoms') || '';
        const summary = item.getAttribute('data-summary') || '';
        const date = item.getAttribute('data-date') || '';

        const matches = problem.includes(query) || 
                        symptoms.includes(query) || 
                        summary.includes(query) || 
                        date.toLowerCase().includes(query);

        if (matches) {
            item.style.display = 'block';
            visibleCount++;
        } else {
            item.style.display = 'none';
        }
    });

    if (noResults) {
        noResults.style.display = (visibleCount === 0 && items.length > 0) ? 'block' : 'none';
    }
}

function sortTimeline() {
    const sortOrder = document.getElementById('sortOrder');
    const timelineContainer = document.getElementById('timelineContainer');
    if (!sortOrder || !timelineContainer) return;

    const items = Array.from(timelineContainer.querySelectorAll('.timeline-item'));
    const isNewest = sortOrder.value === 'newest';

    items.sort((a, b) => {
        const dateA = new Date(a.getAttribute('data-date') || 0);
        const dateB = new Date(b.getAttribute('data-date') || 0);
        
        // Handle invalid dates gracefully by falling back to ID
        if (isNaN(dateA) || isNaN(dateB)) {
            const idA = parseInt(a.getAttribute('data-id') || 0);
            const idB = parseInt(b.getAttribute('data-id') || 0);
            return isNewest ? idB - idA : idA - idB;
        }

        return isNewest ? dateB - dateA : dateA - dateB;
    });

    // Re-append items in sorted order
    items.forEach(item => timelineContainer.appendChild(item));
}

/**
 * Modal Handling & Data Binding
 */
function openRecordModal(buttonElement) {
    const card = buttonElement.closest('.record-card');
    if (!card) return;

    const dataScript = card.querySelector('.record-data');
    if (!dataScript) return;

    try {
        const data = JSON.parse(dataScript.textContent);

        // Bind fields
        document.getElementById('modalDate').textContent = data.date || 'Not specified';
        document.getElementById('modalMainProblem').textContent = data.main_problem || 'Not available';
        document.getElementById('modalDuration').textContent = data.duration || 'Not specified';
        document.getElementById('modalSymptoms').textContent = data.symptoms || 'None recorded';
        document.getElementById('modalMedicalHistory').textContent = data.medical_history || 'None reported';
        document.getElementById('modalMedicines').textContent = data.medicines || 'None currently taking';
        document.getElementById('modalAllergies').textContent = data.allergies || 'No known allergies';
        document.getElementById('modalSummary').textContent = data.summary || 'No AI summary generated.';

        const modal = document.getElementById('recordModal');
        if (modal) {
            modal.classList.add('open');
            modal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden'; // Prevent screen scroll under modal
        }
    } catch (e) {
        console.error('Error parsing clinical record details:', e);
    }
}

function closeRecordModal() {
    const modal = document.getElementById('recordModal');
    if (modal) {
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }
}

function initModalAccessibility() {
    // Close modal on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeRecordModal();
        }
    });

    // Close modal when clicking outside dialog
    const modal = document.getElementById('recordModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeRecordModal();
            }
        });
    }
}