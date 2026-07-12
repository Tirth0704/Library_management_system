# LibraryHub 2.0 — Final Project Specification & File Structure

---

```markdown
# LibraryHub 2.0
### Smart Library Resource & Student Management Platform

> Author: Tirth Acharya
> Stack: Flask + MySQL + Bootstrap 5
> Status: Ready for Development

---

# Hardcoded Constants

| Rule                        | Value                     |
|-----------------------------|---------------------------|
| Rent                        | 10% of book price         |
| Late Fine                   | 5% of rent per day        |
| Loan Period                 | 14 days                   |
| Max Borrowed Books          | 3                         |
| Re-request After Rejection  | 24 hours                  |
| Initial Behaviour Score     | 100                       |
| Score Maximum               | 100                       |
| Score Minimum               | 0                         |

---

# Account Status

| Score Range | Label   |
|-------------|---------|
| 80 – 100    | Good    |
| 50 – 79     | Average |
| 0 – 49      | Bad     |

---

# Behaviour Score Rules

| Event                                        | Change   |
|----------------------------------------------|----------|
| Returned on time                             | +2       |
| Returned early                               | +3       |
| Returned late                                | -5       |
| Lost book                                    | -25      |
| Damaged book confirmed by librarian          | -20      |
| Damage fine added by librarian               | -5       |
| Cancelled approved request                   | -3       |
| Paid fine immediately                        | +2       |
| Librarian manual increase (score < 30)       | Variable |

---

# Fine & Payment Logic

## Rent
- Charged at the time of return always
- Rent = 10% of book price
- Student can pay rent early via dashboard before due date

## Late Fine
- Triggered only if book is returned after due date
- Fine Per Day = 5% of Rent
- Total Fine = Fine Per Day × Number of Overdue Days

## Lost Book
- Student pays full book price
- No rent charged
- No per day fine
- Behaviour score -25

## Damaged Book
- Student pays rent + variable damage fine set by librarian
- Behaviour score -20 for damage
- Behaviour score -5 for damage fine being applied

## Payment Methods
- Online: Razorpay (UPI, Card, Net Banking)
- Offline: Cash (Librarian clicks Paid Offline button)

## Receipt
- PDF receipt downloadable after payment

---

# User Roles

## Student
- Self registration (no approval needed)
- Can search books by name or author (live search)
- Can request books (max 3 at a time)
- Can cancel pending requests
- Can pay rent early via dashboard
- Can pay fines via Razorpay or cash
- Can submit book recommendations
- Can view issued books, history, fines, payments
- Can view behaviour score and account status
- Can update own profile (including semester)

## Librarian
- Single hardcoded account
- Email: admin.lms@gmail.com
- Password: admin@#$123
- Full control over all library operations

---

# Student Profile Fields

| Field             | Type     | Notes                          |
|-------------------|----------|--------------------------------|
| Student ID        | INT      | Auto generated primary key     |
| Enrollment Number | VARCHAR  | Typed by student               |
| Full Name         | VARCHAR  |                                |
| Department        | VARCHAR  | Dropdown                       |
| Semester          | VARCHAR  | Dropdown, student updates self |
| Email             | VARCHAR  | Unique                         |
| Phone Number      | VARCHAR  | Also used as WhatsApp number   |
| Password          | VARCHAR  | Hashed via Werkzeug            |
| Behaviour Score   | INT      | Starts at 100                  |
| Account Status    | VARCHAR  | Good / Average / Bad           |
| Joining Date      | DATE     | Auto set on registration       |

---

# Book Fields

| Field           | Type     | Notes                        |
|-----------------|----------|------------------------------|
| Book ID         | INT      | Auto generated primary key   |
| Title           | VARCHAR  |                              |
| Author          | VARCHAR  |                              |
| Publisher       | VARCHAR  |                              |
| Price           | DECIMAL  | Used for rent and fine calc  |
| Total Copies    | INT      |                              |
| Available Copies| INT      | Auto managed                 |
| Issued Copies   | INT      | Auto managed                 |
| Category        | INT      | Foreign key to categories    |
| Added Date      | DATE     | Auto set                     |
| Status          | VARCHAR  | Available / Unavailable      |

---

# Book Request Workflow

Student requests book
↓
Status: Pending
↓
Librarian reviews
↓
Approve → Book handed to student physically
          Librarian enters issue date
          Due date = Issue date + 14 days
          Status: Issued

Reject  → Reason recorded
          Student notified (WhatsApp + in-app)
          Student can re-request after 24 hours

Hold    → Student has unpaid fine
          Stays on hold until fine is cleared

---

# Book Return Workflow

Student brings book to library desk
↓
Librarian opens student issued books
↓
Selects the book being returned
↓
System checks: returned late?
  Yes → System calculates fine automatically
  No  → No fine
↓
Librarian checks: damaged?
  Yes → Librarian enters damage fine (variable amount)
↓
Student reported lost?
  Yes → System adds full book price as payment
↓
Total due shown to librarian
↓
Student pays (Razorpay or cash)
↓
Librarian marks paid offline if cash
↓
Return completed
↓
Behaviour score updated
↓
Receipt available for student

---

# WhatsApp Notification Events

| Event                    | Trigger                                  |
|--------------------------|------------------------------------------|
| Request Approved         | Librarian approves request               |
| Request Rejected         | Librarian rejects request (with reason)  |
| Due Date Reminder        | 1 day before due date (scheduled task)   |
| Overdue Notice           | First day after due date (one time only) |
| Fine Payment Confirmed   | Payment successfully recorded            |

- Provider: Twilio WhatsApp API
- No retry on failure
- Mandatory for all students
- Phone number is used as WhatsApp number

---

# Student Recommendation Flow

Student submits form:
  Book Name (required)
  Author (required)
  Publisher (optional)
  Reason (optional)
↓
Librarian sees Pending Recommendations list
↓
Librarian adds to library OR rejects
↓
Student receives in-app notification of outcome

---

# Newly Added Books

- Shown on student dashboard
- Books sorted by date added (most recent first)
- No personalization

---

# Database Tables

| Table                | Purpose                                      |
|----------------------|----------------------------------------------|
| students             | Student accounts and profile data            |
| books                | Book inventory                               |
| categories           | Flat category list                           |
| book_requests        | All book requests with status                |
| book_issues          | Active and completed book issues             |
| book_returns         | Return records                               |
| fines                | Fine records linked to issues                |
| payments             | Payment records                              |
| behaviour_logs       | Every score change with reason               |
| notifications        | In-app notifications                         |
| whatsapp_logs        | WhatsApp message delivery records            |
| book_recommendations | Student submitted book recommendations       |
| activity_logs        | General activity trail for librarian view    |

---

# Technology Stack

| Layer          | Technology                        |
|----------------|-----------------------------------|
| Frontend       | HTML5, CSS3, Bootstrap 5, JS      |
| Backend        | Python, Flask                     |
| Database       | MySQL                             |
| ORM            | SQLAlchemy                        |
| Auth           | Flask-Login, Werkzeug             |
| Payments       | Razorpay Python SDK               |
| WhatsApp       | Twilio Python SDK                 |
| Scheduler      | APScheduler                       |
| PDF Generation | ReportLab                         |
| Charts         | Chart.js                          |
| Templating     | Jinja2                            |

---

# Security

- Passwords hashed with Werkzeug
- CSRF protection on all forms
- Role based access (student vs librarian)
- Input validation on all forms
- Secure session management
- SQL injection prevention via SQLAlchemy ORM
```

