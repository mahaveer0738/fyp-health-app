# Deep Dive: Authentication, Database, & Security

This document explains the theory, technologies, and architecture behind the login system and patient database recently added to the FYP Health App.

## 1. How the Login Page was Made
The login and registration pages (`login.html` and `register.html`) were built using standard web technologies (Vanilla HTML, CSS, and JavaScript). 

- **No External Frameworks**: It does not use heavy frameworks like React or Angular. This keeps your project lightweight.
- **Styling**: It uses modern CSS variables and flexbox/grid to create a responsive, glass-like UI. The only external resource is the **Google Fonts API** (to load the 'Inter' font).
- **Communication (API)**: When you click "Login", the JavaScript uses the browser's built-in `fetch()` API to send a request to your *own* backend at `http://localhost:8000/auth/login`. **No third-party authentication services (like Google Auth or Firebase) are used**. It is a fully custom, self-contained system.

---

## 2. The Database Architecture (SQLite + SQLAlchemy)

We used **SQLite**, which is a lightweight SQL database that stores all data in a single file (`fyp_health.db`). To interact with the database using Python instead of raw SQL queries, we used an ORM (Object-Relational Mapper) called **SQLAlchemy**.

There are exactly **3 Tables** in the database:

### A. The `users` Table
Stores the core authentication credentials.
- `id`: Unique integer (Primary Key).
- `email`: The user's email address (must be unique).
- `hashed_password`: We NEVER store the actual password (explained below).
- `is_active`: A boolean to ban/disable users if needed.

### B. The `patient_profiles` Table
Stores the medical profile associated with a user.
- `id`: Unique integer (Primary Key).
- `user_id`: A **Foreign Key** pointing to the `users` table. 
- `name`, `age`, `gender`, `chronic_conditions`: Static data about the patient.

### C. The `visit_history` Table
Stores the timeline of every time the patient talks to the Agent.
- `id`: Unique integer (Primary Key).
- `patient_id`: A **Foreign Key** pointing to the `patient_profiles` table.
- `timestamp`: The exact date and time of the chat.
- `symptoms`: What the patient complained about.
- `triage_label`: The L0-L3 severity prediction.
- `ai_summary`: The final advice given by the LLM.

**How data is stored:**
One `User` has exactly One `PatientProfile`. 
One `PatientProfile` can have Many `VisitHistory` records.

---

## 3. Security: Can it be hacked?

Security is handled in `backend/core/security.py`. While no system is 100% unhackable, this project implements industry-standard security measures to prevent common attacks.

### 🛡️ What makes it secure?
1. **Password Hashing (bcrypt)**: If a hacker steals your `fyp_health.db` database, they will NOT see user passwords. They will see strings like `$2b$12$NqO/x...`. We use **bcrypt**, an algorithm that converts passwords into irreversible mathematical hashes. Even if someone knows the hash, they cannot easily reverse it to find the password.
2. **JWT (JSON Web Tokens)**: When a user logs in successfully, the server gives them a temporary digital ID card (a JWT token). The token is signed using a secret key (`SECRET_KEY`). If a hacker tries to forge a token, the backend will reject it because the cryptographic signature won't match.

### ⚠️ Potential Vulnerabilities (How it *could* be hacked in production)
Because this is a Final Year Project currently running locally, there are two main vulnerabilities you must address before deploying to the real internet:

1. **No HTTPS (MITM Attacks)**: Currently, the app runs on `http://localhost`. If deployed on HTTP, a hacker on the same Wi-Fi network could intercept the traffic (Man-In-The-Middle) and steal the JWT token or passwords while they are flying through the air. 
   - *Fix*: Always deploy using an SSL Certificate (`https://`).
2. **XSS (Cross-Site Scripting)**: The JWT token is stored in the browser's `localStorage`. If a hacker manages to inject malicious JavaScript into your webpage (e.g., via a bad input), that script can easily read `localStorage` and steal the user's session token.
   - *Fix*: For enterprise apps, it is recommended to store tokens in `HttpOnly` Cookies, which JavaScript cannot access.

## Summary of Technologies Used
- **Database**: SQLite
- **ORM**: SQLAlchemy
- **Web Framework**: FastAPI
- **Password Hashing**: `passlib` with `bcrypt`
- **Token Generation**: `python-jose` (JWT)
