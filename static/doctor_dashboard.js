
document.addEventListener("DOMContentLoaded", function () {

    // =========================================================
    // ELEMENTS
    // =========================================================

    var sidebar = document.getElementById("sidebar");
    var sidebarScrim = document.getElementById("sidebarScrim");
    var menuToggle = document.getElementById("menuToggle");

    var searchForm = document.getElementById("searchForm");
    var searchInput = document.getElementById("patientSearchInput");
    var searchBtn = document.getElementById("searchBtn");

    var resultsCount = document.getElementById("resultsCount");
    var patientList = document.getElementById("patientList");
    var emptyState = document.getElementById("emptyState");
    var noResultsState = document.getElementById("noResultsState");
    var loadingState = document.getElementById("loadingState");

    var patientCardTemplate =
        document.getElementById("patientCardTemplate");

    var casePanel = document.getElementById("casePanel");
    var casePlaceholder = document.getElementById("casePlaceholder");
    var backToPatients = document.getElementById("backToPatients");

    var patientIdentity = document.getElementById("patientIdentity");
    var historyGrid = document.getElementById("historyGrid");
    var redFlagCard = document.getElementById("redFlagCard");
    var conversationTimeline =
        document.getElementById("conversationTimeline");

    var toggleConversation =
        document.getElementById("toggleConversation");

    var verifyCaseBtn =
        document.getElementById("verifyCaseBtn");

    var reviewCaseBtn =
        document.getElementById("reviewCaseBtn");

    var logoutBtn =
        document.getElementById("logoutBtn");

    var currentPatientId = null;


    // =========================================================
    // BASIC CHECK
    // =========================================================

    console.log("ArogyaCare Doctor Dashboard JS loaded.");

    console.log(
        "Search form:",
        searchForm
    );

    console.log(
        "Search input:",
        searchInput
    );

    console.log(
        "Patient list:",
        patientList
    );


    // =========================================================
    // SIDEBAR
    // =========================================================

    if (menuToggle && sidebar) {

        menuToggle.addEventListener(
            "click",
            function () {

                sidebar.classList.toggle("open");

                if (sidebarScrim) {
                    sidebarScrim.classList.toggle("show");
                }
            }
        );
    }

    if (sidebarScrim) {

        sidebarScrim.addEventListener(
            "click",
            function () {

                if (sidebar) {
                    sidebar.classList.remove("open");
                }

                sidebarScrim.classList.remove("show");
            }
        );
    }


    // =========================================================
    // HIDDEN / VISIBLE HELPERS
    // =========================================================

    function show(element) {

        if (!element) {
            return;
        }

        element.hidden = false;
        element.style.display = "";
    }


    function hide(element) {

        if (!element) {
            return;
        }

        element.hidden = true;
        element.style.display = "none";
    }


    // =========================================================
    // HTML ESCAPE
    // =========================================================

    function escapeHtml(value) {

        if (
            value === null ||
            value === undefined
        ) {
            return "";
        }

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    // =========================================================
    // SEARCH RESULT COUNT
    // =========================================================

    function updateResultCount(count) {

        if (!resultsCount) {
            return;
        }

        if (count === 0) {
            resultsCount.textContent =
                "No patients found.";
            return;
        }

        resultsCount.textContent =
            String(count) +
            (
                count === 1
                    ? " patient found."
                    : " patients found."
            );
    }


    // =========================================================
    // CLEAR RESULTS
    // =========================================================

    function clearResults() {

        if (patientList) {
            patientList.innerHTML = "";
        }
    }


    // =========================================================
    // SEARCH PATIENTS
    // =========================================================

    function searchPatients(event) {

        if (event) {
            event.preventDefault();
        }

        if (!searchInput) {

            console.error(
                "ERROR: patientSearchInput not found."
            );

            return;
        }

        var query =
            String(searchInput.value || "").trim();

        console.log(
            "Searching patient:",
            query
        );


        // Empty search
        if (!query) {

            clearResults();

            updateResultCount(0);

            hide(noResultsState);
            hide(loadingState);

            show(emptyState);

            return;
        }


        // Loading state
        clearResults();

        hide(emptyState);
        hide(noResultsState);
        show(loadingState);


        var url =
            "/api/doctor/patients/search?q=" +
            encodeURIComponent(query);


        console.log(
            "SEARCH URL:",
            url
        );


        fetch(
            url,
            {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            }
        )
        .then(
            function (response) {

                console.log(
                    "SEARCH STATUS:",
                    response.status
                );

                if (!response.ok) {

                    throw new Error(
                        "Search failed. HTTP " +
                        response.status
                    );
                }

                return response.json();
            }
        )
        .then(
            function (data) {

                console.log(
                    "SEARCH RESPONSE:",
                    data
                );

                hide(loadingState);

                clearResults();


                // =================================================
                // HANDLE API RESPONSE
                // =================================================

                var patients = [];


                if (Array.isArray(data)) {

                    patients = data;

                } else if (
                    data &&
                    Array.isArray(data.patients)
                ) {

                    patients = data.patients;

                } else if (
                    data &&
                    Array.isArray(data.results)
                ) {

                    patients = data.results;

                } else if (
                    data &&
                    data.patient
                ) {

                    patients = [
                        data.patient
                    ];
                }


                console.log(
                    "PATIENTS FOUND:",
                    patients.length
                );


                updateResultCount(
                    patients.length
                );


                if (patients.length === 0) {

                    hide(emptyState);
                    show(noResultsState);

                    return;
                }


                hide(emptyState);
                hide(noResultsState);


                for (
                    var i = 0;
                    i < patients.length;
                    i++
                ) {

                    createPatientCard(
                        patients[i]
                    );
                }
            }
        )
        .catch(
            function (error) {

                console.error(
                    "PATIENT SEARCH ERROR:",
                    error
                );

                hide(loadingState);
                clearResults();

                updateResultCount(0);

                hide(emptyState);
                show(noResultsState);

                if (noResultsState) {

                    noResultsState.innerHTML =
                        '<p class="empty-title">' +
                        'Search error' +
                        '</p>' +

                        '<p class="empty-sub">' +
                        escapeHtml(
                            error.message
                        ) +
                        '</p>';
                }
            }
        );
    }


    // =========================================================
    // SEARCH FORM
    // =========================================================

    if (searchForm) {

        searchForm.addEventListener(
            "submit",
            searchPatients
        );

    } else {

        console.error(
            "ERROR: searchForm not found."
        );
    }


    // =========================================================
    // SEARCH BUTTON FALLBACK
    // =========================================================

    if (searchBtn) {

        searchBtn.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                searchPatients(event);
            }
        );
    }


    // =========================================================
    // ENTER KEY FALLBACK
    // =========================================================

    if (searchInput) {

        searchInput.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {

                    event.preventDefault();

                    searchPatients(event);
                }
            }
        );
    }


    // =========================================================
    // CREATE PATIENT CARD
    // =========================================================

    function createPatientCard(patient) {

        if (!patientList) {

            console.error(
                "ERROR: patientList not found."
            );

            return;
        }


        var patientId =
            patient.id ||
            patient.patient_id ||
            patient.patientId;


        var name =
            patient.full_name ||
            patient.fullName ||
            patient.name ||
            "Unknown Patient";


        var age =
            patient.age !== null &&
            patient.age !== undefined
                ? patient.age
                : "N/A";


        var gender =
            patient.gender ||
            "N/A";


        var phone =
            patient.phone ||
            patient.mobile ||
            "Not available";


        var abha =
            patient.abha_id ||
            patient.abhaId ||
            "Not available";


        var status =
            patient.status ||
            "Intake available";


        var lastVisit =
            patient.last_visit ||
            patient.lastVisit ||
            patient.last_case_date ||
            "";


        // =====================================================
        // USE EXISTING TEMPLATE
        // =====================================================

        var card;


        if (patientCardTemplate) {

            var clone =
                patientCardTemplate.content.cloneNode(
                    true
                );

            card =
                clone.querySelector(
                    ".patient-card"
                );

            if (!card) {
                return;
            }


            var avatar =
                card.querySelector(
                    ".avatar"
                );

            var patientName =
                card.querySelector(
                    ".patient-name"
                );

            var patientDemo =
                card.querySelector(
                    ".patient-demo"
                );

            var patientMobile =
                card.querySelector(
                    ".patient-mobile"
                );

            var patientAbha =
                card.querySelector(
                    ".patient-abha"
                );

            var statusPill =
                card.querySelector(
                    ".status-pill"
                );

            var lastVisitElement =
                card.querySelector(
                    ".last-visit"
                );

            var viewCaseBtn =
                card.querySelector(
                    ".view-case-btn"
                );


            if (avatar) {

                avatar.textContent =
                    String(name)
                        .charAt(0)
                        .toUpperCase();
            }


            if (patientName) {

                patientName.textContent =
                    name;
            }


            if (patientDemo) {

                patientDemo.textContent =
                    String(age) +
                    " years • " +
                    String(gender);
            }


            if (patientMobile) {

                patientMobile.textContent =
                    "Mobile: " +
                    String(phone);
            }


            if (patientAbha) {

                patientAbha.textContent =
                    "ABHA: " +
                    String(abha);
            }


            if (statusPill) {

                statusPill.textContent =
                    status;
            }


            if (lastVisitElement) {

                if (lastVisit) {

                    lastVisitElement.textContent =
                        "Last case: " +
                        String(lastVisit);

                } else {

                    lastVisitElement.textContent =
                        "Case available";
                }
            }


            if (viewCaseBtn) {

                viewCaseBtn.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();
                        event.stopPropagation();

                        if (patientId) {
                            loadPatientCase(
                                patientId
                            );
                        }
                    }
                );
            }


            card.addEventListener(
                "click",
                function () {

                    if (patientId) {
                        loadPatientCase(
                            patientId
                        );
                    }
                }
            );


            card.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key === "Enter" ||
                        event.key === " "
                    ) {

                        event.preventDefault();

                        if (patientId) {
                            loadPatientCase(
                                patientId
                            );
                        }
                    }
                }
            );


            patientList.appendChild(
                clone
            );

            return;
        }


        // =====================================================
        // FALLBACK CARD
        // =====================================================

        var fallbackCard =
            document.createElement("li");

        fallbackCard.className =
            "patient-card";

        fallbackCard.innerHTML =
            '<div class="patient-card-id">' +

                '<div class="avatar avatar-md">' +
                    escapeHtml(
                        String(name)
                            .charAt(0)
                            .toUpperCase()
                    ) +
                '</div>' +

                '<div class="patient-card-name">' +

                    '<span class="patient-name">' +
                        escapeHtml(name) +
                    '</span>' +

                    '<span class="patient-demo">' +
                        escapeHtml(
                            String(age) +
                            " years • " +
                            String(gender)
                        ) +
                    '</span>' +

                '</div>' +

            '</div>' +

            '<div class="patient-card-meta">' +

                '<span class="patient-mobile">' +
                    escapeHtml(phone) +
                '</span>' +

                '<span class="patient-abha">' +
                    escapeHtml(abha) +
                '</span>' +

            '</div>' +

            '<div class="patient-card-status">' +

                '<span class="status-pill">' +
                    escapeHtml(status) +
                '</span>' +

                '<span class="last-visit">' +
                    escapeHtml(lastVisit) +
                '</span>' +

            '</div>' +

            '<button type="button" class="btn btn-outline btn-sm view-case-btn">' +
                'View case' +
            '</button>';


        var fallbackButton =
            fallbackCard.querySelector(
                ".view-case-btn"
            );


        if (fallbackButton) {

            fallbackButton.addEventListener(
                "click",
                function (event) {

                    event.stopPropagation();

                    if (patientId) {
                        loadPatientCase(
                            patientId
                        );
                    }
                }
            );
        }


        fallbackCard.addEventListener(
            "click",
            function () {

                if (patientId) {
                    loadPatientCase(
                        patientId
                    );
                }
            }
        );


        patientList.appendChild(
            fallbackCard
        );
    }


    // =========================================================
    // LOAD PATIENT CASE
    // =========================================================

    function loadPatientCase(patientId) {

        if (!patientId) {

            console.error(
                "Patient ID missing."
            );

            return;
        }


        currentPatientId =
            patientId;


        console.log(
            "Loading patient:",
            patientId
        );


        // Show case panel
        if (casePanel) {
            casePanel.hidden = false;
            casePanel.style.display = "";
        }


        if (casePlaceholder) {
            hide(casePlaceholder);
        }


        if (patientList) {
            patientList.style.display = "none";
        }


        if (patientIdentity) {

            patientIdentity.innerHTML =
                '<p>Loading patient details...</p>';
        }


        fetch(
            "/api/doctor/patient/" +
            encodeURIComponent(patientId),
            {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            }
        )
        .then(
            function (response) {

                return response.text()
                    .then(
                        function (text) {

                            var data;

                            try {

                                data =
                                    JSON.parse(
                                        text
                                    );

                            } catch (error) {

                                throw new Error(
                                    "Server returned invalid JSON."
                                );
                            }


                            if (!response.ok) {

                                throw new Error(
                                    data.error ||
                                    "Unable to load patient case."
                                );
                            }


                            return data;
                        }
                    );
            }
        )
        .then(
            function (data) {

                console.log(
                    "PATIENT CASE:",
                    data
                );

                renderPatientCase(
                    data
                );
            }
        )
        .catch(
            function (error) {

                console.error(
                    "PATIENT CASE ERROR:",
                    error
                );

                if (patientIdentity) {

                    patientIdentity.innerHTML =
                        '<div class="error-message">' +

                            '<strong>' +
                                'Unable to load patient details.' +
                            '</strong>' +

                            '<br><br>' +

                            escapeHtml(
                                error.message
                            ) +

                        '</div>';
                }
            }
        );
    }


    // =========================================================
    // RENDER CASE
    // =========================================================

    function renderPatientCase(data) {

        var patient =
            data.patient ||
            data;


        var history =
            data.history ||
            data.latest_history ||
            {};


        var conversations =
            data.conversations ||
            [];


        renderPatientIdentity(
            patient
        );


        renderHistory(
            history
        );


        renderRedFlag(
            data
        );


        renderConversation(
            conversations
        );


        renderDocuments(
            data.documents ||
            []
        );
    }


    // =========================================================
    // PATIENT IDENTITY
    // =========================================================

    function renderPatientIdentity(patient) {

        if (!patientIdentity) {
            return;
        }


        var name =
            patient.full_name ||
            patient.fullName ||
            patient.name ||
            "Unknown Patient";


        var age =
            patient.age !== undefined &&
            patient.age !== null
                ? patient.age
                : "N/A";


        var gender =
            patient.gender ||
            "N/A";


        var phone =
            patient.phone ||
            "Not available";


        var abha =
            patient.abha_id ||
            patient.abhaId ||
            "Not available";


        patientIdentity.innerHTML =

            '<div class="patient-detail-name">' +
                escapeHtml(name) +
            '</div>' +

            '<div class="patient-detail-grid">' +

                '<div>' +
                    '<span>Age</span>' +
                    '<strong>' +
                        escapeHtml(age) +
                    '</strong>' +
                '</div>' +

                '<div>' +
                    '<span>Gender</span>' +
                    '<strong>' +
                        escapeHtml(gender) +
                    '</strong>' +
                '</div>' +

                '<div>' +
                    '<span>Phone</span>' +
                    '<strong>' +
                        escapeHtml(phone) +
                    '</strong>' +
                '</div>' +

                '<div>' +
                    '<span>ABHA ID</span>' +
                    '<strong>' +
                        escapeHtml(abha) +
                    '</strong>' +
                '</div>' +

            '</div>';
    }


    // =========================================================
    // HISTORY
    // =========================================================

    function renderHistory(history) {

        if (!historyGrid) {
            return;
        }


        var complaint =
            history.main_problem ||
            history.mainProblem ||
            "Not clearly stated.";


        var duration =
            history.duration ||
            "Not clearly stated.";


        var symptoms =
            history.symptoms ||
            "Not clearly stated.";


        var medicalHistory =
            history.medical_history ||
            history.medicalHistory ||
            "Not clearly stated.";


        var medicines =
            history.medicines ||
            "Not clearly stated.";


        var allergies =
            history.allergies ||
            "Not clearly stated.";


        var summary =
            history.summary ||
            "Not clearly stated.";


        historyGrid.innerHTML =

            historyItem(
                "Current Complaint",
                complaint
            ) +

            historyItem(
                "Duration",
                duration
            ) +

            historyItem(
                "Current Symptoms",
                symptoms
            ) +

            historyItem(
                "Past Medical History",
                medicalHistory
            ) +

            historyItem(
                "Current Medications",
                medicines
            ) +

            historyItem(
                "Allergies",
                allergies
            ) +

            historyItem(
                "Summary",
                summary
            );
    }


    function historyItem(title, value) {

        return (

            '<div class="history-item">' +

                '<div class="history-label">' +
                    escapeHtml(title) +
                '</div>' +

                '<div class="history-value">' +
                    escapeHtml(value) +
                '</div>' +

            '</div>'
        );
    }


    // =========================================================
    // RED FLAGS
    // =========================================================

    function renderRedFlag(data) {

        if (!redFlagCard) {
            return;
        }


        var detected =
            data.red_flag_detected === true ||
            data.red_flag === true;


        var reason =
            data.red_flag_reason ||
            data.redFlagReason ||
            "";


        if (!detected) {

            redFlagCard.innerHTML =

                '<div class="red-flag-safe">' +

                    '<strong>' +
                        'No Red Flag Detected' +
                    '</strong>' +

                    '<p>' +
                        'No potential emergency warning signal was detected.' +
                    '</p>' +

                '</div>';

            return;
        }


        if (!reason) {

            reason =
                "A potentially serious symptom was detected.";
        }


        redFlagCard.innerHTML =

            '<div class="red-flag-danger">' +

                '<strong>' +
                    'RED FLAG DETECTED' +
                '</strong>' +

                '<p>' +

                    '<strong>Reason:</strong> ' +

                    escapeHtml(reason) +

                '</p>' +

                '<p>' +

                    '<strong>Action:</strong> ' +

                    'Please seek urgent medical attention. ' +

                    'This is an emergency warning, not a diagnosis.' +

                '</p>' +

            '</div>';
    }


    // =========================================================
    // CONVERSATION
    // =========================================================

    function renderConversation(conversations) {

        if (!conversationTimeline) {
            return;
        }


        conversationTimeline.innerHTML = "";


        if (
            !Array.isArray(conversations) ||
            conversations.length === 0
        ) {

            conversationTimeline.innerHTML =
                '<li>No conversation available.</li>';

            return;
        }


        for (
            var i = 0;
            i < conversations.length;
            i++
        ) {

            var item =
                conversations[i];


            var sender =
                String(
                    item.sender ||
                    item.role ||
                    ""
                ).toLowerCase();


            var message =
                item.message ||
                item.content ||
                "";


            var li =
                document.createElement("li");


            li.className =
                sender === "patient"
                    ? "conversation-item patient"
                    : "conversation-item ai";


            li.innerHTML =

                '<div class="conversation-sender">' +

                    (
                        sender === "patient"
                            ? "Patient"
                            : "AI Assistant"
                    ) +

                '</div>' +

                '<div class="conversation-message">' +

                    escapeHtml(message) +

                '</div>';


            conversationTimeline.appendChild(
                li
            );
        }
    }


    // =========================================================
    // DOCUMENTS
    // =========================================================

    function renderDocuments(documents) {

        var docsEmpty =
            document.querySelector(
                ".docs-empty"
            );


        if (!docsEmpty) {
            return;
        }


        if (
            !Array.isArray(documents) ||
            documents.length === 0
        ) {

            docsEmpty.innerHTML =
                '<p>No documents attached to this case yet.</p>';

            return;
        }


        var html =
            '<div class="doctor-documents-list">';


        for (
            var i = 0;
            i < documents.length;
            i++
        ) {

            var doc =
                documents[i];


            var id =
                doc.id ||
                doc.document_id;


            var filename =
                doc.original_filename ||
                doc.filename ||
                "Document";


            html +=

                '<div class="doctor-document-row">' +

                    '<span>' +
                        escapeHtml(filename) +
                    '</span>' +

                    '<a href="/doctor/document/' +
                        encodeURIComponent(id) +
                        '/view" target="_blank">' +
                        'View' +
                    '</a>' +

                    '<a href="/doctor/document/' +
                        encodeURIComponent(id) +
                        '/download">' +
                        'Download' +
                    '</a>' +

                '</div>';
        }


        html += "</div>";


        docsEmpty.innerHTML =
            html;
    }


    // =========================================================
    // BACK TO PATIENTS
    // =========================================================

    if (backToPatients) {

        backToPatients.addEventListener(
            "click",
            function (event) {

                event.preventDefault();


                currentPatientId = null;


                if (casePanel) {
                    hide(casePanel);
                }


                if (patientList) {
                    patientList.style.display = "";
                }


                if (casePlaceholder) {
                    show(casePlaceholder);
                }


                if (searchInput) {
                    searchInput.focus();
                }
            }
        );
    }


    // =========================================================
    // CASE TABS
    // =========================================================

    var caseTabs =
        document.querySelectorAll(
            ".case-tab"
        );


    var casePanels =
        document.querySelectorAll(
            ".case-tab-panel"
        );


    for (
        var t = 0;
        t < caseTabs.length;
        t++
    ) {

        caseTabs[t].addEventListener(
            "click",
            function () {

                var selectedTab =
                    this.getAttribute(
                        "data-tab"
                    );


                for (
                    var a = 0;
                    a < caseTabs.length;
                    a++
                ) {

                    caseTabs[a].classList.remove(
                        "active"
                    );

                    caseTabs[a].setAttribute(
                        "aria-selected",
                        "false"
                    );
                }


                for (
                    var b = 0;
                    b < casePanels.length;
                    b++
                ) {

                    casePanels[b].classList.remove(
                        "active"
                    );
                }


                this.classList.add(
                    "active"
                );

                this.setAttribute(
                    "aria-selected",
                    "true"
                );


                for (
                    var c = 0;
                    c < casePanels.length;
                    c++
                ) {

                    if (
                        casePanels[c].getAttribute(
                            "data-panel"
                        ) === selectedTab
                    ) {

                        casePanels[c].classList.add(
                            "active"
                        );
                    }
                }
            }
        );
    }


    // =========================================================
    // CONVERSATION TOGGLE
    // =========================================================

    if (toggleConversation) {

        toggleConversation.addEventListener(
            "click",
            function () {

                if (!conversationTimeline) {
                    return;
                }


                conversationTimeline.classList.toggle(
                    "expanded"
                );


                if (
                    conversationTimeline.classList.contains(
                        "expanded"
                    )
                ) {

                    toggleConversation.textContent =
                        "Collapse";

                } else {

                    toggleConversation.textContent =
                        "Expand";
                }
            }
        );
    }


    // =========================================================
    // VERIFY CASE
    // =========================================================

    if (verifyCaseBtn) {

        verifyCaseBtn.addEventListener(
            "click",
            function () {

                if (!currentPatientId) {
                    return;
                }


                fetch(
                    "/api/doctor/patient/" +
                    encodeURIComponent(
                        currentPatientId
                    ) +
                    "/verify",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json",
                            "Accept":
                                "application/json"
                        },
                        body: JSON.stringify({})
                    }
                )
                .then(
                    function (response) {
                        return response.json();
                    }
                )
                .then(
                    function (data) {

                        if (
                            data &&
                            data.success
                        ) {

                            verifyCaseBtn.textContent =
                                "Verified";

                            verifyCaseBtn.disabled =
                                true;
                        }
                    }
                )
                .catch(
                    function (error) {

                        console.error(
                            "VERIFY ERROR:",
                            error
                        );
                    }
                );
            }
        );
    }


    // =========================================================
    // REVIEW CASE
    // =========================================================

    if (reviewCaseBtn) {

        reviewCaseBtn.addEventListener(
            "click",
            function () {

                if (!currentPatientId) {
                    return;
                }


                window.location.href =
                    "/physician-review?patient_id=" +
                    encodeURIComponent(
                        currentPatientId
                    );
            }
        );
    }


    // =========================================================
    // LOGOUT
    // =========================================================

    if (logoutBtn) {

        logoutBtn.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                window.location.href =
                    "/logout";
            }
        );
    }


    // =========================================================
    // INITIAL STATE
    // =========================================================

    hide(casePanel);
    hide(noResultsState);
    hide(loadingState);

    show(emptyState);

});
