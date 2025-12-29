# 🔐 Security Overview — TaskHub API (Mid-Level)

This document describes the **security design decisions** of the TaskHub API.

The goal is to demonstrate **safe, production-aligned backend practices**
without unnecessary complexity.

---

## 🎯 Security Philosophy

- Secure by default
- Explicit authentication and authorization
- No secrets in source code
- Configuration over hardcoding
- Defense through simplicity

This project focuses on **application-layer security**, not infrastructure hardening.

---

## 1️⃣ Authentication Strategy (JWT)

TaskHub uses **JSON Web Tokens (JWT)** for authentication.

### Token Types
- **Access Token**
  - Short-lived
  - Sent with every authenticated request
- **Refresh Token**
  - Longer-lived
  - Used to obtain new access tokens

### Token Transport
- Sent via `Authorization` header
- Format:  
Authorization: Bearer <token>

yaml
Copy code

### Token Contents
- `sub` — authenticated username
- `exp` — expiration timestamp

### Validation Rules
Every protected request validates:
- Token signature
- Token expiration
- User existence in the database

Invalid or expired tokens result in `401 Unauthorized`.

---

## 2️⃣ Authorization

Authorization is enforced at the API layer.

Rules:
- Users can only access their own resources
- Ownership checks are performed in every protected endpoint
- No client-side trust is assumed

Example:
- A task can only be deleted by its owner
- Requests with valid tokens but invalid ownership are rejected

---

## 3️⃣ Password Handling

Passwords are **never stored or transmitted in plaintext**.

### Hashing Strategy
- `bcrypt` is used in production
- A faster hashing algorithm is used in test environments to speed up CI

### Rules
- Passwords are hashed during registration
- Hashes are verified during login
- Hashed passwords are never returned in API responses

The system never exposes:
- Plain passwords
- Password hashes
- Credential metadata

---

## 4️⃣ Secrets Management

Sensitive configuration includes:
- Database connection URL
- JWT signing secret
- Redis broker URL

### Rules
- Secrets are injected via environment variables
- `.env.example` documents required variables
- `.env` files are excluded from version control
- No secrets are hardcoded in source code

### Environments
- Local: `.env`
- CI: GitHub Actions secrets
- AWS: ECS task definition / parameter store

---

## 5️⃣ Transport & Network Safety

- HTTPS is assumed in production environments
- TLS termination occurs at the load balancer
- Internal service communication uses private networking

The application does not implement custom TLS logic.

---

## 6️⃣ Dependency & Runtime Safety

- Dependencies are pinned via `requirements.txt`
- No dynamic dependency loading at runtime
- Security-sensitive logic is isolated in dedicated modules

The project avoids:
- Runtime code execution
- Dynamic imports based on user input

---

## 7️⃣ Repository Safety

The repository enforces:
- `.gitignore` for environment files
- No credentials in commits
- Clear separation between code and configuration

All secrets must be supplied **at runtime**, never at build time.

---

## 🎯 Summary

This security model ensures:
- Proper authentication and authorization
- Safe password handling
- Secure secret management
- Clean separation of concerns

The approach reflects **real-world mid-level backend security practices**
without introducing unnecessary complexity.