---

# Project File Structure

```
libraryhub/
│
├── run.py
├── config.py
├── requirements.txt
├── .env
├── .gitignore
│
├── app/
│   │
│   ├── __init__.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── student.py
│   │   ├── book.py
│   │   ├── category.py
│   │   ├── request.py
│   │   ├── issue.py
│   │   ├── return_.py
│   │   ├── fine.py
│   │   ├── payment.py
│   │   ├── behaviour_log.py
│   │   ├── notification.py
│   │   ├── whatsapp_log.py
│   │   ├── recommendation.py
│   │   └── activity_log.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── student.py
│   │   ├── books.py
│   │   ├── requests.py
│   │   ├── payments.py
│   │   ├── notifications.py
│   │   ├── recommendations.py
│   │   └── librarian/
│   │       ├── __init__.py
│   │       ├── dashboard.py
│   │       ├── books.py
│   │       ├── categories.py
│   │       ├── requests.py
│   │       ├── issues.py
│   │       ├── returns.py
│   │       ├── students.py
│   │       ├── payments.py
│   │       ├── recommendations.py
│   │       └── notifications.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── fine_service.py
│   │   ├── payment_service.py
│   │   ├── behaviour_service.py
│   │   ├── whatsapp_service.py
│   │   ├── scheduler_service.py
│   │   ├── receipt_service.py
│   │   └── notification_service.py
│   │
│   ├── forms/
│   │   ├── __init__.py
│   │   ├── auth_forms.py
│   │   ├── student_forms.py
│   │   ├── book_forms.py
│   │   ├── request_forms.py
│   │   ├── return_forms.py
│   │   ├── payment_forms.py
│   │   └── recommendation_forms.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   │
│   │   ├── student/
│   │   │   ├── dashboard.html
│   │   │   ├── profile.html
│   │   │   ├── books.html
│   │   │   ├── book_detail.html
│   │   │   ├── my_requests.html
│   │   │   ├── my_books.html
│   │   │   ├── my_history.html
│   │   │   ├── my_fines.html
│   │   │   ├── pay_fine.html
│   │   │   ├── receipts.html
│   │   │   ├── recommendations.html
│   │   │   └── notifications.html
│   │   │
│   │   └── librarian/
│   │       ├── dashboard.html
│   │       ├── books/
│   │       │   ├── list.html
│   │       │   ├── add.html
│   │       │   └── edit.html
│   │       ├── categories/
│   │       │   └── list.html
│   │       ├── requests/
│   │       │   └── list.html
│   │       ├── issues/
│   │       │   └── list.html
│   │       ├── returns/
│   │       │   └── process.html
│   │       ├── students/
│   │       │   ├── list.html
│   │       │   └── detail.html
│   │       ├── payments/
│   │       │   └── list.html
│   │       ├── recommendations/
│   │       │   └── list.html
│   │       └── notifications/
│   │           └── list.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   ├── student.css
│   │   │   └── librarian.css
│   │   ├── js/
│   │   │   ├── main.js
│   │   │   ├── search.js
│   │   │   ├── payment.js
│   │   │   └── charts.js
│   │   ├── img/
│   │   │   └── logo.png
│   │   └── receipts/
│   │       └── .gitkeep
│   │
│   └── utils/
│       ├── __init__.py
│       ├── decorators.py
│       ├── helpers.py
│       └── validators.py
│
└── migrations/
    └── schema.sql
```

