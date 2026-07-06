# Student Assignment Portal

A clean, modern, and responsive Django web application designed for students and faculty members to manage, submit, evaluate, and track academic assignments online.

## 🚀 Features

### Core Portals
*   **Role-Based Access:** Strict separation of student and faculty portals. Users can only log in through their designated login portals.
*   **Systems Administration:** Access to the Django Admin panel for root system management.

### Faculty Features
*   **Assignment Management:** Create assignments for specific subjects, set deadlines, and manage questions.
*   **Question Creator:** Support for multiple question types:
    *   Multiple Choice Questions (MCQ) with option validation.
    *   Short Answer (2-Mark) questions.
    *   Detailed (5-Mark) questions.
*   **Submissions Evaluation:** View list of student submissions, assign marks (0–10), and write textual review feedback.
*   **Performance Metrics:** View live analytical charts of submission statuses and assignment completions.
*   **Reports Export:** Download dynamic, formatted PDF reports of student submissions using ReportLab.

### Student Features
*   **Subject Enrollment:** Search and enroll in subjects handled by the department.
*   **Assignment Workflows:** 
    *   View all pending, in-progress, and completed assignments.
    *   Draft and save answers locally (*In Progress*).
    *   Submit answers before the due date (*Submitted*).
*   **Results Viewer:** View evaluations, read faculty feedback, and download PDF summaries of submitted answers.

---

## 🛠️ Technology Stack
*   **Backend Framework:** Django (Python)
*   **Frontend Design:** Semantic HTML5, CSS Variables (Custom Theme), Vanilla JavaScript
*   **Data Visualization:** Chart.js
*   **PDF Generation:** ReportLab
*   **Static Asset Handling:** WhiteNoise (configured for production)
*   **Database:** SQLite

---

## 💻 Local Installation & Setup

### Prerequisites
*   Python 3.10 or higher installed.
*   SQLite command-line tool (optional, for direct database queries).

### Setup Steps
1.  **Clone / Download the Repository:**
    ```bash
    cd Assignment_Portal
    ```

2.  **Install Required Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run Database Migrations:**
    ```bash
    python manage.py migrate
    ```

4.  **Create an Admin (Superuser) Account:**
    ```bash
    python manage.py createsuperuser
    ```

5.  **Start the Local Server:**
    ```bash
    python manage.py runserver
    ```
    Access the portal at `http://127.0.0.1:8000/`.

---

## ☁️ Deployment Guide (Render)

The codebase is pre-configured with the correct dependencies and scripts for hosting on Render.

### Render Configuration Settings:
*   **Environment / Language:** `Python`
*   **Branch:** `main` (or your active Git branch)
*   **Build Command:** 
    ```bash
    chmod +x build.sh && ./build.sh
    ```
*   **Start Command:**
    ```bash
    gunicorn assignment_portal.wsgi:application
    ```
*   **Instance Plan:** `Free`
