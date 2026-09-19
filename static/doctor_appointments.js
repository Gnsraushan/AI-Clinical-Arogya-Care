document.addEventListener("DOMContentLoaded", function () {

    const container = document.getElementById(
        "doctorAppointmentsContainer"
    );

    const filterButtons = document.querySelectorAll(
        ".filter-btn"
    );

    let allAppointments = [];
    let currentFilter = "all";


    // =========================================
    // LOAD APPOINTMENTS
    // =========================================

    async function loadAppointments() {

        container.innerHTML = `
            <div class="loading-box">
                <div class="loader"></div>
                <p>Loading appointments...</p>
            </div>
        `;

        try {

            const response = await fetch(
                "/api/doctor/appointments"
            );

            if (!response.ok) {
                throw new Error(
                    "Failed to load appointments"
                );
            }

            const data = await response.json();

            allAppointments = Array.isArray(data)
                ? data
                : (data.appointments || []);

            updateSummary(allAppointments);

            renderAppointments();

        } catch (error) {

            console.error(
                "Doctor appointments error:",
                error
            );

            container.innerHTML = `
                <div class="error-box">
                    <p>
                        Unable to load appointments.
                    </p>

                    <button
                        class="action-btn confirm"
                        id="retryDoctorAppointments">
                        Try Again
                    </button>
                </div>
            `;

            const retry =
                document.getElementById(
                    "retryDoctorAppointments"
                );

            if (retry) {
                retry.addEventListener(
                    "click",
                    loadAppointments
                );
            }
        }
    }


    // =========================================
    // SUMMARY
    // =========================================

    function updateSummary(appointments) {

        const todayCount =
            document.getElementById("todayCount");

        const pendingCount =
            document.getElementById("pendingCount");

        const completedCount =
            document.getElementById("completedCount");

        const today = new Date()
            .toISOString()
            .split("T")[0];

        let todayTotal = 0;
        let pendingTotal = 0;
        let completedTotal = 0;

        appointments.forEach(function (appointment) {

            const status = getStatus(appointment);

            const date =
                appointment.appointment_date ||
                appointment.date ||
                "";

            if (date === today) {
                todayTotal++;
            }

            if (status === "pending") {
                pendingTotal++;
            }

            if (status === "completed") {
                completedTotal++;
            }
        });

        if (todayCount) {
            todayCount.textContent = todayTotal;
        }

        if (pendingCount) {
            pendingCount.textContent = pendingTotal;
        }

        if (completedCount) {
            completedCount.textContent = completedTotal;
        }
    }


    // =========================================
    // RENDER
    // =========================================

    function renderAppointments() {

        let appointments =
            allAppointments.filter(function (appointment) {

                if (currentFilter === "all") {
                    return true;
                }

                return (
                    getStatus(appointment) ===
                    currentFilter
                );
            });


        if (appointments.length === 0) {

            container.innerHTML = `
                <div class="empty-box">
                    <p>
                        No appointments found for
                        this category.
                    </p>
                </div>
            `;

            return;
        }


        container.innerHTML = "";


        appointments.forEach(function (appointment) {

            const patientName =
                appointment.patient_name ||
                appointment.full_name ||
                appointment.patient ||
                "Patient";

            const patientId =
                appointment.patient_id ||
                appointment.abha_id ||
                "N/A";

            const date =
                appointment.appointment_date ||
                appointment.date ||
                "Not available";

            const time =
                appointment.appointment_time ||
                appointment.time ||
                "Not available";

            const mode =
                appointment.mode ||
                "In-person";

            const notes =
                appointment.notes ||
                "No notes provided";

            const status =
                getStatus(appointment);


            const patientInitial =
                patientName
                    .charAt(0)
                    .toUpperCase();


            const card =
                document.createElement("div");

            card.className =
                "doctor-appointment-card";


            card.innerHTML = `

                <div class="patient-info">

                    <div class="patient-avatar">
                        ${patientInitial}
                    </div>

                    <div>

                        <h3>
                            ${escapeHTML(patientName)}
                        </h3>

                        <p>
                            Patient ID:
                            ${escapeHTML(patientId)}
                        </p>

                    </div>

                </div>


                <div class="appointment-info">

                    <div class="info-item">
                        Date
                        <strong>
                            ${escapeHTML(
                                formatDate(date)
                            )}
                        </strong>
                    </div>

                    <div class="info-item">
                        Time
                        <strong>
                            ${escapeHTML(
                                formatTime(time)
                            )}
                        </strong>
                    </div>

                    <div class="info-item">
                        Consultation
                        <strong>
                            ${escapeHTML(mode)}
                        </strong>
                    </div>

                    <div class="info-item">
                        Reason
                        <strong>
                            ${escapeHTML(notes)}
                        </strong>
                    </div>

                </div>


                <div class="appointment-actions">

                    <span class="status-badge ${getStatusClass(status)}">
                        ${escapeHTML(
                            formatStatus(status)
                        )}
                    </span>

                    ${getActionButtons(
                        appointment,
                        status
                    )}

                </div>
            `;


            container.appendChild(card);
        });
    }


    // =========================================
    // ACTION BUTTONS
    // =========================================

    function getActionButtons(
        appointment,
        status
    ) {

        const appointmentId =
            appointment.id ||
            appointment.appointment_id;


        if (!appointmentId) {
            return "";
        }


        if (status === "pending") {

            return `
                <button
                    class="action-btn confirm"
                    data-action="confirmed"
                    data-id="${appointmentId}">
                    Confirm
                </button>

                <button
                    class="action-btn"
                    data-action="cancelled"
                    data-id="${appointmentId}">
                    Cancel
                </button>
            `;
        }


        if (status === "confirmed") {

            return `
                <button
                    class="action-btn confirm"
                    data-action="completed"
                    data-id="${appointmentId}">
                    Complete
                </button>

                <button
                    class="action-btn"
                    data-action="cancelled"
                    data-id="${appointmentId}">
                    Cancel
                </button>
            `;
        }


        return "";
    }


    // =========================================
    // UPDATE STATUS
    // =========================================

    async function updateAppointmentStatus(
        appointmentId,
        status
    ) {

        try {

            const response = await fetch(
                `/api/doctor/appointments/${appointmentId}/status`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        status: status
                    })
                }
            );


            if (!response.ok) {
                throw new Error(
                    "Status update failed"
                );
            }


            const data =
                await response.json();


            if (data.success === false) {
                throw new Error(
                    data.message ||
                    "Unable to update appointment"
                );
            }


            await loadAppointments();


        } catch (error) {

            console.error(
                "Status update error:",
                error
            );

            alert(
                "Unable to update appointment status."
            );
        }
    }


    // =========================================
    // BUTTON CLICK
    // =========================================

    container.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    "[data-action]"
                );

            if (!button) {
                return;
            }


            const appointmentId =
                button.dataset.id;

            const status =
                button.dataset.action;


            if (!appointmentId) {
                return;
            }


            updateAppointmentStatus(
                appointmentId,
                status
            );
        }
    );


    // =========================================
    // FILTERS
    // =========================================

    filterButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    filterButtons.forEach(
                        function (item) {
                            item.classList.remove(
                                "active"
                            );
                        }
                    );


                    button.classList.add(
                        "active"
                    );


                    currentFilter =
                        button.dataset.status ||
                        "all";


                    renderAppointments();
                }
            );
        }
    );


    // =========================================
    // HELPERS
    // =========================================

    function getStatus(appointment) {

        return String(
            appointment.status ||
            "pending"
        ).toLowerCase();
    }


    function formatStatus(status) {

        const value =
            String(status).toLowerCase();


        if (value === "confirmed") {
            return "Confirmed";
        }

        if (value === "completed") {
            return "Completed";
        }

        if (
            value === "cancelled" ||
            value === "canceled"
        ) {
            return "Cancelled";
        }

        return "Pending";
    }


    function getStatusClass(status) {

        const value =
            String(status).toLowerCase();


        if (value === "confirmed") {
            return "confirmed";
        }

        if (value === "completed") {
            return "completed";
        }

        if (
            value === "cancelled" ||
            value === "canceled"
        ) {
            return "cancelled";
        }

        return "pending";
    }


    function formatDate(dateString) {

        if (!dateString) {
            return "Not available";
        }


        const date =
            new Date(dateString);


        if (isNaN(date.getTime())) {
            return dateString;
        }


        return date.toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );
    }


    function formatTime(timeString) {

        if (!timeString) {
            return "Not available";
        }


        const parts =
            String(timeString).split(":");


        if (parts.length < 2) {
            return timeString;
        }


        let hour =
            parseInt(parts[0], 10);

        const minute =
            parts[1];


        if (isNaN(hour)) {
            return timeString;
        }


        const suffix =
            hour >= 12 ? "PM" : "AM";


        hour =
            hour % 12;


        if (hour === 0) {
            hour = 12;
        }


        return `${hour}:${minute} ${suffix}`;
    }


    function escapeHTML(value) {

        const div =
            document.createElement("div");

        div.textContent =
            value == null
                ? ""
                : String(value);

        return div.innerHTML;
    }


    // =========================================
    // INITIAL LOAD
    // =========================================

    loadAppointments();

});