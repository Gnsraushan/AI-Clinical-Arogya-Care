/* =====================================================
   CARESYNC
   Flask + MySQL + Groq Chat Integration
   ===================================================== */


/* ================= ELEMENTS ================= */

var messageInput = document.getElementById("messageInput");
var sendButton = document.getElementById("sendButton");
var messages = document.getElementById("messages");

var toast = document.getElementById("toast");
var toastTitle = document.getElementById("toastTitle");
var toastMessage = document.getElementById("toastMessage");


/* =====================================================
   TOAST
   ===================================================== */

function showToast(title, message) {

    if (!toast || !toastTitle || !toastMessage) {
        return;
    }

    toastTitle.textContent = title;
    toastMessage.textContent = message;

    toast.classList.add("show");

    clearTimeout(window.toastTimer);

    window.toastTimer = setTimeout(function () {
        toast.classList.remove("show");
    }, 2500);
}


/* =====================================================
   ADD PATIENT MESSAGE
   ===================================================== */

function addPatientMessage(text) {

    if (!messages) {
        return;
    }

    var message = document.createElement("div");
    message.className = "message patient-message";

    var bubble = document.createElement("div");
    bubble.className = "bubble";

    var paragraph = document.createElement("p");
    paragraph.textContent = text;

    var small = document.createElement("small");
    small.textContent = "Now";

    bubble.appendChild(paragraph);
    bubble.appendChild(small);

    var avatar = document.createElement("div");
    avatar.className = "message-avatar patient";
    avatar.textContent = "RS";

    message.appendChild(bubble);
    message.appendChild(avatar);

    messages.appendChild(message);

    messages.scrollTop = messages.scrollHeight;
}


/* =====================================================
   ADD AI MESSAGE
   ===================================================== */

function addAIMessage(text) {

    if (!messages) {
        return;
    }

    var message = document.createElement("div");
    message.className = "message ai-message";

    var avatar = document.createElement("div");
    avatar.className = "message-avatar ai";
    avatar.textContent = "✦";

    var bubble = document.createElement("div");
    bubble.className = "bubble";

    var title = document.createElement("b");
    title.textContent = "AI Assistant";

    var paragraph = document.createElement("p");
    paragraph.textContent = text;

    var small = document.createElement("small");
    small.textContent = "Now";

    bubble.appendChild(title);
    bubble.appendChild(paragraph);
    bubble.appendChild(small);

    message.appendChild(avatar);
    message.appendChild(bubble);

    messages.appendChild(message);

    messages.scrollTop = messages.scrollHeight;
}


/* =====================================================
   RED FLAG ALERT
   ===================================================== */

function showRedFlagAlert(reason) {

    /* If alert already exists, remove old one */
    var oldAlert = document.getElementById("redFlagAlert");

    if (oldAlert) {
        oldAlert.remove();
    }


    /* Create alert box */
    var alertBox = document.createElement("div");

    alertBox.id = "redFlagAlert";

    alertBox.style.position = "fixed";
    alertBox.style.top = "24px";
    alertBox.style.right = "24px";
    alertBox.style.width = "360px";
    alertBox.style.maxWidth = "calc(100vw - 48px)";
    alertBox.style.background = "#fff5f5";
    alertBox.style.border = "1px solid #ffb8b8";
    alertBox.style.borderLeft = "5px solid #dc2626";
    alertBox.style.borderRadius = "12px";
    alertBox.style.padding = "16px";
    alertBox.style.boxShadow = "0 8px 25px rgba(0,0,0,0.15)";
    alertBox.style.zIndex = "99999";
    alertBox.style.fontFamily = "Arial, sans-serif";


    /* Heading */
    var heading = document.createElement("div");

    heading.textContent = "⚠ RED-FLAG ALERT";

    heading.style.fontWeight = "700";
    heading.style.color = "#b91c1c";
    heading.style.fontSize = "16px";
    heading.style.marginBottom = "8px";


    /* Message */
    var message = document.createElement("div");

    message.textContent =
        reason ||
        "A potentially urgent symptom was reported. Please alert hospital staff immediately.";

    message.style.color = "#4b1d1d";
    message.style.fontSize = "14px";
    message.style.lineHeight = "1.5";
    message.style.marginBottom = "12px";


    /* Important note */
    var note = document.createElement("div");

    note.textContent =
        "This is an alert, not a diagnosis. A doctor or hospital staff member must make the final decision.";

    note.style.color = "#6b3030";
    note.style.fontSize = "12px";
    note.style.lineHeight = "1.4";


    /* Close button */
    var closeButton = document.createElement("button");

    closeButton.textContent = "Dismiss";

    closeButton.type = "button";

    closeButton.style.marginTop = "12px";
    closeButton.style.padding = "7px 12px";
    closeButton.style.border = "1px solid #dc2626";
    closeButton.style.borderRadius = "7px";
    closeButton.style.background = "#ffffff";
    closeButton.style.color = "#b91c1c";
    closeButton.style.cursor = "pointer";
    closeButton.style.fontWeight = "600";


    closeButton.addEventListener("click", function () {
        alertBox.remove();
    });


    /* Build alert */
    alertBox.appendChild(heading);
    alertBox.appendChild(message);
    alertBox.appendChild(note);
    alertBox.appendChild(closeButton);

    document.body.appendChild(alertBox);


    /* Also show toast */
    showToast(
        "URGENT ALERT",
        "Potential red-flag symptom detected."
    );
}


