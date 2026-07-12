-- ============================================================================
-- LibraryHub 2.0 — Complete MySQL Schema
-- ----------------------------------------------------------------------------
-- Author       : Tirth Acharya
-- Database     : libraryhub
-- Engine       : InnoDB (for FK constraints + transactions)
-- Charset      : utf8mb4 (full Unicode support)
-- Collation    : utf8mb4_unicode_ci
-- ----------------------------------------------------------------------------
-- Notes:
--   - This schema is auto-created by SQLAlchemy via db.create_all() at boot.
--   - This file serves as a reference / manual bootstrap option.
--   - Run this file when setting up on a fresh MySQL server:
--       mysql -u root -p < migrations/schema.sql
--   - Foreign keys use ON DELETE CASCADE where child rows must not orphan,
--     and ON DELETE SET NULL where the relationship is optional.
-- ============================================================================

-- ─── Database Creation ─────────────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS libraryhub
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE libraryhub;

-- Disable FK checks during table creation
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tables in reverse dependency order (safe re-run)
DROP TABLE IF EXISTS activity_logs;
DROP TABLE IF EXISTS whatsapp_logs;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS behaviour_logs;
DROP TABLE IF EXISTS book_recommendations;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS fines;
DROP TABLE IF EXISTS book_returns;
DROP TABLE IF EXISTS book_issues;
DROP TABLE IF EXISTS book_requests;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS students;

SET FOREIGN_KEY_CHECKS = 1;


