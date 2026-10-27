# 🛡️ ResultShield — The Self-Healing University Result Portal

**A university result management system exploring software reliability, health monitoring, incident tracking, and recovery workflows.**

ResultShield is a web-based project developed for **Identity 2026 — Third Year: Self-Healing Software**. It demonstrates how a university result portal can combine student result lookup, administrative record management, backend health checks, and failure-simulation workflows.

---

## 📌 Project Overview

University result portals should provide students with reliable access to their examination results. ResultShield explores ways to monitor application health, identify simulated failures, and organize incident-handling workflows.

The project combines a student-facing result portal with backend APIs and administrative functionality.

## ✨ Features

### 🎓 Student Result Portal

* Search for examination results using a roll number.
* Display student details, marks, and result status.
* Retrieve result information through backend APIs.

### 🔐 Admin Management

* Admin login endpoint.
* Student record management APIs.
* Add and update student records.
* Support for administrative operations.

### ❤️ Health Monitoring

* Backend health-check endpoint.
* Database connectivity status.
* JSON responses for checking application health.

### 🩺 Self-Healing Control Center

* Incident tracking endpoints.
* System status information.
* Recovery workflow endpoint.
* Failure-simulation endpoints for testing selected scenarios.

> **Note:** Some failure scenarios are simulated. The project is a learning prototype and does not claim complete autonomous recovery for every production failure.

---

## 🛠️ Tech Stack

| Technology   | Purpose                  |
| ------------ | ------------------------ |
| Python       | Backend programming      |
| FastAPI      | REST API development     |
| SQLite       | Database storage         |
| HTML         | Frontend structure       |
| CSS          | Styling and layout       |
| JavaScript   | Frontend interactions    |
| Uvicorn      | Local development server |
| Git & GitHub | Version control          |

---

## 📂 Project Structure

```text
resultshield/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── admin.py
│   │   │   ├── results.py
│   │   │   └── self_healing.py
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── main.py
│   ├── .env.example
│   ├── .gitignore
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .gitignore
└── README.md
```

---

## ⚙️ Getting Started

### Prerequisites

Install the following:

* Python 3.11
* Git
* A web browser
* Visual Studio Code (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/Dikshita1824/ResultShield-Self-Healing-Portal.git
cd ResultShield-Self-Healing-Portal
```

### 2. Set Up the Backend

Open a terminal inside the `backend` directory:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Start the Backend

From the `backend` directory, run:

```bash
python -m uvicorn app.main:app --reload
```

The backend should be available at:

* **API Base:** http://127.0.0.1:8000
* **Health Check:** http://127.0.0.1:8000/api/health
* **API Documentation:** http://127.0.0.1:8000/docs

### 4. Start the Frontend

Open a **second terminal** in the project's root directory:

```bash
cd frontend
python -m http.server 5500
```

Open the frontend in your browser:

http://127.0.0.1:5500

Keep both terminals running while testing the application.

---

## 🔌 API Endpoints

| Method | Endpoint                            | Purpose                                |
| ------ | ----------------------------------- | -------------------------------------- |
| GET    | `/api/health`                       | Check application health               |
| GET    | `/api/results/{roll_number}`        | Retrieve a student's result            |
| POST   | `/api/admin/login`                  | Admin authentication                   |
| GET    | `/api/admin/students`               | Retrieve student records               |
| POST   | `/api/admin/students`               | Add a student record                   |
| PUT    | `/api/admin/students/{roll_number}` | Update a student record                |
| GET    | `/api/self-healing/status`          | Check self-healing status              |
| GET    | `/api/self-healing/incidents`       | Retrieve incident information          |
| POST   | `/api/self-healing/chaos/{action}`  | Trigger a supported failure simulation |
| POST   | `/api/self-healing/recover`         | Trigger the recovery workflow          |
| POST   | `/api/self-healing/incidents/test`  | Test incident handling                 |

**Authentication:** Some administrative and self-healing endpoints require admin authentication. Refer to the API documentation for the expected request format.

---

## 🧪 Testing

You can test the API endpoints using the interactive Swagger UI:

http://127.0.0.1:8000/docs

The health-check endpoint can be used to verify that the application is responding and the database connection is available.

Example health-check response:

```json
{
  "status": "healthy",
  "database": "SQLite",
  "database_status": "connected"
}
```

The exact response may vary depending on the application's current state.

---

## 🔒 Security Notes

* Do not commit `.env` files, passwords, access tokens, or other secrets.
* Keep virtual environments and local database files out of version control.
* Use secure authentication and environment-based configuration before deploying publicly.
* This project is a prototype and should not be used to manage real student records without appropriate security, privacy, and reliability measures.

---

## 🚀 Future Improvements

* Automated service recovery and watchdog monitoring.
* More robust database-failure handling.
* Rate limiting and traffic-spike protection.
* Improved incident logs and recovery-time measurements.
* Expanded automated testing.
* Integration with monitoring and error-tracking tools such as Sentry.
* Deployment to a cloud hosting platform.

These are potential improvements and should not be considered implemented unless verified in the project.

---

## 🎯 Project Information

* **Project:** ResultShield — The Self-Healing University Result Portal
* **Event:** Identity 2026
* **Category:** Third Year — Self-Healing Software
* **Developer:** Dikshita Mittal
* **Purpose:** Educational project exploring reliable university result systems

---

## 👩‍💻 Author

**Dikshita Mittal**
BCA Student | Aspiring Software Developer

Built with curiosity, persistence, and a focus on learning through practical implementation.

---

⭐ If you find this project interesting, consider starring the repository!