/* =====================================================
   SEND MESSAGE
   ===================================================== */

async function sendMessage() {

    if (!messageInput) {
        return;
    }

    var text = messageInput.value.trim();

    if (!text) {
        return;
    }


    /* Show patient message immediately */
    addPatientMessage(text);

    messageInput.value = "";


    /* Disable send button while AI is responding */
    if (sendButton) {
        sendButton.disabled = true;
    }


    try {

        var response = await fetch("/api/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: text
            })

        });


        var data = await response.json();


        /* Backend error */
        if (!response.ok || !data.success) {

            showToast(
                "Error",
                data.message || "AI response nahi mila."
            );

            return;
        }


        /* =================================================
           AI RESPONSE
           ================================================= */

        if (data.reply) {

            addAIMessage(data.reply);

            showToast(
                "Response received",
                "AI response successfully generated."
            );

        } else {

            showToast(
                "Error",
                "AI ne koi response nahi diya."
            );
        }


        /* =================================================
           RED FLAG RESPONSE
           ================================================= */

        if (data.red_flag === true) {

            showRedFlagAlert(
                data.red_flag_reason
            );

        }


        /*
         IMPORTANT:

         Patient history yahan automatically generate nahi
         kar rahe hain.

         Isse har patient message par Groq ka extra API call
         nahi jayega.

         History sirf Generate Patient History button se
         generate hogi.
        */

    }


    catch (error) {

        console.error(
            "Chat Error:",
            error
        );

        showToast(
            "Connection Error",
            "Flask server se connection nahi ho pa raha."
        );

    }


    finally {

        if (sendButton) {
            sendButton.disabled = false;
        }

        if (messageInput) {
            messageInput.focus();
        }

    }

}


/* =====================================================
   SEND BUTTON
   ===================================================== */

if (sendButton) {

    sendButton.addEventListener(
        "click",
        sendMessage
    );

}


/* =====================================================
   ENTER KEY
   ===================================================== */

if (messageInput) {

    messageInput.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {

                event.preventDefault();

                sendMessage();

            }

        }
    );

}


/* =====================================================
   QUICK ANSWERS
   ===================================================== */

var quickButtons =
    document.querySelectorAll(
        ".quick-buttons button"
    );


quickButtons.forEach(function (button) {

    button.addEventListener(
        "click",
        function () {

            if (messageInput) {

                messageInput.value =
                    button.textContent.trim();

                sendMessage();

            }

        }
    );

});


/* =====================================================
   LANGUAGE
   ===================================================== */

var languageButtons =
    document.querySelectorAll(
        ".language"
    );