---

# File Responsibilities

```
run.py
  Entry point of the application
  Creates Flask app and starts server

config.py
  All configuration variables
  Database URL
  Secret key
  Razorpay keys
  Twilio credentials
  All loaded from .env

.env
  SECRET_KEY
  DATABASE_URL
  RAZORPAY_KEY_ID
  RAZORPAY_KEY_SECRET
  TWILIO_ACCOUNT_SID
  TWILIO_AUTH_TOKEN
  TWILIO_WHATSAPP_NUMBER

app/__init__.py
  Creates Flask app instance
  Initializes SQLAlchemy
  Initializes Flask-Login
  Registers all blueprints
  Starts APScheduler

models/
  One file per database table
  Each file contains the SQLAlchemy model class

routes/
  One file per feature area
  Student routes handle student-facing pages
  Librarian routes handle librarian-facing pages
  Each route file is a Flask Blueprint

services/
  fine_service.py       → Calculates rent, late fine, lost fine
  payment_service.py    → Razorpay integration
  behaviour_service.py  → Score update logic
  whatsapp_service.py   → Twilio message sending
  scheduler_service.py  → APScheduler daily tasks
  receipt_service.py    → PDF generation via ReportLab
  notification_service  → In-app notification creation

forms/
  WTForms classes for all input forms
  Includes CSRF protection automatically

utils/
  decorators.py   → @student_required @librarian_required
  helpers.py      → Common helper functions
  validators.py   → Custom input validators

templates/
  base.html is the shared layout
  student/ contains all student pages
  librarian/ contains all librarian pages
  All use Jinja2 templating

static/
  css/      → Stylesheets
  js/       → JavaScript files including Chart.js and live search
  img/      → Static images
  receipts/ → Generated PDF receipts stored here

migrations/
  schema.sql contains the complete MySQL database schema
```

---

# URL Map

```
Authentication
  GET  POST  /login
  GET  POST  /register
  GET        /logout

Student
  GET        /dashboard
  GET        /profile
  GET  POST  /profile/edit
  GET        /books
  GET        /books/<id>
  POST       /books/<id>/request
  POST       /requests/<id>/cancel
  GET        /my-requests
  GET        /my-books
  GET        /my-history
  GET        /my-fines
  GET        /pay/<fine_id>
  POST       /pay/<fine_id>/razorpay
  GET        /receipts
  GET        /receipts/<payment_id>/download
  GET  POST  /recommendations
  GET        /notifications

Librarian
  GET        /librarian/dashboard
  GET        /librarian/books
  GET  POST  /librarian/books/add
  GET  POST  /librarian/books/edit/<id>
  POST       /librarian/books/delete/<id>
  GET        /librarian/categories
  POST       /librarian/categories/add
  POST       /librarian/categories/delete/<id>
  GET        /librarian/requests
  POST       /librarian/requests/<id>/approve
  POST       /librarian/requests/<id>/reject
  POST       /librarian/requests/<id>/hold
  GET        /librarian/issues
  GET        /librarian/returns
  GET        /librarian/returns/<issue_id>
  POST       /librarian/returns/<issue_id>/complete
  GET        /librarian/students
  GET        /librarian/students/<id>
  POST       /librarian/students/<id>/score
  GET        /librarian/payments
  POST       /librarian/payments/<id>/mark-offline
  GET        /librarian/recommendations
  POST       /librarian/recommendations/<id>/approve
  POST       /librarian/recommendations/<id>/reject
  GET        /librarian/notifications
```

---

This is your complete project definition and file structure.

Everything is defined. Zero open questions remain. Ready to start coding whenever you are.

Email:    admin.lms@gmail.com
Password: admin@#$123