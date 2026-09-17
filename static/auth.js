/* =========================================================
   CARESYNC AUTHENTICATION
   Flask + MySQL
   ========================================================= */


/* =========================================================
   GET ROLE FROM URL
   ========================================================= */

function getRoleFromURL() {

    const params = new URLSearchParams(
        window.location.search
    );

    const role = params.get("role");

    if (role === "patient") {
        return "patient";
    }

    if (role === "doctor") {
        return "doctor";
    }

    return "patient";
}



/* =========================================================
   EMAIL VALIDATION
   ========================================================= */

function isValidEmail(value) {

    const pattern =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    return pattern.test(
        value.trim()
    );
}


/* =========================================================
   FIELD ERROR
   ========================================================= */

function setFieldError(input, message) {

    const group =
        input.closest(".form-group");

    if (!group) return;

    group.classList.add("has-error");

    const error =
        group.querySelector(".error-text");

    if (error) {
        error.textContent = message;
    }
}


/* =========================================================
   CLEAR FIELD ERROR
   ========================================================= */

function clearFieldError(input) {

    const group =
        input.closest(".form-group");

    if (!group) return;

    group.classList.remove("has-error");
}


/* =========================================================
   CLEAR ALL ERRORS
   ========================================================= */

function clearAllErrors(form) {

    form.querySelectorAll(
        ".form-group"
    ).forEach(function (group) {

        group.classList.remove(
            "has-error"
        );

    });
}


/* =========================================================
   STATUS MESSAGE
   ========================================================= */

function showStatusMessage(
    element,
    message,
    type
) {

    if (!element) return;

    element.textContent = message;

    element.classList.remove(
        "success",
        "error"
    );

    element.classList.add(type);
}


/* =========================================================
   PASSWORD TOGGLE
   ========================================================= */

function initPasswordToggles() {

    const buttons =
        document.querySelectorAll(
            ".toggle-password"
        );

    buttons.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                const wrapper =
                    button.closest(
                        ".password-wrapper"
                    );

                if (!wrapper) return;

                const input =
                    wrapper.querySelector(
                        "input"
                    );

                if (!input) return;

                if (input.type === "password") {

                    input.type = "text";

                    button.textContent =
                        "Hide";

                } else {

                    input.type = "password";

                    button.textContent =
                        "Show";
                }

            }
        );

    });
}


/* =========================================================
   LOGIN PAGE
   ========================================================= */

function initLoginPage() {

    const form =
        document.getElementById(
            "loginForm"
        );

    if (!form) return;


    /* GET ROLE */

    const role =
        getRoleFromURL();


    /* GET ELEMENTS */

    const title =
        document.getElementById(
            "authTitle"
        );

    const subtitle =
        document.getElementById(
            "authSubtitle"
        );

    const label =
        document.getElementById(
            "identifierLabel"
        );

    const identifier =
        document.getElementById(
            "identifier"
        );

    const createAccount =
        document.getElementById(
            "createAccountLink"
        );

    const status =
        document.getElementById(
            "statusMessage"
        );


    /* =====================================================
       PATIENT LOGIN
       ===================================================== */

    if (role === "patient") {

        if (title) {
            title.textContent =
                "Patient Sign In";
        }

        if (subtitle) {
            subtitle.textContent =
                "Access your intake profile and records.";
        }

        if (label) {
            label.textContent =
                "Patient ID / ABHA Number / Phone";
        }

        if (identifier) {

            identifier.placeholder =
                "ABHA number or phone number";

            identifier.name =
                "patientIdentifier";
        }

    }


    /* =====================================================
       DOCTOR / STAFF LOGIN
       ===================================================== */

    else {

        if (title) {
            title.textContent =
                "Doctor / Hospital Staff Sign In";
        }

        if (subtitle) {
            subtitle.textContent =
                "Access the clinical intake dashboard.";
        }

        if (label) {
            label.textContent =
                "Email";
        }

        if (identifier) {

            identifier.placeholder =
                "doctor@hospital.com";

            identifier.name =
                "email";
        }
    }


    /* =====================================================
       REGISTER LINK
       ===================================================== */

    if (createAccount) {

        createAccount.href =
            "/register?role=" + role;
    }


    /* =====================================================
       LOGIN SUBMIT
       ===================================================== */

    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            clearAllErrors(form);


            let valid = true;


            /* =================================================
               IDENTIFIER VALIDATION
               ================================================= */

            if (
                !identifier ||
                identifier.value.trim() === ""
            ) {

                if (identifier) {

                    setFieldError(
                        identifier,
                        role === "patient"
                            ? "Patient ID / ABHA / Phone is required."
                            : "Email is required."
                    );
                }

                valid = false;

            } else if (
                role === "doctor" &&
                !isValidEmail(
                    identifier.value
                )
            ) {

                setFieldError(
                    identifier,
                    "Enter a valid email address."
                );

                valid = false;
            }


            /* =================================================
               PASSWORD VALIDATION
               ================================================= */

            const password =
                document.getElementById(
                    "password"
                );

            if (
                !password ||
                password.value.trim() === ""
            ) {

                if (password) {

                    setFieldError(
                        password,
                        "Password is required."
                    );
                }

                valid = false;
            }


            /* =================================================
               STOP IF INVALID
               ================================================= */

            if (!valid) {

                showStatusMessage(
                    status,
                    "Please fix the highlighted fields.",
                    "error"
                );

                return;
            }


            /* =================================================
               SEND LOGIN DATA TO FLASK
               ================================================= */

            const formData =
                new FormData(form);


            /* IMPORTANT:
               Flask ko role bhejna */

            formData.set(
                "role",
                role
            );


            try {

                const response =
                    await fetch(
                        "/login",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const message =
                    await response.text();


                /* =================================================
                   LOGIN FAILED
                   ================================================= */

                if (!response.ok) {

                    throw new Error(
                        message ||
                        "Login failed."
                    );
                }


                /* =================================================
                   LOGIN SUCCESS
                   ================================================= */

                showStatusMessage(
                    status,
                    "Login successful! Redirecting...",
                    "success"
                );


                setTimeout(
    function () {

        if (role === "patient") {
            window.location.href =
                "/patient-dashboard";
        } else {
            window.location.href =
                "/dashboard";
        }

    },
    800
);


            } catch (error) {

                console.error(
                    "Login error:",
                    error
                );

                showStatusMessage(
                    status,
                    error.message ||
                    "Login failed. Please try again.",
                    "error"
                );
            }

        }
    );
}


