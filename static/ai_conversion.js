document.addEventListener("DOMContentLoaded", function () {

    // ================================
    // MOBILE MENU
    // ================================
    const menuButton = document.getElementById("mobileMenuToggle");
    const mobileDrawer = document.getElementById("mobileDrawer");

    if (menuButton && mobileDrawer) {
        menuButton.addEventListener("click", function () {
            const isOpen =
                menuButton.getAttribute("aria-expanded") === "true";

            if (isOpen) {
                menuButton.setAttribute("aria-expanded", "false");
                mobileDrawer.setAttribute("aria-hidden", "true");
                mobileDrawer.classList.remove("open");
            } else {
                menuButton.setAttribute("aria-expanded", "true");
                mobileDrawer.setAttribute("aria-hidden", "false");
                mobileDrawer.classList.add("open");
            }
        });
    }


    // ================================
    // AUTO SCROLL CONVERSATION
    // ================================
    const conversationStream =
        document.getElementById("conversationStream");

    if (conversationStream) {
        conversationStream.scrollTop =
            conversationStream.scrollHeight;
    }


    // ================================
    // GENERATE REPORT
    // ================================
    const generateButton =
        document.getElementById("generateHistoryBtn");

    if (generateButton) {

        generateButton.addEventListener("click", async function () {

            if (generateButton.disabled) {
                return;
            }

            generateButton.disabled = true;

            const oldText = generateButton.textContent;

            generateButton.textContent = "Generating...";

            try {

                const generateUrl =
                    generateButton.getAttribute("data-generate-url");

                if (!generateUrl) {
                    throw new Error(
                        "Generate Report URL is missing."
                    );
                }

                const response = await fetch(
                    generateUrl,
                    {
                        method: "POST",
                        headers: {
                            "Accept": "application/json"
                        },
                        credentials: "same-origin"
                    }
                );

                let data;

                try {
                    data = await response.json();
                } catch (jsonError) {
                    throw new Error(
                        "Server ne valid response nahi diya. Status: " +
                        response.status
                    );
                }

                if (!response.ok || !data.success) {
                    throw new Error(
                        data.message ||
                        "Report generate nahi ho payi."
                    );
                }


                // ================================
                // GENERATED HISTORY
                // ================================
                const history = data.history || {};


                // ================================
                // SUMMARY
                // ================================
                const summaryElement =
                    document.getElementById("summaryText");

                if (summaryElement) {
                    summaryElement.textContent =
                        history.summary || "Not reported";
                }


                // ================================
                // OTHER FIELDS
                // ================================
                updateElement(
                    "mainProblem",
                    history.main_problem
                );

                updateElement(
                    "duration",
                    history.duration
                );

                updateElement(
                    "symptoms",
                    history.symptoms
                );

                updateElement(
                    "medicalHistory",
                    history.medical_history
                );

                updateElement(
                    "medicines",
                    history.medicines
                );

                updateElement(
                    "allergies",
                    history.allergies
                );


                // ================================
                // SUCCESS
                // ================================
                generateButton.textContent =
                    "Report Generated ✓";


                // ================================
                // SCROLL TO SUMMARY
                // ================================
                const summarySection =
                    document.getElementById("summary-heading");

                if (summarySection) {
                    summarySection.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });
                }


                // ================================
                // RESET BUTTON
                // ================================
                setTimeout(function () {

                    generateButton.disabled = false;

                    generateButton.textContent =
                        "Generate Report";

                }, 2500);

            } catch (error) {

                console.error(
                    "Generate Report Error:",
                    error
                );

                alert(
                    error.message ||
                    "Something went wrong while generating the report."
                );

                generateButton.disabled = false;

                generateButton.textContent =
                    oldText;
            }

        });
    }


    // ================================
    // COPY SUMMARY
    // ================================
    const copyButton =
        document.getElementById("copySummaryBtn");

    if (copyButton) {

        copyButton.addEventListener("click", async function () {

            const summaryElement =
                document.getElementById("summaryText");

            if (!summaryElement) {
                return;
            }

            const text =
                summaryElement.textContent.trim();

            if (!text) {
                return;
            }

            try {

                await navigator.clipboard.writeText(text);

                const oldText =
                    copyButton.textContent;

                copyButton.textContent =
                    "Copied ✓";

                setTimeout(function () {
                    copyButton.textContent = oldText;
                }, 2000);

            } catch (error) {

                console.error(
                    "Copy Error:",
                    error
                );

                const textarea =
                    document.createElement("textarea");

                textarea.value = text;

                document.body.appendChild(textarea);

                textarea.select();

                try {
                    document.execCommand("copy");
                } catch (copyError) {
                    console.error(copyError);
                }

                document.body.removeChild(textarea);
            }

        });
    }


    // ================================
    // SUMMARY SHOW MORE / LESS
    // ================================
    setupSummaryToggle();

});


// ============================================
// UPDATE FIELD
// ============================================
function updateElement(elementId, value) {

    const element =
        document.getElementById(elementId);

    if (!element) {
        return;
    }

    if (
        value === null ||
        value === undefined ||
        String(value).trim() === ""
    ) {
        element.textContent = "Not reported";
        return;
    }

    element.textContent =
        String(value).trim();
}


// ============================================
// SUMMARY TOGGLE
// ============================================
function setupSummaryToggle() {

    const summaryElement =
        document.getElementById("summaryText");

    const toggleButton =
        document.getElementById("toggleSummaryExpand");

    if (!summaryElement || !toggleButton) {
        return;
    }

    const fullText =
        summaryElement.textContent.trim();

    const maxLength = 250;

    if (fullText.length <= maxLength) {
        toggleButton.style.display = "none";
        return;
    }

    const shortText =
        fullText.substring(0, maxLength) + "...";

    summaryElement.textContent =
        shortText;

    toggleButton.textContent =
        "Show more";

    toggleButton.setAttribute(
        "aria-expanded",
        "false"
    );

    toggleButton.addEventListener(
        "click",
        function () {

            const expanded =
                toggleButton.getAttribute(
                    "aria-expanded"
                ) === "true";

            if (expanded) {

                summaryElement.textContent =
                    shortText;

                toggleButton.textContent =
                    "Show more";

                toggleButton.setAttribute(
                    "aria-expanded",
                    "false"
                );

            } else {

                summaryElement.textContent =
                    fullText;

                toggleButton.textContent =
                    "Show less";

                toggleButton.setAttribute(
                    "aria-expanded",
                    "true"
                );
            }

        }
    );
}