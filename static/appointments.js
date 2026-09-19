document.addEventListener("DOMContentLoaded", function () {

    const container = document.getElementById("appointmentsContainer");
    const emptyState = document.getElementById("emptyState");
    const tabs = document.querySelectorAll(".tab");

    let currentStatus = "upcoming";

    // =========================================
    // LOAD APPOINTMENTS
    // =========================================

    async function loadAppointments(status = "upcoming") {

        currentStatus = status;

        container.innerHTML = `
            <div class="loading-card">
                <div class="loader"></div>
                <p>Loading your appointments...</p>
            </div>
        `;

        emptyState.style.display = "none";

        try {

            const response = await fetch("/api/appointments/my");

            if (!response.ok) {
                throw new Error("Unable to load appointments");
            }

            const data = await response.json();

            // Support both:
            // { appointments: [...] }
            // and direct [...]
            const appointments = Array.isArray(data)
                ? data
                : (data.appointments || []);

            const filteredAppointments = appointments.filter(function (appointment) {

                const appointmentStatus =
                    String(
                        appointment.status ||
                        appointment.appointment_status ||
                        "upcoming"
                    ).toLowerCase();

                if (status === "upcoming") {
                    return (
                        appointmentStatus === "upcoming" ||
                        appointmentStatus === "confirmed" ||
                        appointmentStatus === "scheduled" ||
                        appointmentStatus === "pending"
                    );
                }

                if (status === "completed") {
                    return appointmentStatus === "completed";
                }

                if (status === "cancelled") {
                    return (
                        appointmentStatus === "cancelled" ||
                        appointmentStatus === "canceled"
                    );
                }

                return true;
            });

            if (filteredAppointments.length === 0) {
                container.innerHTML = "";
                emptyState.style.display = "block";
                return;
            }

            renderAppointments(filteredAppointments);

        } catch (error) {

            console.error("Appointment loading error:", error);

            container.innerHTML = `
                <div class="loading-card">
                    <p>
                        Unable to load appointments right now.
                    </p>
                    <button
                        class="primary-btn"
                        id="retryAppointments">
                        Try Again
                    </button>
                </div>
            `;

            const retryButton =
                document.getElementById("retryAppointments");

            if (retryButton) {
                retryButton.addEventListener("click", function () {
                    loadAppointments(currentStatus);
                });
            }
        }
    }


    // =========================================
    // RENDER APPOINTMENTS
    // =========================================

    function renderAppointments(appointments) {

        container.innerHTML = "";

        appointments.forEach(function (appointment) {

            const doctorName =
                appointment.doctor_name ||
                appointment.full_name ||
                appointment.doctor ||
                "Doctor";

            const specialty =
                appointment.specialty ||
                appointment.department ||
                appointment.staff_role ||
                "Medical Specialist";

            const hospital =
                appointment.hospital ||
                "ArogyaCare";

            const date =
                appointment.appointment_date ||
                appointment.date ||
                "Date not available";

            const time =
                appointment.appointment_time ||
                appointment.time ||
                "Time not available";

            const mode =
                appointment.mode ||
                "In-person";

            const status =
                String(
                    appointment.status ||
                    "upcoming"
                ).toLowerCase();

            const doctorInitial =
                doctorName.charAt(0).toUpperCase();

            const card = document.createElement("div");

            card.className = "appointment-card";

            card.innerHTML = `
                <div class="doctor-info">

                    <div class="doctor-avatar">
                        ${doctorInitial}
                    </div>

                    <div>
                        <h3>${escapeHTML(doctorName)}</h3>

                        <p>
                            ${escapeHTML(specialty)}
                        </p>

                        <p>
                            ${escapeHTML(hospital)}
                        </p>
                    </div>

                </div>


                <div class="appointment-details">

                    <div class="detail-item">
                        Date
                        <strong>
                            ${escapeHTML(formatDate(date))}
                        </strong>
                    </div>

                    <div class="detail-item">
                        Time
                        <strong>
                            ${escapeHTML(formatTime(time))}
                        </strong>
                    </div>

                    <div class="detail-item">
                        Consultation
                        <strong>
                            ${escapeHTML(mode)}
                        </strong>
                    </div>

                    <span class="status ${getStatusClass(status)}">
                        ${escapeHTML(formatStatus(status))}
                    </span>

                </div>
            `;

            container.appendChild(card);
        });
    }


    // =========================================
    // STATUS TABS
    // =========================================

    tabs.forEach(function (tab) {

        tab.addEventListener("click", function () {

            tabs.forEach(function (item) {
                item.classList.remove("active");
            });

            tab.classList.add("active");

            const status =
                tab.dataset.status || "upcoming";

            loadAppointments(status);
        });
    });


    // =========================================
    // HELPERS
    // =========================================

    function formatDate(dateString) {

        if (!dateString) {
            return "Not available";
        }

        const date = new Date(dateString);

        if (isNaN(date.getTime())) {
            return dateString;
        }

        return date.toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric"
        });
    }


    function formatTime(timeString) {

        if (!timeString) {
            return "Not available";
        }

        // Handles HH:MM:SS
        const parts = String(timeString).split(":");

        if (parts.length < 2) {
            return timeString;
        }

        let hour = parseInt(parts[0], 10);
        const minute = parts[1];

        if (isNaN(hour)) {
            return timeString;
        }

        const suffix = hour >= 12 ? "PM" : "AM";

        hour = hour % 12;

        if (hour === 0) {
            hour = 12;
        }

        return `${hour}:${minute} ${suffix}`;
    }


    function formatStatus(status) {

        const value = String(status).toLowerCase();

        if (value === "confirmed") {
            return "Confirmed";
        }

        if (value === "scheduled") {
            return "Scheduled";
        }

        if (value === "pending") {
            return "Pending";
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

        return "Upcoming";
    }


    function getStatusClass(status) {

        const value = String(status).toLowerCase();

        if (value === "completed") {
            return "completed";
        }

        if (
            value === "cancelled" ||
            value === "canceled"
        ) {
            return "cancelled";
        }

        return "upcoming";
    }


    function escapeHTML(value) {

        const div = document.createElement("div");

        div.textContent = value == null
            ? ""
            : String(value);

        return div.innerHTML;
    }


    // =========================================
    // INITIAL LOAD
    // =========================================

    loadAppointments("upcoming");

});