const API_BASE = "http://127.0.0.1:8000";

const $ = (id) => document.getElementById(id);

function setText(id, value) {
    $(id).textContent = value;
}

function setService(id, healthy, onlineText = "Online") {
    const element = $(id);
    element.textContent = healthy ? onlineText : "Unavailable";
    element.style.color = healthy ? "var(--green)" : "var(--red)";
}

async function fetchHealth() {
    setText("healthStatus", "Checking services");
    setText("sidebarStatus", "Checking system...");

    try {
        const response = await fetch(`${API_BASE}/api/health`);

        if (!response.ok) {
            throw new Error("Health endpoint returned an error.");
        }

        const data = await response.json();

        const healthy = data.status === "healthy";
        const databaseConnected =
            data.database_status === "connected";

        setText("heroHealth", healthy ? "System Healthy" : "System Degraded");
        setText("healthStatus", healthy ? "All reported checks passed" : "System needs attention");
        setText(
            "healthDescription",
            healthy
                ? "The backend reports a healthy status."
                : "The backend reports a degraded status."
        );

        setText("databaseStatus", databaseConnected ? "Connected" : "Unavailable");
        setService("backendService", true);
        setService("databaseService", databaseConnected, "Connected");
        setService("monitorService", true, "Reachable");

        setText("sidebarStatus", healthy ? "System healthy" : "Attention needed");

        const heroHealth = $("heroHealth");
        heroHealth.style.color = healthy ? "var(--green)" : "var(--orange)";

        const indicator = document.querySelector(".status-dot");
        indicator.style.background = healthy ? "var(--green)" : "var(--orange)";

        $("healthStatus").style.color = healthy
            ? "var(--green)"
            : "var(--orange)";

    } catch (error) {
        setText("heroHealth", "Backend Offline");
        setText("healthStatus", "Backend unavailable");
        setText("healthDescription", "Start the Python backend and refresh the health check.");
        setText("databaseStatus", "Unknown");
        setText("sidebarStatus", "Backend unavailable");

        setService("backendService", false);
        setService("databaseService", false);
        setService("monitorService", false);

        $("heroHealth").style.color = "var(--red)";
        $("healthStatus").style.color = "var(--red)";

        console.error("Health check failed:", error);
    }
}

async function searchResult(event) {
    event.preventDefault();

    const rollNumber = $("rollNumber").value.trim();

    if (!rollNumber) {
        showResultMessage("Please enter a student roll number.", "error");
        return;
    }

    const button = $("searchButton");
    button.disabled = true;
    button.textContent = "Searching...";

    $("resultCard").classList.add("hidden");
    showResultMessage("Fetching result from the backend...", "");

    try {
        const response = await fetch(
            `${API_BASE}/api/results/${encodeURIComponent(rollNumber)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to find this result.");
        }

        const student = data.student;

        if (!student) {
            throw new Error("The backend did not return a student record.");
        }

        setText("resultName", student.name ?? "Unknown Student");
        setText("resultRoll", student.roll_number ?? rollNumber);
        setText("resultCourse", student.course ?? "—");
        setText("resultSemester", student.semester ?? "—");
        setText(
            "resultMarks",
            `${student.marks ?? 0} / ${student.max_marks ?? 100}`
        );

        setText("resultBadge", student.result ?? "Available");

        const marks = Number(student.marks ?? 0);
        const maxMarks = Number(student.max_marks ?? 100);

        const percentage =
            maxMarks > 0 ? Math.max(0, Math.min(100, (marks / maxMarks) * 100)) : 0;

        $("marksProgress").style.width = `${percentage}%`;
        setText("marksPercentage", `${percentage.toFixed(1)}%`);

        $("resultCard").classList.remove("hidden");
        showResultMessage("Result retrieved successfully.", "success");

    } catch (error) {
        showResultMessage(error.message, "error");
        console.error("Result search failed:", error);
    } finally {
        button.disabled = false;
        button.textContent = "Search →";
    }
}

function showResultMessage(message, type) {
    const element = $("resultMessage");
    element.textContent = message;
    element.className = `message ${type}`;
}

async function fetchIncidents() {
    const table = $("incidentTable");
    const message = $("incidentMessage");

    table.innerHTML = `
        <tr>
            <td colspan="4" class="empty-state">Loading incidents...</td>
        </tr>
    `;

    message.textContent = "Loading incident history...";
    message.className = "message";

    try {
        const response = await fetch(`${API_BASE}/api/self-healing/incidents`);

        if (!response.ok) {
            throw new Error("Incident history endpoint is not available.");
        }

        const data = await response.json();

        const incidents = Array.isArray(data)
            ? data
            : Array.isArray(data.incidents)
                ? data.incidents
                : [];

        setText("incidentCount", incidents.length);

        if (incidents.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="4" class="empty-state">
                        No incidents have been recorded yet.
                    </td>
                </tr>
            `;
            message.textContent = "Incident history loaded.";
            return;
        }

        table.replaceChildren();

        incidents.forEach((incident) => {
            const row = document.createElement("tr");

            const values = [
                incident.type ?? `Incident ${incident.id ?? ""}`,
                incident.message ?? "—",
                incident.timestamp ?? "—",
                incident.status ?? "Unknown"
            ];

            values.forEach((value, index) => {
                const cell = document.createElement("td");

                if (index === 3) {
                    const badge = document.createElement("span");
                    badge.className = "status-pill";
                    badge.textContent = String(value);
                    cell.appendChild(badge);
                } else {
                    cell.textContent = String(value);
                }

                row.appendChild(cell);
            });

            table.appendChild(row);
        });

        message.textContent = `${incidents.length} incident(s) loaded.`;

    } catch (error) {
        setText("incidentCount", "—");

        table.innerHTML = `
            <tr>
                <td colspan="4" class="empty-state">
                    Incident history is currently unavailable.
                </td>
            </tr>
        `;

        message.textContent =
            "Check the backend route before using incident history.";

        console.warn("Incident history unavailable:", error);
    }
}

$("resultForm").addEventListener("submit", searchResult);

$("refreshButton").addEventListener("click", async () => {
    await fetchHealth();
    await fetchIncidents();
});

$("healthButton").addEventListener("click", fetchHealth);
$("incidentRefresh").addEventListener("click", fetchIncidents);

fetchHealth();
fetchIncidents();