-- ============================================================================
-- 1. STUDENTS
-- ----------------------------------------------------------------------------
-- Represents a registered student account.
-- Behaviour score starts at 100; account status derived from score.
-- Phone number doubles as WhatsApp contact number.
-- ============================================================================
CREATE TABLE students (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_number   VARCHAR(50)  NOT NULL,
    full_name           VARCHAR(150) NOT NULL,
    email               VARCHAR(150) NOT NULL UNIQUE,
    phone_number        VARCHAR(15)  NOT NULL,
    password_hash       VARCHAR(256) NOT NULL,

    department          VARCHAR(100) NOT NULL,
    semester            VARCHAR(20)  NOT NULL,

    behaviour_score     INT          NOT NULL DEFAULT 100,
    account_status      VARCHAR(20)  NOT NULL DEFAULT 'Good',

    joining_date        DATE         NOT NULL,
    created_at          DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_students_email        (email),
    INDEX idx_students_enrollment   (enrollment_number),
    INDEX idx_students_status       (account_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 2. CATEGORIES
-- ----------------------------------------------------------------------------
-- Flat list of book categories.
-- Each book belongs to one category (FK on books table).
-- ============================================================================
CREATE TABLE categories (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL UNIQUE,
    description  VARCHAR(255) DEFAULT NULL,
    created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 3. BOOKS
-- ----------------------------------------------------------------------------
-- Represents a book in the library inventory.
-- Rent = 10% of price, Late fine per day = 5% of rent (computed in app).
-- ============================================================================
CREATE TABLE books (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    title               VARCHAR(255)  NOT NULL,
    author              VARCHAR(150)  NOT NULL,
    publisher           VARCHAR(150)  DEFAULT NULL,
    price               DECIMAL(10,2) NOT NULL,

    total_copies        INT          NOT NULL DEFAULT 1,
    available_copies    INT          NOT NULL DEFAULT 1,
    issued_copies       INT          NOT NULL DEFAULT 0,

    category_id         INT          DEFAULT NULL,

    status              VARCHAR(20)  NOT NULL DEFAULT 'Available',
    added_date          DATE         NOT NULL,
    created_at          DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_books_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE SET NULL,

    INDEX idx_books_title    (title),
    INDEX idx_books_author   (author),
    INDEX idx_books_category (category_id),
    INDEX idx_books_status   (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 4. BOOK_REQUESTS
-- ----------------------------------------------------------------------------
-- Tracks every book request made by a student.
-- Status: Pending / Approved / Rejected / Hold / Cancelled
-- rejected_at is used to enforce 24-hour re-request rule.
-- ============================================================================
CREATE TABLE book_requests (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    student_id          INT          NOT NULL,
    book_id             INT          NOT NULL,

    status              VARCHAR(20)  NOT NULL DEFAULT 'Pending',
    rejection_reason    TEXT         DEFAULT NULL,
    rejected_at         DATETIME     DEFAULT NULL,

    requested_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_requests_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_requests_book
        FOREIGN KEY (book_id)
        REFERENCES books(id)
        ON DELETE CASCADE,

    INDEX idx_requests_student  (student_id),
    INDEX idx_requests_book     (book_id),
    INDEX idx_requests_status   (status),
    INDEX idx_requests_rejected (rejected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 5. BOOK_ISSUES
-- ----------------------------------------------------------------------------
-- Created when librarian physically hands a book to a student.
-- due_date = issue_date + 14 days (LOAN_PERIOD_DAYS constant).
-- ============================================================================
CREATE TABLE book_issues (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    student_id     INT          NOT NULL,
    book_id        INT          NOT NULL,
    request_id     INT          DEFAULT NULL,

    issue_date     DATE         NOT NULL,
    due_date       DATE         NOT NULL,
    return_date    DATE         DEFAULT NULL,

    is_returned    BOOLEAN      NOT NULL DEFAULT FALSE,
    is_lost        BOOLEAN      NOT NULL DEFAULT FALSE,

    status         VARCHAR(20)  NOT NULL DEFAULT 'Issued',

    created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME     DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_issues_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_issues_book
        FOREIGN KEY (book_id)
        REFERENCES books(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_issues_request
        FOREIGN KEY (request_id)
        REFERENCES book_requests(id)
        ON DELETE SET NULL,

    INDEX idx_issues_student    (student_id),
    INDEX idx_issues_book       (book_id),
    INDEX idx_issues_status     (status),
    INDEX idx_issues_due_date   (due_date),
    INDEX idx_issues_returned   (is_returned)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 6. BOOK_RETURNS
-- ----------------------------------------------------------------------------
-- Records a completed book return transaction.
-- One-to-one with book_issues (UNIQUE on issue_id).
-- condition: Good / Damaged / Lost
-- ============================================================================
CREATE TABLE book_returns (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    issue_id          INT          NOT NULL UNIQUE,
    student_id        INT          NOT NULL,
    book_id           INT          NOT NULL,

    return_date       DATE         NOT NULL,
    condition         VARCHAR(20)  NOT NULL DEFAULT 'Good',

    rent_charged      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    late_fine         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    damage_fine       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    lost_amount       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_due         DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    librarian_notes   TEXT         DEFAULT NULL,

    created_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_returns_issue
        FOREIGN KEY (issue_id)
        REFERENCES book_issues(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_returns_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_returns_book
        FOREIGN KEY (book_id)
        REFERENCES books(id)
        ON DELETE CASCADE,

    INDEX idx_returns_student   (student_id),
    INDEX idx_returns_book      (book_id),
    INDEX idx_returns_date      (return_date),
    INDEX idx_returns_condition (`condition`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 7. FINES
-- ----------------------------------------------------------------------------
-- Tracks all fine records linked to book issues.
-- fine_type: rent / late / damage / lost
-- status: Unpaid / Paid
-- ============================================================================
CREATE TABLE fines (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    student_id   INT           NOT NULL,
    issue_id     INT           NOT NULL,

    fine_type    VARCHAR(20)   NOT NULL,
    amount       DECIMAL(10,2) NOT NULL,
    description  VARCHAR(255)  DEFAULT NULL,

    status       VARCHAR(20)   NOT NULL DEFAULT 'Unpaid',

    created_at   DATETIME      DEFAULT CURRENT_TIMESTAMP,
    paid_at      DATETIME      DEFAULT NULL,

    CONSTRAINT fk_fines_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_fines_issue
        FOREIGN KEY (issue_id)
        REFERENCES book_issues(id)
        ON DELETE CASCADE,

    INDEX idx_fines_student    (student_id),
    INDEX idx_fines_issue      (issue_id),
    INDEX idx_fines_type       (fine_type),
    INDEX idx_fines_status     (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 8. PAYMENTS
-- ----------------------------------------------------------------------------
-- Records every payment made by a student.
-- payment_method: razorpay / cash
-- status: Pending / Completed / Failed
-- One-to-one with fines via fine_id.
-- ============================================================================
CREATE TABLE payments (
    id                       INT AUTO_INCREMENT PRIMARY KEY,
    student_id               INT           NOT NULL,
    fine_id                  INT           DEFAULT NULL,

    amount                   DECIMAL(10,2) NOT NULL,
    payment_method           VARCHAR(20)   NOT NULL,
    status                   VARCHAR(20)   NOT NULL DEFAULT 'Pending',

    razorpay_order_id        VARCHAR(100)  DEFAULT NULL,
    razorpay_payment_id      VARCHAR(100)  DEFAULT NULL,
    razorpay_signature       VARCHAR(255)  DEFAULT NULL,

    receipt_path             VARCHAR(255)  DEFAULT NULL,

    created_at               DATETIME      DEFAULT CURRENT_TIMESTAMP,
    completed_at             DATETIME      DEFAULT NULL,

    CONSTRAINT fk_payments_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_payments_fine
        FOREIGN KEY (fine_id)
        REFERENCES fines(id)
        ON DELETE SET NULL,

    INDEX idx_payments_student    (student_id),
    INDEX idx_payments_fine       (fine_id),
    INDEX idx_payments_method     (payment_method),
    INDEX idx_payments_status     (status),
    INDEX idx_payments_razorpay   (razorpay_payment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 9. BEHAVIOUR_LOGS
-- ----------------------------------------------------------------------------
-- Immutable audit log of every behaviour score change.
-- score_before + score_change = score_after (clamped 0-100 in app layer).
-- ============================================================================
CREATE TABLE behaviour_logs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    student_id    INT           NOT NULL,

    score_before  INT           NOT NULL,
    score_change  INT           NOT NULL,
    score_after   INT           NOT NULL,

    event_type    VARCHAR(50)   NOT NULL,
    description   VARCHAR(255)  DEFAULT NULL,

    created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_behaviour_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    INDEX idx_behaviour_student  (student_id),
    INDEX idx_behaviour_event    (event_type),
    INDEX idx_behaviour_created  (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 10. NOTIFICATIONS
-- ----------------------------------------------------------------------------
-- In-app notifications sent to students.
-- Types: request_approved, request_rejected, due_reminder, overdue_notice,
--        fine_paid, recommendation_approved, recommendation_rejected, general
-- ============================================================================
CREATE TABLE notifications (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    student_id          INT           NOT NULL,

    notification_type   VARCHAR(50)   NOT NULL,
    title               VARCHAR(150)  NOT NULL,
    message             TEXT          NOT NULL,

    is_read             BOOLEAN       NOT NULL DEFAULT FALSE,

    created_at          DATETIME      DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notifications_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    INDEX idx_notif_student  (student_id),
    INDEX idx_notif_type     (notification_type),
    INDEX idx_notif_read     (is_read),
    INDEX idx_notif_created  (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 11. WHATSAPP_LOGS
-- ----------------------------------------------------------------------------
-- Records every WhatsApp message attempted via Twilio.
-- status: sent / failed (no retry on failure as per spec).
-- ============================================================================
CREATE TABLE whatsapp_logs (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    student_id     INT           NOT NULL,

    event_type     VARCHAR(50)   NOT NULL,
    to_number      VARCHAR(20)   NOT NULL,
    message_body   TEXT          NOT NULL,

    status         VARCHAR(20)   NOT NULL DEFAULT 'sent',
    twilio_sid     VARCHAR(100)  DEFAULT NULL,
    error_message  TEXT          DEFAULT NULL,

    created_at     DATETIME      DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_whatsapp_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    INDEX idx_whatsapp_student  (student_id),
    INDEX idx_whatsapp_event    (event_type),
    INDEX idx_whatsapp_status   (status),
    INDEX idx_whatsapp_created  (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 12. BOOK_RECOMMENDATIONS
-- ----------------------------------------------------------------------------
-- Student-submitted book recommendations.
-- status: Pending / Approved / Rejected
-- ============================================================================
CREATE TABLE book_recommendations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT           NOT NULL,

    book_name       VARCHAR(255)  NOT NULL,
    author          VARCHAR(150)  NOT NULL,
    publisher       VARCHAR(150)  DEFAULT NULL,
    reason          TEXT          DEFAULT NULL,

    status          VARCHAR(20)   NOT NULL DEFAULT 'Pending',
    librarian_note  VARCHAR(255)  DEFAULT NULL,

    submitted_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    reviewed_at     DATETIME      DEFAULT NULL,

    CONSTRAINT fk_recommendations_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    INDEX idx_recom_student  (student_id),
    INDEX idx_recom_status   (status),
    INDEX idx_recom_created  (submitted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 13. ACTIVITY_LOGS
-- ----------------------------------------------------------------------------
-- General activity trail for librarian audit view.
-- actor_type: student / librarian
-- ============================================================================
CREATE TABLE activity_logs (
    id            INT AUTO_INCREMENT PRIMARY KEY,

    actor_type    VARCHAR(20)   NOT NULL,
    actor_id      INT           DEFAULT NULL,

    entity_type   VARCHAR(50)   DEFAULT NULL,
    entity_id     INT           DEFAULT NULL,

    action        VARCHAR(100)  NOT NULL,
    description   TEXT          DEFAULT NULL,

    created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_activity_actor      (actor_type, actor_id),
    INDEX idx_activity_entity     (entity_type, entity_id),
    INDEX idx_activity_action     (action),
    INDEX idx_activity_created    (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- SEED DATA (Optional — comment out if not needed on production)
-- ============================================================================

-- ─── Seed Categories ───────────────────────────────────────────────────────
INSERT INTO categories (name, description) VALUES
    ('Computer Science', 'Programming, algorithms, systems, and theory'),
    ('Mathematics',      'Pure and applied mathematics'),
    ('Physics',          'Classical, modern, and quantum physics'),
    ('Chemistry',        'Organic, inorganic, and physical chemistry'),
    ('Literature',       'Fiction, poetry, drama, and criticism'),
    ('History',          'World, regional, and cultural history'),
    ('Biography',        'Biographies, autobiographies, and memoirs'),
    ('Reference',        'Dictionaries, encyclopedias, and handbooks'),
    ('Fiction',          'Novels and short story collections'),
    ('Self-Help',        'Personal development and productivity');


-- ─── Seed Sample Books (Optional) ──────────────────────────────────────────
INSERT INTO books
    (title, author, publisher, price, total_copies, available_copies,
     issued_copies, category_id, status, added_date)
VALUES
    ('Introduction to Algorithms', 'Thomas H. Cormen', 'MIT Press',
     850.00, 3, 3, 0, 1, 'Available', CURDATE()),

    ('Clean Code', 'Robert C. Martin', 'Prentice Hall',
     650.00, 2, 2, 0, 1, 'Available', CURDATE()),

    ('The Pragmatic Programmer', 'David Thomas', 'Addison-Wesley',
     720.00, 2, 2, 0, 1, 'Available', CURDATE()),

    ('Calculus: Early Transcendentals', 'James Stewart', 'Cengage',
     920.00, 4, 4, 0, 2, 'Available', CURDATE()),

    ('Atomic Habits', 'James Clear', 'Penguin Random House',
     499.00, 5, 5, 0, 10, 'Available', CURDATE()),

    ('Sapiens', 'Yuval Noah Harari', 'Harper',
     599.00, 3, 3, 0, 6, 'Available', CURDATE()),

    ('The Alchemist', 'Paulo Coelho', 'HarperOne',
     350.00, 4, 4, 0, 9, 'Available', CURDATE()),

    ('Structure and Interpretation of Computer Programs', 'Abelson & Sussman',
     'MIT Press', 800.00, 2, 2, 0, 1, 'Available', CURDATE());


-- ============================================================================
-- VIEWS (Optional — for reporting / dashboards)
-- ============================================================================

-- ─── View: Currently Overdue Issues ────────────────────────────────────────
CREATE OR REPLACE VIEW v_overdue_issues AS
SELECT
    bi.id              AS issue_id,
    bi.student_id,
    s.full_name        AS student_name,
    s.enrollment_number,
    s.phone_number,
    bi.book_id,
    b.title            AS book_title,
    b.author           AS book_author,
    bi.issue_date,
    bi.due_date,
    DATEDIFF(CURDATE(), bi.due_date) AS days_overdue,
    ROUND(b.price * 0.10, 2)                                AS rent_amount,
    ROUND(b.price * 0.10 * 0.05, 2)                         AS fine_per_day,
    ROUND(b.price * 0.10 * 0.05 *
          DATEDIFF(CURDATE(), bi.due_date), 2)              AS accrued_late_fine
FROM book_issues bi
    INNER JOIN students s ON s.id = bi.student_id
    INNER JOIN books    b ON b.id = bi.book_id
WHERE bi.is_returned = FALSE
    AND bi.is_lost = FALSE
    AND bi.due_date < CURDATE();


-- ─── View: Student Fine Summary ────────────────────────────────────────────
CREATE OR REPLACE VIEW v_student_fine_summary AS
SELECT
    s.id                                                    AS student_id,
    s.full_name,
    s.enrollment_number,
    s.behaviour_score,
    s.account_status,
    COUNT(f.id)                                             AS total_fines,
    COALESCE(SUM(CASE WHEN f.status = 'Unpaid' THEN f.amount
                      ELSE 0 END), 0)                       AS unpaid_amount,
    COALESCE(SUM(CASE WHEN f.status = 'Paid'   THEN f.amount
                      ELSE 0 END), 0)                       AS paid_amount,
    COALESCE(SUM(f.amount), 0)                              AS total_amount
FROM students s
    LEFT JOIN fines f ON f.student_id = s.id
GROUP BY s.id, s.full_name, s.enrollment_number,
         s.behaviour_score, s.account_status;


-- ─── View: Active Issues per Student ───────────────────────────────────────
CREATE OR REPLACE VIEW v_student_active_issues AS
SELECT
    s.id                    AS student_id,
    s.full_name,
    s.enrollment_number,
    COUNT(bi.id)            AS active_issue_count
FROM students s
    LEFT JOIN book_issues bi
        ON bi.student_id = s.id
        AND bi.is_returned = FALSE
        AND bi.is_lost = FALSE
GROUP BY s.id, s.full_name, s.enrollment_number;


-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
-- To verify installation:
--   USE libraryhub;
--   SHOW TABLES;
--   SELECT COUNT(*) FROM categories;   -- Should return 10
--   SELECT COUNT(*) FROM books;        -- Should return 8
-- ============================================================================