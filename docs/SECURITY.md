# 🔐 Security Overview

This document summarizes the **application-level security model** of TaskHub API.

The focus is on **correctness, simplicity, and production-aligned defaults**.

---

## 1️⃣ Authentication (JWT)

- JWT-based authentication
- Short-lived access tokens
- Long-lived refresh tokens
- Tokens sent via `Authorization: Bearer`

Every protected request validates:
- Token signature
- Token expiration
- User existence

Invalid tokens return `401 Unauthorized`.

---

## 2️⃣ Authorization

- Users can only access their own resources
- Ownership checks enforced server-side
- No client-side trust

---

## 3️⃣ Password Handling

- Passwords are never stored in plaintext
- `bcrypt` used in production
- Faster hashing used in tests for CI performance

Passwords are:
- Hashed on registration
- Verified on login
- Never returned in responses

---

## 4️⃣ Secrets Management

Sensitive values include:
- Database URL
- JWT secret
- Redis connection URL

Rules:
- Supplied via environment variables
- Documented in `.env.example`
- Never committed to Git
- Never baked into images

---

## 🎯 Summary

This security model ensures:
- Safe authentication
- Proper authorization
- Secure credential handling
- Clear separation between code and secrets

It reflects **real-world mid-level backend security practices** without unnecessary complexity.