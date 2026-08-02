<div align="center">

```
██████╗  ██████╗  ██████╗ ███╗   ███╗
██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║
██║  ██║██║   ██║██║   ██║██╔████╔██║
██║  ██║██║   ██║██║   ██║██║╚██╔╝██║
██████╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║
╚═════╝  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝
```

# DOOM — Web Vulnerability Scanner

**Enterprise-grade automated web vulnerability scanner built for DVWA and CTF lab environments.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-purple?style=flat-square&logo=linux)](https://kali.org)
[![Version](https://img.shields.io/badge/Version-3.0.0-red?style=flat-square)](https://github.com/tayyabakhtar/doom-scanner)
[![Author](https://img.shields.io/badge/Author-Tayyab%20Akhtar-orange?style=flat-square)](https://github.com/tayyabakhtar)

> ⚠️ **Legal Disclaimer:** DOOM is intended for use on systems you own or have **explicit written authorisation** to test. Unauthorised scanning is illegal. Always obtain permission before testing any target.

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Vulnerability Coverage](#vulnerability-coverage)
- [Installation](#installation)
- [Usage](#usage)
- [Flag Reference](#flag-reference)
- [How It Works](#how-it-works)
- [Sample Output](#sample-output)
- [PDF Report](#pdf-report)
- [Project Structure](#project-structure)
- [Disclaimer](#disclaimer)

---

## Overview

DOOM is a command-line web vulnerability scanner written in Python, designed to automate the detection of common web application vulnerabilities against **DVWA (Damn Vulnerable Web Application)** and general web targets.

Unlike simple scanners, DOOM:
- **Auto-detects DVWA** and directly targets every known vulnerability module
- **Auto-authenticates** with DVWA — no manual cookie copying required
- **Auto-sets security level** via the DVWA interface
- Generates a **professional enterprise-grade PDF report** with CVSS scores, OWASP references, and step-by-step remediation

Built for the Offensive Security module by **Tayyab Akhtar**.

---

## Features

| Feature | Description |
|---|---|
| Auto DVWA Login | Automatically logs into DVWA with default or custom credentials |
| Direct Module Targeting | Directly hits every DVWA vulnerability URL — no crawling guesswork |
| Auto Security Level | Sets DVWA security to your chosen level automatically |
| 6 Vulnerability Checks | XSS (Reflected + Stored), SQLi, Command Injection, LFI, CSRF |
| Animated CLI | Threaded spinner animation during scans |
| Colour-Coded Output | CRITICAL (red), HIGH (orange), MEDIUM (yellow), LOW (blue) |
| Enterprise PDF Report | Cover page, executive summary, CVSS table, remediation steps |
| Stealth Mode | Random jitter delays + User-Agent rotation |
| Rate Limiting | Configurable delay between requests |
| Single File | One Python script, no complex setup |

---

## Vulnerability Coverage

| # | Vulnerability | CVSS | Severity | CWE | OWASP 2021 |
|---|---|---|---|---|---|
| 1 | SQL Injection (Error-Based) | 9.8 | CRITICAL | CWE-89 | A03: Injection |
| 2 | OS Command Injection | 9.8 | CRITICAL | CWE-78 | A03: Injection |
| 3 | Cross-Site Scripting (Stored) | 7.2 | HIGH | CWE-79 | A03: Injection |
| 4 | Local File Inclusion | 8.1 | HIGH | CWE-98 | A01: Broken Access Control |
| 5 | Cross-Site Scripting (Reflected) | 6.1 | HIGH | CWE-79 | A03: Injection |
| 6 | Cross-Site Request Forgery | 6.5 | MEDIUM | CWE-352 | A01: Broken Access Control |

---

## Installation

### Prerequisites

- Python 3.8+
- Kali Linux (recommended) or any Linux distro
- DVWA running locally (Docker recommended)

### Step 1 — Clone the repository

```bash
git clone https://github.com/tayyabakhtar786/Doom.git
cd DOOM
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Set up DVWA (if not already running)

```bash
# Pull and run DVWA via Docker
docker pull vulnerables/web-dvwa
docker run -d -p 80:80 vulnerables/web-dvwa
```

Then visit `http://localhost/dvwa/setup.php` and click **Create / Reset Database**.

### Step 4 — Verify installation

```bash
python doom.py -h
```

---

## Usage

### Basic scan — DOOM auto-logs in and scans everything

```bash
python doom.py -u http://localhost
```

### Custom security level

```bash
python doom.py -u http://localhost --level low
```

### Stealth mode with slower requests

```bash
python doom.py -u http://localhost --stealth --delay 1.0
```

### Custom PDF output filename

```bash
python doom.py -u http://localhost -o my_report.pdf
```

### Skip login (if already authenticated via another method)

```bash
python doom.py -u http://localhost --no-login
```

### Full example

```bash
python doom.py -u http://localhost --level low --stealth --delay 0.8 -o pentest_report.pdf
```

---

## Flag Reference

| Flag | Type | Default | Description |
|---|---|---|---|
| `-u`, `--url` | string | `http://127.0.0.1` | Target base URL |
| `-o`, `--output` | string | `DOOM_Report_<timestamp>.pdf` | PDF output filename |
| `--level` | choice | `low` | DVWA security level: `low` / `medium` / `high` / `impossible` |
| `--delay` | float | `0.5` | Seconds between HTTP requests |
| `--stealth` | flag | off | Enable stealth mode (random jitter + UA rotation) |
| `--no-login` | flag | off | Skip DVWA auto-login |
| `-h`, `--help` | flag | — | Show help and exit |

---

## How It Works

```
doom.py
  │
  ├── 1. UI.banner()          → ASCII art + version info
  ├── 2. UI.loading()         → Animated startup sequence
  ├── 3. DVWAScanner.login()  → Auto-authenticates with DVWA
  ├── 4. set_security_level() → Sets DVWA to chosen level
  │
  ├── 5. run_full_scan()
  │     ├── scan_sqli()       → SQL Injection (forms + URL params)
  │     ├── scan_xss_r()      → Reflected XSS (form inputs)
  │     ├── scan_xss_s()      → Stored XSS (submit + re-fetch)
  │     ├── scan_cmd()        → Command Injection (ping form)
  │     ├── scan_lfi()        → Local File Inclusion (file param)
  │     └── scan_csrf()       → CSRF (missing token check)
  │
  └── 6. EnterpriseReporter   → PDF with cover, summary, findings
```

Each check:
1. Sends crafted HTTP requests with known exploit payloads
2. Analyses the response for vulnerability indicators
3. Records the finding with CVSS score, CWE, OWASP reference
4. Prints a colour-coded result to the terminal immediately

---

## Sample Output
```
██████╗  ██████╗  ██████╗ ███╗   ███╗
██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║
██║  ██║██║   ██║██║   ██║██╔████╔██║
██║  ██║██║   ██║██║   ██║██║╚██╔╝██║
██████╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║
╚═════╝  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝
```

════════════════════════════════════════════════════════════════
  Developer    : Tayyab Akhtar
  Version      : 3.0.0
  Module       : Full DVWA Vulnerability Scanner
  Status       : Enterprise Professional Edition
════════════════════════════════════════════════════════════════

[*] Initializing DOOM engine... OK
[*] Loading attack payloads... OK
[*] Mapping DVWA modules... OK
[*] Preparing scan environment... OK

[+] Attempting automated DVWA authentication...
[+] Authentication successful
[+] Security level set to: low
[+] Starting comprehensive scan of http://localhost

[✶] Scanning SQL Injection...
[!] VULNERABILITY FOUND: SQL Injection at /dvwa/vulnerabilities/sqli/

[✸] Scanning Command Injection...
[!] VULNERABILITY FOUND: Command Injection at /dvwa/vulnerabilities/exec/

...

═══════════════════════════════════════════════════════════
Scan completed! 6 vulnerabilities discovered
Threat Score: 8.9/10.0
Report saved to: DOOM_Report_20260802_120000.pdf
═══════════════════════════════════════════════════════════
```

---

## PDF Report

The generated PDF includes:

- **Cover Page** — Tool name, author, target, scan date, threat score
- **Executive Summary** — Written narrative, overall risk classification
- **Summary Table** — All findings with severity, CVSS, and OWASP mapping
- **Detailed Findings** — Per-finding section with:
  - Severity badge
  - Affected endpoint
  - Description and business impact
  - Enterprise remediation steps (numbered)
  - CWE and OWASP references

---

## Project Structure

```
doom-scanner/
├── doom.py              # Main scanner (single file)
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── LICENSE              # MIT License
├── CHEATSHEET.md        # Quick flag reference
├── INTERNALS.md         # Architecture and how-to-extend guide
├── docs/
│   └── report_sample.md # Sample report structure description
└── tests/
    └── test_doom.py     # Basic unit tests
```

---

## Disclaimer

> This tool is developed for **educational purposes only** as part of an Offensive Security module.
> 
> **DOOM must only be used against:**
> - Systems you personally own
> - Systems for which you have **explicit written authorisation** to test
> - Intentionally vulnerable lab environments (DVWA, Juice Shop, HackTheBox, TryHackMe)
> 
> The author (**Tayyab Akhtar**) accepts no liability for misuse of this tool.
> Unauthorised computer access is a criminal offence under the Computer Misuse Act 1990 (UK),
> CFAA (USA), and equivalent laws worldwide.

---

<div align="center">

Made with ❤️ by **Tayyab Akhtar**

</div>