/* =========================================================
   REGISTER PAGE
   ========================================================= */

function initRegisterPage() {

    const form =
        document.getElementById(
            "registerForm"
        );

    if (!form) return;


    /* GET ROLE */

    const role =
        getRoleFromURL();


    /* GET ELEMENTS */

    const doctorFields =
        document.getElementById(
            "doctorFields"
        );

    const patientFields =
        document.getElementById(
            "patientFields"
        );

    const title =
        document.getElementById(
            "authTitle"
        );

    const subtitle =
        document.getElementById(
            "authSubtitle"
        );

    const signIn =
        document.getElementById(
            "signInLink"
        );

    const status =
        document.getElementById(
            "statusMessage"
        );


    /* =====================================================
       PATIENT REGISTRATION
       ===================================================== */

    if (role === "patient") {

        if (title) {
            title.textContent =
                "Patient Registration";
        }

        if (subtitle) {
            subtitle.textContent =
                "Create your account to begin intake.";
        }

        if (doctorFields) {
            doctorFields.style.display =
                "none";
        }

        if (patientFields) {
            patientFields.style.display =
                "block";
        }

    }


    /* =====================================================
       DOCTOR REGISTRATION
       ===================================================== */

    else {

        if (title) {
            title.textContent =
                "Doctor / Hospital Staff Registration";
        }

        if (subtitle) {
            subtitle.textContent =
                "Create a staff account to access the dashboard.";
        }

        if (doctorFields) {
            doctorFields.style.display =
                "block";
        }

        if (patientFields) {
            patientFields.style.display =
                "none";
        }
    }


    /* =====================================================
       SIGN IN LINK
       ===================================================== */

    if (signIn) {

        signIn.href =
            "/?role=" + role;
    }


    /* =====================================================
       REGISTER SUBMIT
       ===================================================== */

    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            clearAllErrors(form);


            let valid = true;


            /* =================================================
               FULL NAME
               ================================================= */

            const fullName =
                document.getElementById(
                    "fullName"
                );

            if (
                !fullName ||
                fullName.value.trim() === ""
            ) {

                if (fullName) {

                    setFieldError(
                        fullName,
                        "Full name is required."
                    );
                }

                valid = false;
            }


            /* =================================================
               DOCTOR / STAFF FIELDS
               ================================================= */

            if (role === "doctor") {

                const email =
                    document.getElementById(
                        "email"
                    );

                const staffRole =
                    document.getElementById(
                        "staffRole"
                    );

                const department =
                    document.getElementById(
                        "department"
                    );

                const hospital =
                    document.getElementById(
                        "hospital"
                    );


                /* EMAIL */

                if (
                    !email ||
                    email.value.trim() === ""
                ) {

                    if (email) {

                        setFieldError(
                            email,
                            "Email is required."
                        );
                    }

                    valid = false;

                } else if (
                    !isValidEmail(
                        email.value
                    )
                ) {

                    setFieldError(
                        email,
                        "Enter a valid email."
                    );

                    valid = false;
                }


                /* STAFF ROLE */

                if (
                    !staffRole ||
                    staffRole.value === ""
                ) {

                    if (staffRole) {

                        setFieldError(
                            staffRole,
                            "Please select a staff role."
                        );
                    }

                    valid = false;
                }


                /* DEPARTMENT */

                if (
                    !department ||
                    department.value.trim() === ""
                ) {

                    if (department) {

                        setFieldError(
                            department,
                            "Department is required."
                        );
                    }

                    valid = false;
                }


                /* HOSPITAL */

                if (
                    !hospital ||
                    hospital.value.trim() === ""
                ) {

                    if (hospital) {

                        setFieldError(
                            hospital,
                            "Hospital is required."
                        );
                    }

                    valid = false;
                }
            }


            /* =================================================
               PATIENT FIELDS
               ================================================= */

            else {

                const age =
                    document.getElementById(
                        "age"
                    );

                const gender =
                    document.getElementById(
                        "gender"
                    );

                const phone =
                    document.getElementById(
                        "phone"
                    );


                /* AGE */

                if (
                    !age ||
                    age.value.trim() === ""
                ) {

                    if (age) {

                        setFieldError(
                            age,
                            "Age is required."
                        );
                    }

                    valid = false;

                } else if (
                    Number(age.value) <= 0
                ) {

                    setFieldError(
                        age,
                        "Enter a valid age."
                    );

                    valid = false;
                }


                /* GENDER */

                if (
                    !gender ||
                    gender.value === ""
                ) {

                    if (gender) {

                        setFieldError(
                            gender,
                            "Please select gender."
                        );
                    }

                    valid = false;
                }


                /* PHONE */

                if (
                    !phone ||
                    phone.value.trim() === ""
                ) {

                    if (phone) {

                        setFieldError(
                            phone,
                            "Phone number is required."
                        );
                    }

                    valid = false;
                }
            }


            /* =================================================
               PASSWORD
               ================================================= */

            const password =
                document.getElementById(
                    "password"
                );

            const confirmPassword =
                document.getElementById(
                    "confirmPassword"
                );


            if (
                !password ||
                password.value.trim() === ""
            ) {

                if (password) {

                    setFieldError(
                        password,
                        "Password is required."
                    );
                }

                valid = false;

            } else if (
                password.value.length < 6
            ) {

                setFieldError(
                    password,
                    "Password must be at least 6 characters."
                );

                valid = false;
            }


            /* =================================================
               CONFIRM PASSWORD
               ================================================= */

            if (
                !confirmPassword ||
                confirmPassword.value.trim() === ""
            ) {

                if (confirmPassword) {

                    setFieldError(
                        confirmPassword,
                        "Please confirm your password."
                    );
                }

                valid = false;

            } else if (
                confirmPassword.value !==
                password.value
            ) {

                setFieldError(
                    confirmPassword,
                    "Passwords do not match."
                );

                valid = false;
            }


            /* =================================================
               STOP IF INVALID
               ================================================= */

            if (!valid) {

                showStatusMessage(
                    status,
                    "Please fix the highlighted fields.",
                    "error"
                );

                return;
            }


            /* =================================================
               SEND REGISTRATION DATA TO FLASK
               ================================================= */

            const formData =
                new FormData(form);


            /* IMPORTANT:
               Flask ko role bhejna */

            formData.set(
                "role",
                role
            );


            try {

                const response =
                    await fetch(
                        "/register",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const message =
                    await response.text();


                /* =================================================
                   REGISTRATION FAILED
                   ================================================= */

                if (!response.ok) {

                    throw new Error(
                        message ||
                        "Registration failed."
                    );
                }


                /* =================================================
                   REGISTRATION SUCCESS
                   ================================================= */

                showStatusMessage(
                    status,
                    "Registration successful! Redirecting to sign in...",
                    "success"
                );


                setTimeout(
                    function () {

                        window.location.href =
                            "/?role=" + role;

                    },
                    1000
                );


            } catch (error) {

                console.error(
                    "Registration error:",
                    error
                );

                showStatusMessage(
                    status,
                    error.message ||
                    "Registration failed. Please try again.",
                    "error"
                );
            }

        }
    );
}


/* =========================================================
   PAGE LOAD
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initPasswordToggles();

        initLoginPage();

        initRegisterPage();


        /* =====================================================
           CLEAR ERROR WHEN USER TYPES
           ===================================================== */

        document
            .querySelectorAll(
                ".form-group input, .form-group select"
            )
            .forEach(function (element) {

                element.addEventListener(
                    "input",
                    function () {

                        clearFieldError(
                            element
                        );

                    }
                );


                element.addEventListener(
                    "change",
                    function () {

                        clearFieldError(
                            element
                        );

                    }
                );

            });

    }
);