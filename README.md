# LibraryHub 2.0 📚

> **Smart Library Resource & Student Management Platform**
> A modern web-based library management system built with Flask, MySQL/MariaDB, and Bootstrap 5, featuring real-time live search, automated behaviour score tracking, automated WhatsApp notifications, and payment integration.

---

## 🌟 Key Features

### 👨‍🎓 Student Dashboard
- **Self-Registration:** Dynamic signup displaying the WhatsApp Sandbox connection instructions and QR code.
- **Book Catalog:** Live-searchable book list by title or author.
- **Request Workflow:** Request up to 3 books at a time with instant status feedback.
- **Financial Desk:** Pay early book rents or outstanding late/damage fines online via **Razorpay** checkout.
- **PDF Receipts:** Download computer-generated PDF receipts for all successful transactions.
- **Behaviour Score Tracker:** Real-time visibility into behaviour score changes (ranging from 0 to 100) and status classifications (`Good`, `Average`, `Bad`).
- **Book Recommendations:** Submit acquisition recommendations to the librarian.

### 🛡️ Librarian Dashboard
- **Central Analytics:** Quick overview metrics of total students, active issues, overdue loans, and unpaid fines.
- **Catalog Management:** Create, edit, and delete books and genres/categories.
- **Review Desk:** Approve, hold, or reject student book requests with detailed logging.
- **Return Processing Desk:** Log returned books with options for return conditions (`Good`, `Damaged`, `Lost`). Fine calculation is automated.
- **Fines & Logs:** Manual score adjustment capabilities and delivery logs for in-app and WhatsApp notifications.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript (vanilla) |
| **Backend** | Python 3.11+ / Flask |
| **Database** | MySQL / MariaDB (pymysql dialect) |
| **ORM** | SQLAlchemy |
| **Authentication** | Flask-Login & Werkzeug hashing |
| **Payments** | Razorpay Python SDK |
| **WhatsApp Integration** | Twilio Python SDK |
| **Scheduler** | APScheduler (runs background cron jobs) |
| **PDF Generation** | ReportLab |

---

## 📋 Environment Configuration

Create a `.env` file in the root directory and configure the following variables:

```ini
# Flask Core Configuration
SECRET_KEY=your_secure_random_string_here
FLASK_ENV=development
FLASK_DEBUG=1

# Database Configuration (MySQL / MariaDB)
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/libraryhub

# Razorpay API Credentials
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Twilio WhatsApp Sandbox Credentials
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

---

## 🚀 Installation & Setup

Follow these steps to run the application locally:

### 1. Install Dependencies
Ensure you have Python 3.11 or later installed. Install the required python packages:
```bash
pip install -r requirements.txt
```

### 2. Start Database Server
Ensure your MySQL/MariaDB server is running (e.g., via the XAMPP Control Panel or local MySQL service) on port 3306. Create a blank database named `libraryhub` in your server:
```sql
CREATE DATABASE libraryhub;
```

### 3. Initialize Database Tables
Run the Flask application once or run the SQL schema file to set up all required tables:
```bash
# If using MySQL CLI:
mysql -u root -p libraryhub < migrations/schema.sql
```

### 4. Run the Application
Start the Flask development server:
```bash
python run.py
```
Open `http://localhost:5000` in your web browser.

---

## 💬 WhatsApp Integration & Sandbox Setup

All students receive automated library notifications on WhatsApp. 

### 1. Connect to Twilio Sandbox
Before registering a student account, the student must connect their phone to the Twilio sandbox:
1. Scan the QR code shown on the registration page (`http://localhost:5000/register`).
2. Alternatively, add the number **`+1 415 523 8886`** to your phone's contacts.
3. Send a WhatsApp message containing the text: **`join wherever-according`**.

### 2. Trigger Events
The following actions trigger real-time WhatsApp notifications:
- **Request Approval:** Sent when the librarian approves a book request.
- **Request Rejection:** Sent when the librarian rejects a request (includes the rejection reason).
- **Book Return:** Sent when the librarian processes a returned book (shows condition and outstanding fines).
- **Payment Receipt PDF:** Sent when a student successfully pays a fine or rent. The PDF receipt is attached directly to the WhatsApp message as media.
- **Due Date Reminders (Background):** Runs daily at **09:00 IST** to notify students with books due tomorrow.
- **Overdue Alerts (Background):** Runs daily at **09:30 IST** to notify students on the first day a book becomes overdue (only sent once).

---

## 🧪 Testing WhatsApp Notifications
To manually test the WhatsApp integration without executing database workflows:
1. Run the test script in your terminal:
   ```bash
   python test_whatsapp.py
   ```
2. Select a registered student or enter a custom mobile number to test the connection.
