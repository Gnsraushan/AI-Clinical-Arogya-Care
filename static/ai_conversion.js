document.addEventListener("DOMContentLoaded", function () {

    // =========================================================
    // MOBILE MENU
    // =========================================================

    const menuButton =
        document.getElementById("mobileMenuToggle");

    const mobileDrawer =
        document.getElementById("mobileDrawer");

    if (menuButton && mobileDrawer) {

        menuButton.addEventListener("click", function () {

            const isOpen =
                menuButton.getAttribute("aria-expanded") === "true";

            if (isOpen) {

                menuButton.setAttribute(
                    "aria-expanded",
                    "false"
                );

                mobileDrawer.setAttribute(
                    "aria-hidden",
                    "true"
                );

                mobileDrawer.classList.remove("open");

            } else {

                menuButton.setAttribute(
                    "aria-expanded",
                    "true"
                );

                mobileDrawer.setAttribute(
                    "aria-hidden",
                    "false"
                );

                mobileDrawer.classList.add("open");
            }
        });
    }


    // =========================================================
    // ELEMENTS
    // =========================================================

    const conversationStream =
        document.getElementById("conversationStream");

    const intakeForm =
        document.getElementById("intakeForm");

    const patientMessage =
        document.getElementById("patientMessage");


    // =========================================================
    // AUTO SCROLL
    // =========================================================

    function scrollConversation() {

        if (!conversationStream) {
            return;
        }

        conversationStream.scrollTop =
            conversationStream.scrollHeight;
    }

    scrollConversation();


    // =========================================================
    // ADD MESSAGE TO CHAT
    // =========================================================

    function addMessage(sender, message) {

        if (!conversationStream) {
            return;
        }

        const isPatient =
            String(sender).toLowerCase() === "patient" ||
            String(sender).toLowerCase() === "user";

        const article =
            document.createElement("article");

        article.className =
            "message-row " +
            (isPatient ? "row-patient" : "row-ai");


        const avatar =
            document.createElement("div");

        avatar.className =
            "message-avatar";

        avatar.setAttribute(
            "aria-hidden",
            "true"
        );

        avatar.textContent =
            isPatient ? "P" : "AI";


        const container =
            document.createElement("div");

        container.className =
            "message-bubble-container";


        const meta =
            document.createElement("div");

        meta.className =
            "message-meta";


        const speaker =
            document.createElement("span");

        speaker.className =
            "speaker-label";

        speaker.textContent =
            isPatient
                ? "PATIENT"
                : "AI ASSISTANT";


        meta.appendChild(speaker);


        const content =
            document.createElement("div");

        content.className =
            "message-content";


        const paragraph =
            document.createElement("p");

        paragraph.textContent =
            message;


        content.appendChild(paragraph);

        container.appendChild(meta);

        container.appendChild(content);

        article.appendChild(avatar);

        article.appendChild(container);

        conversationStream.appendChild(article);

        scrollConversation();
    }


    // =========================================================
    // CHAT FORM
    // =========================================================

    if (intakeForm && patientMessage) {

        intakeForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();

                const message =
                    patientMessage.value.trim();

                if (!message) {
                    return;
                }


                const submitButton =
                    intakeForm.querySelector(
                        'button[type="submit"]'
                    );


                if (submitButton) {
                    submitButton.disabled = true;
                }


                patientMessage.disabled = true;


                // Show patient message immediately

                addMessage(
                    "patient",
                    message
                );


                patientMessage.value = "";


                try {

                    const response =
                        await fetch(
                            intakeForm.action ||
                            "/api/chat",
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json",

                                    "Accept":
                                        "application/json"
                                },

                                credentials:
                                    "same-origin",

                                body: JSON.stringify({
                                    message: message
                                })
                            }
                        );


                    let data;

                    try {

                        data =
                            await response.json();

                    } catch (jsonError) {

                        throw new Error(
                            "Server ne valid JSON response nahi diya. Status: " +
                            response.status
                        );
                    }


                    if (
                        !response.ok ||
                        !data.success
                    ) {

                        throw new Error(
                            data.message ||
                            "AI response nahi mila."
                        );
                    }


                    // =================================================
                    // AI REPLY
                    // =================================================

                    if (data.reply) {

                        addMessage(
                            "ai",
                            data.reply
                        );
                    }


                    // =================================================
                    // REPORT UPDATE
                    // =================================================

                    if (data.history) {

                        updateHistory(
                            data.history
                        );
                    }


                    // =================================================
                    // RED FLAG
                    // =================================================

                    if (data.red_flag) {

                        showRedFlag(
                            data.red_flag_reason,
                            data.red_flag_category
                        );
                    }

                } catch (error) {

                    console.error(
                        "AI CHAT ERROR:",
                        error
                    );

                    alert(
                        error.message ||
                        "AI response lene mein problem hui."
                    );

                } finally {

                    if (submitButton) {
                        submitButton.disabled = false;
                    }

                    patientMessage.disabled = false;

                    patientMessage.focus();

                    scrollConversation();
                }
            }
        );
    }


    // =========================================================
    // UPDATE HISTORY
    // =========================================================

    function updateElement(
        id,
        value
    ) {

        const element =
            document.getElementById(id);

        if (!element) {
            return;
        }

        element.textContent =
            value ||
            "Not clearly stated.";
    }


    function updateHistory(history) {

        if (!history) {
            return;
        }


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


        updateElement(
            "summaryText",
            history.summary
        );
    }


    // =========================================================
    // RED FLAG
    // =========================================================

    function showRedFlag(
        reason,
        category
    ) {

        const redFlagElement =
            document.getElementById(
                "redFlag"
            );


        if (!redFlagElement) {
            return;
        }


        redFlagElement.textContent =
            reason ||
            category ||
            "Potential red flag detected.";

        redFlagElement.classList.add(
            "active"
        );
    }


    // =========================================================
    // GENERATE REPORT BUTTON
    // =========================================================

    const generateButton =
        document.getElementById(
            "generateHistoryBtn"
        );


    if (generateButton) {

        generateButton.addEventListener(
            "click",
            async function () {

                if (generateButton.disabled) {
                    return;
                }


                generateButton.disabled = true;


                const oldText =
                    generateButton.textContent;


                generateButton.textContent =
                    "Generating...";


                try {

                    const generateUrl =
                        generateButton.getAttribute(
                            "data-generate-url"
                        );


                    if (!generateUrl) {

                        throw new Error(
                            "Generate Report URL is missing."
                        );
                    }


                    const response =
                        await fetch(
                            generateUrl,
                            {
                                method: "POST",

                                headers: {
                                    "Accept":
                                        "application/json"
                                },

                                credentials:
                                    "same-origin"
                            }
                        );


                    let data;

                    try {

                        data =
                            await response.json();

                    } catch (jsonError) {

                        throw new Error(
                            "Server ne valid response nahi diya. Status: " +
                            response.status
                        );
                    }


                    if (
                        !response.ok ||
                        !data.success
                    ) {

                        throw new Error(
                            data.message ||
                            "Report generate nahi ho payi."
                        );
                    }


                    updateHistory(
                        data.history || {}
                    );


                    if (data.red_flag) {

                        showRedFlag(
                            data.red_flag_reason,
                            data.red_flag_category
                        );
                    }


                } catch (error) {

                    console.error(
                        "REPORT ERROR:",
                        error
                    );


                    alert(
                        error.message ||
                        "Something went wrong while generating the report."
                    );


                } finally {

                    generateButton.disabled =
                        false;

                    generateButton.textContent =
                        oldText;
                }
            }
        );
    }


    // =========================================================
    // COPY SUMMARY
    // =========================================================

    const copySummaryButton =
        document.getElementById(
            "copySummaryBtn"
        );


    if (copySummaryButton) {

        copySummaryButton.addEventListener(
            "click",
            async function () {

                const summaryElement =
                    document.getElementById(
                        "summaryText"
                    );


                if (!summaryElement) {
                    return;
                }


                const text =
                    summaryElement.textContent.trim();


                if (!text) {
                    return;
                }


                try {

                    await navigator.clipboard.writeText(
                        text
                    );

                    const oldText =
                        copySummaryButton.textContent;


                    copySummaryButton.textContent =
                        "Copied";


                    setTimeout(
                        function () {

                            copySummaryButton.textContent =
                                oldText;

                        },
                        1500
                    );

                } catch (error) {

                    console.error(
                        "COPY ERROR:",
                        error
                    );
                }
            }
        );
    }


    // =========================================================
    // SUMMARY SHOW MORE / LESS
    // =========================================================

    const toggleButton =
        document.getElementById(
            "toggleSummaryBtn"
        );

    const summaryElement =
        document.getElementById(
            "summaryText"
        );


    if (
        toggleButton &&
        summaryElement
    ) {

        const fullText =
            summaryElement.textContent.trim();


        if (fullText.length > 300) {

            const shortText =
                fullText.substring(
                    0,
                    300
                ) + "...";


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
        } else {

            toggleButton.style.display =
                "none";
        }
    }


    // =========================================================
    // INITIAL SCROLL
    // =========================================================

    scrollConversation();

});