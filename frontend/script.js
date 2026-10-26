
/* =====================================================
   RESULTSHIELD — FRONTEND CONTROLLER
   Student Portal + Admin Workspace + Self-Healing UI
   ===================================================== */

const API_BASE = "http://127.0.0.1:8000";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

let adminToken = null;
let currentView = "overview";
let editingStudent = false;

// ---------- SAFE HELPERS ----------

function setText(selector, message) {
    const element = $(selector);
    if (element) element.textContent = message
}

function showMessage(selector, message, type = "") {
    const element = $(selector);
    if (!element) return;

    element.textContent = message;
    element.className = type ? `message ${type}` : "message";
}


function setHidden(selector, hidden) {
    const element = $(selector);

    if (element) {
        element.hidden = hidden;
        element.classList.toggle("hidden", hidden);
    }
}

function escapeText(value) {
    return String(value ?? "");
}

async function apiRequest(path, options = {}) {
    const headers = {
        ...(options.headers || {})
    };

    if (options.body && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }

    if (adminToken) {
        headers.Authorization = `Bearer ${adminToken}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers
    });

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        const detail =
            typeof data === "object"
                ? data.detail || data.message
                : data;

        throw new Error(detail || `Request failed (${response.status})`);
    }

    return data;
}

// ---------- THEME TOGGLE ----------

function initTheme() {
    const savedTheme = localStorage.getItem("resultshield-theme");

    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
    }

    const toggle = $("#themeToggle");

    if (!toggle) return;

    updateThemeButton();

    toggle.addEventListener("click", () => {
        document.body.classList.toggle("light-theme");

        const theme = document.body.classList.contains("light-theme")
            ? "light"
            : "dark";

        localStorage.setItem("resultshield-theme", theme);
        updateThemeButton();
    });
}

function updateThemeButton() {
    const toggle = $("#themeToggle");
    if (!toggle) return;

    const isLight = document.body.classList.contains("light-theme");

    toggle.textContent = isLight ? "☾" : "☀";
    toggle.setAttribute(
        "aria-label",
        isLight ? "Switch to dark theme" : "Switch to light theme"
    );
}

// ---------- STUDENT / ADMIN VISIBILITY ----------

function showStudentPortal() {
    setHidden("#studentPortal", false);
    setHidden("#adminWorkspace", true);
    setHidden("#loginModal", true);
}

function showAdminWorkspace() {
    setHidden("#studentPortal", true);
    setHidden("#adminWorkspace", false);
    setHidden("#loginModal", true);

    setHidden("#adminLoginButton", true);
    setHidden("#adminLogoutButton", false);

    openAdminView("overview");
    refreshHealth();
    loadIncidents();
}

function updateLoginButtons() {
    setHidden("#adminLoginButton", Boolean(adminToken));
    setHidden("#adminLogoutButton", !adminToken);
}

function openLoginModal() {
    if (adminToken) {
        showAdminWorkspace();
        return;
    }

    setHidden("#loginModal", false);
    setText("#loginMessage", "");

    const username = $("#adminUsername");
    if (username) username.focus();
}

function closeLoginModal() {
    setHidden("#loginModal", true);
}

function logoutAdmin() {
    adminToken = null;
    showStudentPortal();
    updateLoginButtons();
    setText("#adminUsername", "");
    setText("#adminPassword", "");
}

// ---------- ADMIN LOGIN ----------

function initLogin() {
    $("#adminLoginButton")?.addEventListener("click", openLoginModal);
    $("#closeLogin")?.addEventListener("click", closeLoginModal);
    $("#modalBackdrop")?.addEventListener("click", closeLoginModal);

    $("#adminLogoutButton")?.addEventListener("click", logoutAdmin);

    $("#adminLoginForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();

        const username = $("#adminUsername")?.value.trim();
        const password = $("#adminPassword")?.value;

        if (!username || !password) {
            setText("#loginMessage", "Enter your username and password.");
            return;
        }

        const submitButton = event.submitter;
        if (submitButton) submitButton.disabled = true;

        setText("#loginMessage", "Verifying admin credentials…");

        try {
            /*
             * The backend must implement this endpoint and verify credentials.
             * Expected response: { "access_token": "...", "token_type": "bearer" }
             */
            const data = await apiRequest("/api/admin/login", {
                method: "POST",
                body: JSON.stringify({ username, password })
            });

            if (!data.access_token) {
                throw new Error(
                    "Login endpoint did not return an access token."
                );
            }

            adminToken = data.access_token;

            closeLoginModal();
            updateLoginButtons();
            showAdminWorkspace();
        } catch (error) {
            setText(
                "#loginMessage",
                `Login unavailable: ${error.message}. Check the backend login endpoint.`
            );
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    });
}

// ---------- ADMIN NAVIGATION ----------

function openAdminView(viewName) {
    if (!adminToken) {
        showStudentPortal();
        openLoginModal();
        return;
    }

    currentView = viewName;

    $$(".admin-view").forEach((view) => {
        const shouldHide = view.id !== `view-${viewName}`;

        view.hidden = shouldHide;
        view.classList.toggle("hidden", shouldHide);
    });

    $$("[data-view]").forEach((button) => {
        const active = button.dataset.view === viewName;

        button.classList.toggle("active", active);
        button.setAttribute("aria-current", active ? "page" : "false");
    });

    if (viewName === "students") loadStudents();
    if (viewName === "health") refreshHealth();
    if (viewName === "incidents") loadIncidents();
}

function initAdminNavigation() {
    $$("[data-view]").forEach((button) => {
        button.addEventListener("click", () => {
            openAdminView(button.dataset.view);
        });
    });
}

// ---------- STUDENT RESULT SEARCH ----------


function renderResult(response) {
    const output = $("#resultOutput");
    if (!output) return;

    output.replaceChildren();

    const student = response.student || response;
    const status = String(
        student.result ?? student.status ?? "N/A"
    ).toUpperCase();

    const passed = status === "PASS";
    const failed = status === "FAIL";

    const card = document.createElement("section");
    card.className = `academic-result-card ${passed ? "is-pass" : failed ? "is-fail" : ""}`;

    const header = document.createElement("div");
    header.className = "academic-result-header";

    const heading = document.createElement("div");
    heading.className = "academic-result-heading";

    const eyebrow = document.createElement("span");
    eyebrow.className = "result-eyebrow";
    eyebrow.textContent = "EXAMINATION RECORD";

    const title = document.createElement("h2");
    title.textContent = "Academic Result";

    const subtitle = document.createElement("p");
    subtitle.textContent = "University Examination Result";

    heading.append(eyebrow, title, subtitle);

    const badge = document.createElement("span");
    badge.className = `academic-result-badge ${
        passed ? "pass" : failed ? "fail" : "unknown"
    }`;
    badge.textContent = passed ? "✓ PASS" : failed ? "✕ FAIL" : status;

    header.append(heading, badge);

    const message = document.createElement("div");
    message.className = `result-message ${
        passed ? "message-pass" : failed ? "message-fail" : "message-unknown"
    }`;

    const messageTitle = document.createElement("strong");
    const messageText = document.createElement("p");

    if (passed) {
        messageTitle.textContent = "Congratulations!";
        messageText.textContent =
            "You have successfully passed this examination. Keep up the great work!";
    } else if (failed) {
        messageTitle.textContent = "Result Update";
        messageText.textContent =
            "You have not passed this examination. Review your marks and consult your institution about the next steps.";
    } else {
        messageTitle.textContent = "Result status unavailable";
        messageText.textContent =
            "Please contact your institution to confirm this result.";
    }

    message.append(messageTitle, messageText);

    const detailsHeading = document.createElement("h3");
    detailsHeading.className = "result-section-title";
    detailsHeading.textContent = "Student Details";

    const details = document.createElement("div");
    details.className = "academic-result-grid";

    const fields = [
        ["Student Name", student.student_name ?? student.name ?? "N/A"],
        ["Roll Number", student.roll_number ?? student.roll ?? "N/A"],
        ["Course", student.course ?? "N/A"],
        ["Semester", student.semester ?? "N/A"]
    ];

    fields.forEach(([label, value], index) => {
        const item = document.createElement("div");
        item.className = "academic-result-item";

        const number = document.createElement("span");
        number.className = "result-item-number";
        number.textContent = `0${index + 1}`;

        const contentBox = document.createElement("div");
        contentBox.className = "result-item-content";

        const caption = document.createElement("span");
        caption.className = "academic-result-label";
        caption.textContent = label;

        const valueElement = document.createElement("strong");
        valueElement.className = "academic-result-value";
        valueElement.textContent = String(value);

        contentBox.append(caption, valueElement);
        item.append(number, contentBox);
        details.appendChild(item);
    });

    const marksPanel = document.createElement("div");
    marksPanel.className = "academic-result-marks";

    const marksInfo = document.createElement("div");
    marksInfo.className = "marks-info";

    const marksLabel = document.createElement("span");
    marksLabel.textContent = "MARKS OBTAINED";

    const marksHint = document.createElement("span");
    marksHint.textContent = "Final score";

    marksInfo.append(marksLabel, marksHint);

    const marksValue = document.createElement("div");
    marksValue.className = "marks-value";

    const obtained = document.createElement("strong");
    obtained.textContent = String(student.marks ?? "N/A");

    const separator = document.createElement("span");
    separator.textContent = "/";

    const maximum = document.createElement("span");
    maximum.textContent = String(
        student.max_marks ?? student.total_marks ?? 100
    );

    marksValue.append(obtained, separator, maximum);
    marksPanel.append(marksInfo, marksValue);

    card.append(header, message, detailsHeading, details, marksPanel);
    output.appendChild(card);

    setHidden("#resultOutput", false);
}


function initResultSearch() {
    $("#resultForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();

        const roll = $("#rollNumber")?.value.trim();

        if (!roll) {
            setText("#resultMessage", "Please enter your roll number.");
            return;
        }

        setText("#resultMessage", "Searching for your result…");
        setHidden("#resultOutput", true);

        try {
            const result = await apiRequest(
                `/api/results/${encodeURIComponent(roll)}`
            );

            renderResult(result);
            setText("#resultMessage", "");
        } catch (error) {
            setText("#resultMessage", `Unable to find result: ${error.message}`);
        }
    });
}

// ---------- SYSTEM HEALTH ----------

function displayHealth(data) {
    const status = String(data.status || "unknown").toUpperCase();
    const dbStatus = String(
        data.database_status || data.database || "unknown"
    );

    setText("#healthLabel", status);
    setText("#adminHealth", status);
    setText("#healthStatusValue", status);
    setText("#adminDatabase", dbStatus);
    setText("#databaseStatusValue", dbStatus);
    setText("#connectionLabel", `API: ${status}`);

    const details = [
        `System status: ${status}`,
        `Database: ${dbStatus}`
    ];

    if (data.message) details.push(`Message: ${data.message}`);

    setText("#healthDetails", details.join("\n"));
    setText("#databaseDetails", `Database status: ${dbStatus}`);
    setText("#footerStatus", `System: ${status}`);
}

async function refreshHealth() {
    try {
        const data = await apiRequest("/api/health");
        displayHealth(data);
    } catch (error) {
        setText("#healthLabel", "UNAVAILABLE");
        setText("#adminHealth", "UNAVAILABLE");
        setText("#healthStatusValue", "UNAVAILABLE");
        setText("#connectionLabel", "API: OFFLINE");
        setText("#footerStatus", "API unavailable");
        setText("#healthDetails", error.message);
        setText("#databaseDetails", "Health check could not complete.");
    }
}

function initHealthButtons() {
    $("#refreshHealth")?.addEventListener("click", refreshHealth);
    $("#healthCheckButton")?.addEventListener("click", refreshHealth);
}

// ---------- ADMIN STUDENT MANAGEMENT ----------

function renderStudents(students) {
    const container = $("#studentRecords");
    if (!container) return;

    container.replaceChildren();

    if (!Array.isArray(students) || students.length === 0) {
        container.textContent = "No student records were returned.";
        return;
    }

    students.forEach((student) => {
        const card = document.createElement("div");
        card.className = "student-record";

        const details = document.createElement("div");
        details.className = "student-record-details";

        const name = document.createElement("strong");
        name.textContent = escapeText(
            student.student_name ?? student.name ?? "Unnamed student"
        );

        const info = document.createElement("p");
        info.textContent =
            `Roll: ${student.roll_number ?? student.roll ?? "—"} · ` +
            `Course: ${student.course ?? "—"} · ` +
            `Semester: ${student.semester ?? "—"} · ` +
            `Marks: ${student.marks ?? "—"}`;

        details.append(name, info);

        const actions = document.createElement("div");
        actions.className = "student-record-actions";

        const editButton = document.createElement("button");
        editButton.type = "button";
        editButton.textContent = "Edit";
        editButton.addEventListener("click", () => beginEditStudent(student));

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.textContent = "Delete";
        deleteButton.addEventListener("click", () => deleteStudent(student));

        actions.append(editButton, deleteButton);
        card.append(details, actions);
        container.appendChild(card);
    });
}

async function loadStudents() {
    if (!adminToken) return;

    try {
        const data = await apiRequest("/api/admin/students");
        const students = Array.isArray(data) ? data : data.students;

        renderStudents(students || []);
        setText("#adminStudentMessage", "");
    } catch (error) {
        setText(
            "#adminStudentMessage",
            `Could not load students: ${error.message}. Check the admin students API.`
        );
    }
}

function beginEditStudent(student) {
    if (!adminToken) return;

    editingStudent = true;

    $("#editStudentId").value = student.id ?? student.roll_number ?? student.roll ?? "";
    $("#studentRoll").value = student.roll_number ?? student.roll ?? "";
    $("#studentName").value = student.student_name ?? student.name ?? "";
    $("#studentCourse").value = student.course ?? "";
    $("#studentSemester").value = student.semester ?? "";
    $("#studentMarks").value = student.marks ?? "";

    const submit = $("#studentAdminForm")?.querySelector('[type="submit"]');
    if (submit) submit.textContent = "Update Student";

    setText("#adminStudentMessage", "Editing student record.");
    $("#studentName")?.focus();
}

function resetStudentForm() {
    $("#studentAdminForm")?.reset();

    if ($("#editStudentId")) $("#editStudentId").value = "";

    editingStudent = false;

    const submit = $("#studentAdminForm")?.querySelector('[type="submit"]');
    if (submit) submit.textContent = "Add Student";
}

function initStudentManagement() {
    $("#cancelEdit")?.addEventListener("click", resetStudentForm);

    $("#studentAdminForm")?.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!adminToken) {
            openLoginModal();
            return;
        }

        const student = {
            roll_number: $("#studentRoll")?.value.trim(),
            student_name: $("#studentName")?.value.trim(),
            course: $("#studentCourse")?.value.trim(),
            semester: Number($("#studentSemester")?.value),
            marks: Number($("#studentMarks")?.value)
        };

        if (
            !student.roll_number ||
            !student.student_name ||
            !student.course ||
            !Number.isFinite(student.semester) ||
            !Number.isFinite(student.marks)
        ) {
            setText("#adminStudentMessage", "Please fill all student fields correctly.");
            return;
        }

        const id = $("#editStudentId")?.value;
        const url = editingStudent
            ? `/api/admin/students/${encodeURIComponent(id)}`
            : "/api/admin/students";

        try {
            await apiRequest(url, {
                method: editingStudent ? "PUT" : "POST",
                body: JSON.stringify(student)
            });

            setText(
                "#adminStudentMessage",
                editingStudent ? "Student updated." : "Student added."
            );

            resetStudentForm();
            await loadStudents();
        } catch (error) {
            setText(
                "#adminStudentMessage",
                `Could not save student: ${error.message}. Check the backend route.`
            );
        }
    });
}

async function deleteStudent(student) {
    if (!adminToken) return;

    const id = student.id ?? student.roll_number ?? student.roll;

    if (id === undefined || id === null) {
        setText("#adminStudentMessage", "This record has no usable ID.");
        return;
    }

    if (!window.confirm("Delete this student record? This cannot be undone.")) {
        return;
    }

    try {
        await apiRequest(`/api/admin/students/${encodeURIComponent(id)}`, {
            method: "DELETE"
        });

        setText("#adminStudentMessage", "Student deleted.");
        await loadStudents();
    } catch (error) {
        setText(
            "#adminStudentMessage",
            `Could not delete student: ${error.message}. Check the backend route.`
        );
    }
}


 // ---------- INCIDENT CENTER ----------

function renderIncidents(data) {
    const incidents = Array.isArray(data)
        ? data
        : data.incidents || data.items || [];

    setText("#adminIncidentCount", String(incidents.length));

    // Update every incident list, even if HTML contains duplicate IDs.
    const containers = $$("#incidentList");

    containers.forEach((container) => {
        container.replaceChildren();

        if (incidents.length === 0) {
            container.textContent = "No incidents returned by the backend.";
            return;
        }

        incidents.forEach((incident) => {
            const card = document.createElement("div");
            card.className = "incident-card";

            const title = document.createElement("strong");
            title.textContent = escapeText(
                incident.title || incident.type || incident.name || "System incident"
            );

            const description = document.createElement("p");
            description.textContent = escapeText(
                incident.message || incident.description || incident.status ||
                "No additional details."
            );

            const meta = document.createElement("small");
            meta.textContent = escapeText(
                incident.timestamp || incident.created_at || incident.time || ""
            );

            card.append(title, description, meta);
            container.appendChild(card);
        });
    });
}

async function loadIncidents() {
    if (!adminToken) {
        openLoginModal();
        return;
    }

    $$("#incidentList").forEach((container) => {
        container.textContent = "Loading incidents...";
    });

    try {
        const data = await apiRequest("/api/self-healing/incidents");
        renderIncidents(data);
    } catch (error) {
        $$("#incidentList").forEach((container) => {
            container.textContent = `Could not load incidents: ${error.message}`;
        });
    }
}


function initIncidentButtons() {
    document.addEventListener("click", async (event) => {
        const button = event.target.closest("#refreshIncidents");

        if (!button || button.disabled) return;

        button.disabled = true;
        const originalText = button.textContent;
        button.textContent = "Refreshing...";

        try {
            await loadIncidents();
        } finally {
            button.disabled = false;
            button.textContent = originalText.trim() || "Refresh incidents";
        }
    });
}


// ---------- CHAOS LAB ----------

async function runChaosAction(action) {
    if (!adminToken) {
        openLoginModal();
        return;
    }

    const confirmation = window.confirm(
        `Run the "${action}" test? Only use this on your local development system.`
    );

    if (!confirmation) return;

    setText("#chaosMessage", `Running ${action} test…`);

    try {
        /*
         * This endpoint must be implemented and protected by the backend.
         * Do not expose destructive chaos tests to unauthenticated users.
         */
        const data = await apiRequest(
            `/api/self-healing/chaos/${encodeURIComponent(action)}`,
            { method: "POST" }
        );

        setText(
            "#chaosMessage",
            data.message || `${action} test request completed.`
        );

        await refreshHealth();
        await loadIncidents();
    } catch (error) {
        setText(
            "#chaosMessage",
            `Test unavailable: ${error.message}. Check the protected chaos API route.`
        );
    }
}

function initChaosLab() {
    $$(".chaos-action").forEach((button) => {
        button.addEventListener("click", () => {
            runChaosAction(button.dataset.chaos);
        });
    });
}

// ---------- FOOTER LINKS ----------

function initFooterLinks() {
    $("#footerHome")?.addEventListener("click", (event) => {
        event.preventDefault();
        showStudentPortal();
    });

    $("#homeLink")?.addEventListener("click", (event) => {
        event.preventDefault();
        showStudentPortal();
    });

    $("#footerStudentLink")?.addEventListener("click", (event) => {
        event.preventDefault();
        showStudentPortal();
    });

    $("#footerAdminLink")?.addEventListener("click", (event) => {
        event.preventDefault();
        openLoginModal();
    });

    $("#footerHealthLink")?.addEventListener("click", (event) => {
        event.preventDefault();
        if (!adminToken) return openLoginModal();
        showAdminWorkspace();
        openAdminView("health");
    });

    $("#footerIncidentLink")?.addEventListener("click", (event) => {
        event.preventDefault();
        if (!adminToken) return openLoginModal();
        showAdminWorkspace();
        openAdminView("incidents");
    });

    $("#footerChaosLink")?.addEventListener("click", (event) => {
        event.preventDefault();
        if (!adminToken) return openLoginModal();
        showAdminWorkspace();
        openAdminView("chaos");
    });
}

// ---------- INITIALIZE ----------

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initLogin();
    initAdminNavigation();
    initResultSearch();
    initHealthButtons();
    initStudentManagement();
    initIncidentButtons();
    initChaosLab();
    initFooterLinks();

    showStudentPortal();
    updateLoginButtons();
    refreshHealth();
});


async function handleRecovery(button) {
    if (!adminToken) {
        openLoginModal();
        return;
    }

    button.disabled = true;
    button.textContent = "Recovering...";

    try {
        const result = await apiRequest(
            "/api/self-healing/recover",
            { method: "POST" }
        );

        alert(result.message || "Recovery check completed.");

        await refreshHealth();
        await loadIncidents();
    } catch (error) {
        alert("Recovery failed: " + error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Recover System →";
    }
}

document.getElementById("recoverSystemButton")
    ?.addEventListener("click", function () {
        handleRecovery(this);
    });

document.getElementById("healthRecoverButton")
    ?.addEventListener("click", function () {
        handleRecovery(this);
    });
