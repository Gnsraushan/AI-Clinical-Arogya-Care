document.addEventListener("DOMContentLoaded", function () {

    const doctorGrid = document.getElementById("doctorGrid");
    const loadingState = document.getElementById("loadingState");
    const emptyState = document.getElementById("emptyState");

    const resultCount = document.getElementById("resultCount");

    const doctorSearch = document.getElementById("doctorSearch");
    const clearSearch = document.getElementById("clearSearch");

    const filterBtn = document.getElementById("filterBtn");
    const filtersPanel = document.getElementById("filtersPanel");

    const specialtyFilter =
        document.getElementById("specialtyFilter");

    const locationFilter =
        document.getElementById("locationFilter");

    const availabilityFilter =
        document.getElementById("availabilityFilter");

    const resetFilters =
        document.getElementById("resetFilters");

    const emptyResetBtn =
        document.getElementById("emptyResetBtn");

    const nearMeBtn =
        document.getElementById("nearMeBtn");

    const recommendedBtn =
        document.getElementById("recommendedBtn");


    let doctors = [];


    // =====================================================
    // LOAD DOCTORS
    // =====================================================

    async function loadDoctors() {

        showLoading(true);

        try {

            const response = await fetch(
                "/api/appointments/doctors"
            );

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.error || "Unable to load doctors."
                );
            }

            doctors = Array.isArray(data.doctors)
                ? data.doctors
                : [];

            populateFilters();

            renderDoctors(doctors);

        } catch (error) {

            console.error(
                "FIND DOCTOR ERROR:",
                error
            );

            doctors = [];

            showEmpty(
                "Unable to load doctors right now."
            );

        } finally {

            showLoading(false);

        }
    }


    // =====================================================
    // RENDER DOCTORS
    // =====================================================

    function renderDoctors(list) {

        doctorGrid.innerHTML = "";

        if (!list.length) {

            doctorGrid.style.display = "none";

            emptyState.style.display = "block";

            resultCount.textContent =
                "No matching doctors";

            return;
        }

        doctorGrid.style.display = "grid";

        emptyState.style.display = "none";

        resultCount.textContent =
            `${list.length} doctor${list.length > 1 ? "s" : ""} available`;

        list.forEach(function (doctor) {

            const card =
                createDoctorCard(doctor);

            doctorGrid.appendChild(card);

        });
    }


    // =====================================================
    // CREATE CARD
    // =====================================================

    function createDoctorCard(doctor) {

        const card =
            document.createElement("article");

        card.className = "doctor-card";

        const name =
            doctor.full_name || "Doctor";

        const specialty =
            doctor.department ||
            doctor.staff_role ||
            "Medical Specialist";

        const hospital =
            doctor.hospital ||
            "ArogyaCare Partner Centre";

        const initials =
            getInitials(name);

        card.innerHTML = `

            <div class="doctor-top">

                <div class="doctor-avatar">
                    ${escapeHtml(initials)}
                </div>

                <div class="doctor-info">

                    <h3 title="${escapeHtml(name)}">
                        ${escapeHtml(name)}
                    </h3>

                    <div class="doctor-specialty">
                        ${escapeHtml(specialty)}
                    </div>

                    <div class="doctor-experience">
                        Verified healthcare professional
                    </div>

                </div>

            </div>


            <div class="doctor-hospital">

                <div class="hospital-name">
                    ${escapeHtml(hospital)}
                </div>

                <div class="hospital-location">
                    Consultation centre
                </div>

            </div>


            <div class="doctor-availability">

                <div class="available">

                    <span class="available-dot"></span>

                    Available for appointment

                </div>

                <div class="distance">
                    Nearby
                </div>

            </div>


            <div class="doctor-actions">

                <button
                    type="button"
                    class="profile-btn"
                    data-doctor-id="${doctor.id}">
                    View Profile
                </button>

                <button
                    type="button"
                    class="book-btn"
                    data-doctor-id="${doctor.id}">
                    Book Appointment
                </button>

            </div>
        `;


        // Profile

        const profileBtn =
            card.querySelector(".profile-btn");

        profileBtn.addEventListener(
            "click",
            function () {

                const doctorId =
                    this.dataset.doctorId;

                window.location.href =
                    `/doctor-profile/${doctorId}`;

            }
        );


        // Booking

        const bookBtn =
            card.querySelector(".book-btn");

        bookBtn.addEventListener(
            "click",
            function () {

                const doctorId =
                    this.dataset.doctorId;

                window.location.href =
                    `/book-appointment/${doctorId}`;

            }
        );


        return card;
    }


    // =====================================================
    // FILTERS
    // =====================================================

    function populateFilters() {

        const specialties =
            [...new Set(
                doctors
                    .map(d =>
                        d.department ||
                        d.staff_role
                    )
                    .filter(Boolean)
            )]
            .sort();

        const hospitals =
            [...new Set(
                doctors
                    .map(d => d.hospital)
                    .filter(Boolean)
            )]
            .sort();


        specialtyFilter.innerHTML =
            `<option value="">All specialties</option>`;

        specialties.forEach(function (specialty) {

            specialtyFilter.innerHTML += `
                <option value="${escapeHtml(specialty)}">
                    ${escapeHtml(specialty)}
                </option>
            `;

        });


        locationFilter.innerHTML =
            `<option value="">All hospitals</option>`;

        hospitals.forEach(function (hospital) {

            locationFilter.innerHTML += `
                <option value="${escapeHtml(hospital)}">
                    ${escapeHtml(hospital)}
                </option>
            `;

        });
    }


    function applyFilters() {

        const search =
            doctorSearch.value
                .trim()
                .toLowerCase();

        const specialty =
            specialtyFilter.value
                .trim()
                .toLowerCase();

        const location =
            locationFilter.value
                .trim()
                .toLowerCase();


        const filtered =
            doctors.filter(function (doctor) {

                const name =
                    (doctor.full_name || "")
                        .toLowerCase();

                const department =
                    (
                        doctor.department ||
                        doctor.staff_role ||
                        ""
                    ).toLowerCase();

                const hospital =
                    (doctor.hospital || "")
                        .toLowerCase();

                const matchesSearch =
                    !search ||
                    name.includes(search) ||
                    department.includes(search) ||
                    hospital.includes(search);

                const matchesSpecialty =
                    !specialty ||
                    department === specialty;

                const matchesLocation =
                    !location ||
                    hospital === location;

                return (
                    matchesSearch &&
                    matchesSpecialty &&
                    matchesLocation
                );

            });


        renderDoctors(filtered);

        clearSearch.style.display =
            search ? "block" : "none";
    }


    // =====================================================
    // EVENTS
    // =====================================================

    doctorSearch.addEventListener(
        "input",
        applyFilters
    );


    specialtyFilter.addEventListener(
        "change",
        applyFilters
    );


    locationFilter.addEventListener(
        "change",
        applyFilters
    );


    availabilityFilter.addEventListener(
        "change",
        applyFilters
    );


    filterBtn.addEventListener(
        "click",
        function () {

            filtersPanel.classList.toggle("open");

        }
    );


    clearSearch.addEventListener(
        "click",
        function () {

            doctorSearch.value = "";

            applyFilters();

            doctorSearch.focus();

        }
    );


    resetFilters.addEventListener(
        "click",
        resetAll
    );


    emptyResetBtn.addEventListener(
        "click",
        resetAll
    );


    function resetAll() {

        doctorSearch.value = "";

        specialtyFilter.value = "";

        locationFilter.value = "";

        availabilityFilter.value = "";

        renderDoctors(doctors);

        clearSearch.style.display = "none";
    }


    // =====================================================
    // NEAR ME
    // =====================================================

    nearMeBtn.addEventListener(
        "click",
        function () {

            /*
             * Real location/maps integration will be added
             * later. For now this is a visual/demo action.
             */

            nearMeBtn.classList.toggle("active");

            if (nearMeBtn.classList.contains("active")) {

                nearMeBtn.innerHTML =
                    "<span>✓</span> Nearby selected";

            } else {

                nearMeBtn.innerHTML =
                    "<span>⌖</span> Near me";

            }

        }
    );


    // =====================================================
    // AI RECOMMENDED
    // =====================================================

    recommendedBtn.addEventListener(
        "click",
        function () {

            /*
             * AI specialty recommendation will be connected
             * to the patient's case summary in Step 2.
             */

            const suggestion =
                document.querySelector(".care-suggestion");

            suggestion.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

        }
    );


    // =====================================================
    // HELPERS
    // =====================================================

    function getInitials(name) {

        return name
            .split(" ")
            .filter(Boolean)
            .slice(0, 2)
            .map(word => word[0])
            .join("")
            .toUpperCase();
    }


    function escapeHtml(value) {

        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }


    function showLoading(show) {

        loadingState.style.display =
            show ? "flex" : "none";

        if (show) {

            doctorGrid.style.display = "none";

            emptyState.style.display = "none";

        }
    }


    function showEmpty(message) {

        doctorGrid.style.display = "none";

        emptyState.style.display = "block";

        const paragraph =
            emptyState.querySelector("p");

        if (paragraph) {
            paragraph.textContent = message;
        }

    }


    // =====================================================
    // START
    // =====================================================

    loadDoctors();

});