# Security Policy

The `seriousdb` team and contributors take the security and integrity of this project seriously. We appreciate your efforts to responsibly disclose any vulnerabilities you find.

## Supported Versions

Only the latest code on the `main` branch and the most recent release receive active security updates.

| Version | Supported          |
| ------- | ------------------ |
| `main`  | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions, or pull requests.**

### Preferred Method: Private Vulnerability Reporting
We strongly encourage reporting vulnerabilities confidentially using GitHub's built-in tool:
1. Navigate to the [Security tab](https://github.com/danieldeer/seriousdb/security) of this repository.
2. Click on **Report a vulnerability** to open an advisory draft.
3. Fill in the requested details.

This allows us to collaborate privately on a fix, test it, and publish an advisory and patch simultaneously.

---

## What to Include in Your Report

To help us triage and resolve the issue quickly, please provide as much of the following as possible:

- **Summary & Impact:** A clear description of the vulnerability and the potential impact (e.g., data loss, denial of service, memory exhaustion, information disclosure).
- **Vulnerability Classification:** If known, reference relevant CWE IDs (e.g., *CWE-372*, *CWE-400*).
- **Proof of Concept (PoC):** Step-by-step instructions, sample requests (`curl`, bash, Python script, or JSON payload) to reproduce the issue.
- **Affected Endpoints / Components:** Which module or API endpoint is impacted (e.g., `PUT /items`, `DbEngine`, storage compaction).
- **Suggested Fix:** If you have ideas or patches on how to resolve the issue, feel free to include them.

## Handling Process & Disclosure

- **Acknowledgment:** Maintainers aim to acknowledge receipt of security reports within 48 to 72 hours.
- **Triage & Patch:** We will investigate and work on a fix in a private branch/fork.
- **Coordinated Disclosure:** Once a fix is verified and released, a public security advisory will be published, giving full credit to the reporter (unless you prefer to remain anonymous).