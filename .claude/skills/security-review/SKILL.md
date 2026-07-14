---
name: security-review
description: Perform a security-focused review of code changes or the full codebase. Use when the user asks for a "security review", "security audit", "check for vulnerabilities", or "is this secure".
when-to-use: security review, security audit, check security, vulnerabilities, is this secure, OWASP
allowed-tools: powershell, bash
argument-hint: "[file, PR, or scope to review]"
---

# Security Review Skill

## Scope
Review code for exploitable security vulnerabilities with >80% confidence before flagging. Do not flag theoretical or style issues.

## OWASP Top 10 Checklist

### 1. Injection (SQL, Command, LDAP, NoSQL)
- [ ] All external input is parameterized or sanitized before use in queries/commands
- [ ] ORM is used correctly (no raw query string building with user input)
- [ ] Shell commands are never constructed from user input

### 2. Broken Authentication
- [ ] Passwords are hashed with bcrypt/argon2 (not MD5/SHA1)
- [ ] Session tokens are cryptographically random (not sequential IDs)
- [ ] Sessions are invalidated on logout
- [ ] Brute force protection exists (rate limiting, lockout)

### 3. Sensitive Data Exposure
- [ ] No secrets, tokens, or credentials in source code or logs
- [ ] PII is encrypted at rest for sensitive fields
- [ ] HTTPS enforced everywhere
- [ ] API keys in environment variables only

### 4. Security Misconfigurations
- [ ] Debug mode disabled in production
- [ ] Default credentials changed
- [ ] Unnecessary features/endpoints disabled
- [ ] Error messages don't expose stack traces to end users

### 5. Broken Access Control
- [ ] Authorization checked on every endpoint (not just at the router level)
- [ ] User can only access their own resources (IDOR check)
- [ ] Admin routes require admin role
- [ ] Direct object references (IDs) are validated against the authenticated user

### 6. XSS (Cross-Site Scripting)
- [ ] User input is escaped in HTML output
- [ ] Content-Security-Policy header configured
- [ ] innerHTML avoided; textContent or framework escaping used instead
- [ ] JSON from API is not directly interpolated into HTML

### 7. Insecure Dependencies
```bash
npm audit
pip-audit
bundler-audit
trivy image <image>
```

### 8. Insecure Deserialization
- [ ] User-controlled data is never deserialized into complex objects without validation
- [ ] No use of pickle/marshal/eval on untrusted input

### 9. Logging and Monitoring
- [ ] Auth failures are logged
- [ ] Sensitive data is NOT logged (passwords, tokens, PII)
- [ ] Logs are not visible to end users

### 10. SSRF (Server-Side Request Forgery)
- [ ] URLs from user input are validated against an allowlist before fetching
- [ ] Internal metadata endpoints are blocked from external requests

## Severity Scale
- **CRITICAL** — Exploitable without authentication, direct data access or RCE
- **HIGH** — Exploitable with authentication, privilege escalation or data leakage
- **MEDIUM** — Requires specific conditions, defense-in-depth gap
- **LOW** — Best practice gap, no direct exploit path

## Output Format
For each finding:
```
[SEVERITY] [Category]
File: path/to/file.ext, line N
Issue: [what is wrong]
Risk: [what an attacker can do]
Fix: [specific remediation]
```
