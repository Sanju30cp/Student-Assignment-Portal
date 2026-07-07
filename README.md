# 🎓 Student Assignment Portal

A full-stack Django web application that streamlines assignment management between faculty and students. The portal allows instructors to create assignments, evaluate submissions, and manage subjects, while students can submit assignments and track their academic progress.

## 🌐 Live Demo

**Website:** https://saroja307.pythonanywhere.com/

---

## 🚀 Features

### 👨‍🏫 Faculty

- Faculty Registration & Login
- Faculty Dashboard
- Create Subjects
- Create Assignments
- Upload Questions
- View Student Submissions
- Evaluate Assignments
- Assign Marks
- Manage Student Records

### 👨‍🎓 Student

- Student Registration & Login
- Student Dashboard
- View Available Subjects
- View Assignments
- Submit Assignments
- Track Submission Status
- View Evaluation Results

### 🔐 Authentication

- Secure Login
- Logout
- Role-based Access
- Session Management

---

## 🛠️ Tech Stack

### Backend

- Django
- Python

### Frontend

- HTML5
- CSS3
- Django Templates

### Database

- SQLite3

### Deployment

- PythonAnywhere

---

## 📂 Project Structure

```
Student-Assignment-Portal/
│
├── assignment_portal/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── portal/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── admin.py
│
├── templates/
│
├── static/
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/Sanju30cp/Student-Assignment-Portal.git
```

Move into the project folder

```bash
cd Student-Assignment-Portal
```

Create a virtual environment

```bash
python -m venv venv
```

Activate the virtual environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Apply migrations

```bash
python manage.py migrate
```

Collect static files

```bash
python manage.py collectstatic
```

Run the development server

```bash
python manage.py runserver
```

Visit

```
http://127.0.0.1:8000/
```

---

## 📸 Screenshots

You can add screenshots here.

### Home Page

```
screenshots/home.png
```

### Faculty Dashboard

```
screenshots/faculty-dashboard.png
```

### Student Dashboard

```
screenshots/student-dashboard.png
```

### Assignment Submission

```
screenshots/submission.png
```

---

## 📦 Requirements

- Python 3.10+
- Django 5.x
- SQLite3

---

## 👨‍💻 Author

**Sanju**

GitHub:
https://github.com/Sanju30cp

---

## Future Improvements

- Email Notifications
- Assignment Deadlines
- File Upload Validation
- PDF Report Generation
- Admin Analytics Dashboard
- PostgreSQL Support
- Docker Deployment
- REST API Integration

---

## License

This project is developed for educational purposes.