languageButtons.forEach(function (button) {

    button.addEventListener(
        "click",
        function () {

            languageButtons.forEach(
                function (b) {
                    b.classList.remove("active");
                }
            );

            button.classList.add("active");

            showToast(
                "Language selected",
                button.textContent + " mode selected."
            );

        }
    );

});


/* =====================================================
   VOICE INPUT
   ===================================================== */

var micButton =
    document.getElementById("micButton");


if (micButton) {

    micButton.addEventListener(
        "click",
        function () {

            showToast(
                "Voice input",
                "Voice recognition will be connected later."
            );

        }
    );

}


/* =====================================================
   NEW VISIT
   ===================================================== */

var newVisit =
    document.getElementById("newVisit");


if (newVisit) {

    newVisit.addEventListener(
        "click",
        function () {

            showToast(
                "New visit",
                "A new patient case-taking session is ready."
            );

        }
    );

}


/* =====================================================
   UPLOAD DOCUMENT
   ===================================================== */

var fileInput =
    document.getElementById("fileInput");

var uploadButton =
    document.getElementById("uploadButton");


if (uploadButton && fileInput) {

    uploadButton.addEventListener(
        "click",
        function () {

            fileInput.click();

        }
    );


    fileInput.addEventListener(
        "change",
        function () {

            var file =
                fileInput.files[0];

            if (!file) {
                return;
            }

            showToast(
                "Document selected",
                file.name + " is ready for processing."
            );

        }
    );

}


/* =====================================================
   EDIT SUMMARY
   ===================================================== */

var editSummary =
    document.getElementById("editSummary");


if (editSummary) {

    editSummary.addEventListener(
        "click",
        function () {

            showToast(
                "Edit mode",
                "Case summary is ready for editing."
            );

        }
    );

}


/* =====================================================
   PREVIEW
   ===================================================== */

var previewButton =
    document.getElementById("previewButton");


if (previewButton) {

    previewButton.addEventListener(
        "click",
        function () {

            showToast(
                "Case preview",
                "Physician-ready case sheet preview opened."
            );

        }
    );

}


/* =====================================================
   VERIFY CASE
   ===================================================== */

var verifyButton =
    document.getElementById("verifyButton");


if (verifyButton) {

    verifyButton.addEventListener(
        "click",
        function () {

            var status =
                document.querySelector(
                    ".review-status"
                );


            if (status) {

                status.textContent =
                    "Verified";

                status.style.background =
                    "#eafaf3";

                status.style.color =
                    "#168e65";

            }


            showToast(
                "Case verified",
                "Physician review completed successfully."
            );

        }
    );

}


/* =====================================================
   SEARCH
   ===================================================== */

var searchInput =
    document.getElementById("searchInput");


if (searchInput) {

    searchInput.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {

                var query =
                    searchInput.value.trim();


                if (query) {

                    showToast(
                        "Patient search",
                        "Searching for " + query + "..."
                    );

                }

            }

        }
    );

}


/* =====================================================
   CTRL + K SEARCH
   ===================================================== */

document.addEventListener(
    "keydown",
    function (event) {

        if (
            (event.ctrlKey || event.metaKey) &&
            event.key.toLowerCase() === "k"
        ) {

            event.preventDefault();

            if (searchInput) {
                searchInput.focus();
            }

        }

    }
);


/* =====================================================
   SIDEBAR
   ===================================================== */

var navItems =
    document.querySelectorAll(
        ".nav-item"
    );


navItems.forEach(function (item) {

    item.addEventListener(
        "click",
        function () {

            navItems.forEach(
                function (nav) {
                    nav.classList.remove("active");
                }
            );


            item.classList.add("active");


            var text =
                item.textContent.trim();


            if (
                text !== "Dashboard" &&
                text !== "Settings"
            ) {

                showToast(
                    "Workspace",
                    text + " selected."
                );

            }

        }
    );

});


/* =====================================================
   STARTUP
   ===================================================== */

console.log(
    "CareSync frontend initialized successfully."
);

console.log(
    "Flask + MySQL + Groq chat integration enabled."
);

console.log(
    "Red-flag detection enabled."
);