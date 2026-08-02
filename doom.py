#!/usr/bin/env python3
"""
DOOM - Enterprise Web Vulnerability Scanner (Full DVWA Automation)
Author: Tayyab Akhtar
Description: Automatically crawls and tests all DVWA modules with live animation.
"""

import argparse
import itertools
import random
import re
import sys
import threading
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, parse_qsl, urlunparse

import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Style, Cursor
from fpdf import FPDF
from pyfiglet import Figlet

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# ============================================================================
# ANIMATION SYSTEM (Threaded)
# ============================================================================
class Animator:
    """Handles the rotating star animation during scans."""
    _stop = False
    _thread = None
    _chars = ['✶', '✸', '✹', '✺', '✻', '✼', '❋', '❊', '❉', '✱']
    
    @classmethod
    def start(cls, msg="Scanning"):
        """Start the spinner with a message."""
        cls._stop = False
        cls._msg = msg
        cls._thread = threading.Thread(target=cls._animate, daemon=True)
        cls._thread.start()
    
    @classmethod
    def _animate(cls):
        """Run the animation loop."""
        for char in itertools.cycle(cls._chars):
            if cls._stop:
                break
            sys.stdout.write(f"\r{Fore.YELLOW}[{char}] {cls._msg}...")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 50 + "\r")  # Clear the line
        sys.stdout.flush()
    
    @classmethod
    def stop(cls, success=True):
        """Stop the spinner and print result."""
        cls._stop = True
        if cls._thread and cls._thread.is_alive():
            cls._thread.join(timeout=0.2)
        if success:
            sys.stdout.write(f"\r{Fore.GREEN}[✔] {cls._msg} completed!\n")
        else:
            sys.stdout.write(f"\r{Fore.RED}[✘] {cls._msg} failed!\n")
        sys.stdout.flush()


# ============================================================================
# UI CLASS
# ============================================================================
class UI:
    @staticmethod
    def banner():
        f = Figlet(font='big')
        print(Fore.RED + f.renderText('DOOM') + Style.RESET_ALL)
        print(Fore.CYAN + "═" * 65)
        print(Fore.CYAN + "  Developer    : Tayyab Akhtar")
        print(Fore.CYAN + "  Version      : 3.0.0")
        print(Fore.CYAN + "  Module       : Full DVWA Vulnerability Scanner")
        print(Fore.CYAN + "  Status       : Enterprise Professional Edition")
        print(Fore.CYAN + "═" * 65)
        print()
    
    @staticmethod
    def loading():
        phases = [
            "Initializing DOOM engine",
            "Loading attack payloads",
            "Mapping DVWA modules",
            "Preparing scan environment"
        ]
        for phase in phases:
            print(Fore.YELLOW + f"[*] {phase}", end='', flush=True)
            for _ in range(3):
                time.sleep(0.2)
                print(Fore.YELLOW + ".", end='', flush=True)
            print(Fore.GREEN + " OK")
        print()
    
    @staticmethod
    def info(msg):
        print(Fore.GREEN + "[+] " + msg)
    
    @staticmethod
    def warning(msg):
        print(Fore.YELLOW + "[!] " + msg)
    
    @staticmethod
    def error(msg):
        print(Fore.RED + "[-] " + msg)
    
    @staticmethod
    def vuln_found(msg):
        print(Fore.RED + Style.BRIGHT + f"[!] VULNERABILITY FOUND: {msg}")
    
    @staticmethod
    def info_blue(msg):
        print(Fore.BLUE + "[*] " + msg)


# ============================================================================
# VULNERABILITY DATABASE (Enterprise Remediation)
# ============================================================================
VULN_DATABASE = {
    "SQLi": {
        "title": "SQL Injection (Error-Based)",
        "cwe": "CWE-89", "owasp": "A03:2021-Injection",
        "cvss": 9.8, "severity": "CRITICAL",
        "impact": "An attacker can bypass authentication, read or modify sensitive database records, and potentially execute administrative operations on the database host.",
        "remediation": (
            "1. Use parameterized queries (prepared statements) for all database access.\n"
            "2. Apply strict allow-list input validation for identifiers that cannot be parameterized.\n"
            "3. Run the database account under the principle of least privilege."
        )
    },
    "XSS_R": {
        "title": "Cross-Site Scripting (Reflected)",
        "cwe": "CWE-79", "owasp": "A03:2021-Injection",
        "cvss": 6.1, "severity": "HIGH",
        "impact": "Attackers can run malicious scripts in a victim's browser context, enabling session hijacking, credential theft, or page defacement.",
        "remediation": (
            "1. Apply context-aware output encoding (HTML, JS, attribute) on all dynamic data.\n"
            "2. Deploy a strict Content Security Policy (CSP) header.\n"
            "3. Sanitize inputs using vetted libraries before rendering or persisting."
        )
    },
    "CMD_INJ": {
        "title": "OS Command Injection",
        "cwe": "CWE-78", "owasp": "A03:2021-Injection",
        "cvss": 9.8, "severity": "CRITICAL",
        "impact": "Allows arbitrary OS command execution, potentially leading to full host compromise and lateral movement.",
        "remediation": (
            "1. Avoid passing user input to system shells.\n"
            "2. Use native language APIs instead of shell commands (no shell=True in Python).\n"
            "3. Enforce strict allow-list validation on any unavoidable command parameters."
        )
    },
    "LFI": {
        "title": "Local File Inclusion",
        "cwe": "CWE-98", "owasp": "A01:2021-Broken Access Control",
        "cvss": 8.1, "severity": "HIGH",
        "impact": "Attackers can read sensitive local files (configs, credentials) or achieve code execution via log poisoning.",
        "remediation": (
            "1. Avoid using user input in file path resolution.\n"
            "2. Canonicalize paths (os.path.realpath) and confirm they stay within an authorized base directory.\n"
            "3. Use a hardcoded allow-list of permitted file identifiers."
        )
    },
    "CSRF": {
        "title": "Cross-Site Request Forgery",
        "cwe": "CWE-352", "owasp": "A01:2021-Broken Access Control",
        "cvss": 6.5, "severity": "MEDIUM",
        "impact": "Forces an authenticated user's browser to submit forged state-changing requests without consent.",
        "remediation": (
            "1. Implement unpredictable per-session anti-CSRF tokens for all state-changing requests.\n"
            "2. Set session cookies to SameSite=Strict or Lax.\n"
            "3. Verify custom request headers (e.g., X-Requested-With) server-side."
        )
    },
    "XSS_S": {
        "title": "Cross-Site Scripting (Stored)",
        "cwe": "CWE-79", "owasp": "A03:2021-Injection",
        "cvss": 7.2, "severity": "HIGH",
        "impact": "Persistent malicious scripts stored in the database, affecting all users who view the affected page.",
        "remediation": (
            "1. Implement context-aware output encoding for all stored data.\n"
            "2. Use CSP headers to restrict script execution.\n"
            "3. Properly sanitize all input before persisting to the database."
        )
    }
}

SEVERITY_COLORS = {
    "CRITICAL": (204, 0, 0),
    "HIGH":     (230, 92, 0),
    "MEDIUM":   (200, 150, 0),
    "LOW":      (0, 102, 204),
    "INFO":     (0, 153, 76)
}


# ============================================================================
# DVWA SCANNER (Automated Full Coverage)
# ============================================================================
class DVWAScanner:
    def __init__(self, base_url, delay=0.5, stealth=False):
        self.base_url = base_url
        self.delay = delay
        self.stealth = stealth
        self.session = requests.Session()
        self.findings = []
        
        # All DVWA modules to test
        self.modules = {
            'sqli': {
                'url': 'vulnerabilities/sqli/',
                'method': 'POST',
                'params': {'id': '1', 'Submit': 'Submit'}
            },
            'sqliblind': {
                'url': 'vulnerabilities/sqli_blind/',
                'method': 'POST',
                'params': {'id': '1', 'Submit': 'Submit'}
            },
            'xss_r': {
                'url': 'vulnerabilities/xss_r/',
                'method': 'GET',
                'params': {'name': 'test'}
            },
            'xss_s': {
                'url': 'vulnerabilities/xss_s/',
                'method': 'POST',
                'params': {'txtName': 'test', 'mtxMessage': 'test', 'btnSign': 'Sign Guestbook'}
            },
            'cmd_exec': {
                'url': 'vulnerabilities/exec/',
                'method': 'POST',
                'params': {'ip': '127.0.0.1', 'Submit': 'Submit'}
            },
            'lfi': {
                'url': 'vulnerabilities/fi/',
                'method': 'GET',
                'params': {'page': 'include.php'}
            },
            'csrf': {
                'url': 'vulnerabilities/csrf/',
                'method': 'GET',
                'params': {}
            },
            'upload': {
                'url': 'vulnerabilities/upload/',
                'method': 'GET',
                'params': {}
            },
            'captcha': {
                'url': 'vulnerabilities/captcha/',
                'method': 'GET',
                'params': {}
            }
        }
    
    def login(self, username='admin', password='password'):
        """Login to DVWA."""
        Animator.start("Logging into DVWA")
        try:
            login_url = urljoin(self.base_url, 'login.php')
            r = self.session.get(login_url)
            soup = BeautifulSoup(r.text, 'html.parser')
            token = soup.find('input', {'name': 'user_token'})
            user_token = token['value'] if token else ''
            
            payload = {
                'username': username,
                'password': password,
                'Login': 'Login',
                'user_token': user_token
            }
            r = self.session.post(login_url, data=payload)
            if 'index.php' in r.url or 'security' in r.url.lower():
                Animator.stop(True)
                return True
            Animator.stop(False)
            return False
        except Exception as e:
            Animator.stop(False)
            return False
    
    def set_security_level(self, level='low'):
        """Set DVWA security level."""
        Animator.start(f"Setting security level to '{level}'")
        try:
            sec_url = urljoin(self.base_url, 'security.php')
            r = self.session.get(sec_url)
            soup = BeautifulSoup(r.text, 'html.parser')
            token = soup.find('input', {'name': 'user_token'})
            user_token = token['value'] if token else ''
            
            payload = {
                'security': level,
                'seclev_submit': 'Submit',
                'user_token': user_token
            }
            self.session.post(sec_url, data=payload)
            Animator.stop(True)
        except:
            Animator.stop(False)
    
    def _random_delay(self):
        if self.stealth:
            time.sleep(self.delay + random.uniform(0, 1.0))
        else:
            time.sleep(self.delay)
    
    def scan_sqli(self, url):
        """Test for SQL injection."""
        Animator.start("Testing SQL Injection (error-based)")
        payloads = ["'", "1' OR '1'='1", "1' AND '1'='2"]
        for payload in payloads:
            try:
                self._random_delay()
                test_url = urljoin(self.base_url, url + f"?id={payload}&Submit=Submit")
                r = self.session.get(test_url)
                if any(sig in r.text.lower() for sig in ["sql syntax", "mysql_fetch", "you have an error in your sql"]):
                    Animator.stop()
                    return True
            except:
                pass
        Animator.stop(False)
        return False
    
    def scan_blind_sqli(self, url):
        """Test for blind SQL injection using time-based payloads."""
        Animator.start("Testing Blind SQL Injection (time-based)")
        try:
            self._random_delay()
            test_url = urljoin(self.base_url, url + "?id=1' AND SLEEP(5)-- &Submit=Submit")
            start = time.time()
            r = self.session.get(test_url, timeout=10)
            elapsed = time.time() - start
            if elapsed > 4.5:
                Animator.stop()
                return True
        except:
            pass
        Animator.stop(False)
        return False
    
    def scan_xss_reflected(self, url):
        """Test for reflected XSS."""
        Animator.start("Testing Reflected XSS")
        payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg/onload=alert(1)>"
        ]
        for payload in payloads:
            try:
                self._random_delay()
                test_url = urljoin(self.base_url, url + f"?name={payload}")
                r = self.session.get(test_url)
                if payload in r.text:
                    Animator.stop()
                    return True
            except:
                pass
        Animator.stop(False)
        return False
    
    def scan_xss_stored(self, url):
        """Test for stored XSS."""
        Animator.start("Testing Stored XSS")
        try:
            self._random_delay()
            payload = "<script>alert('XSS')</script>"
            data = {
                'txtName': 'test',
                'mtxMessage': payload,
                'btnSign': 'Sign Guestbook'
            }
            post_url = urljoin(self.base_url, url)
            POST_url = urljoin(self.base_url, 'vulnerabilities/xss_s/')
            r = self.session.post(POST_url, data=data)
            # Check if payload is reflected
            if payload in r.text:
                Animator.stop()
                return True
        except:
            pass
        Animator.stop(False)
        return False
    
    def scan_command_injection(self, url):
        """Test for command injection."""
        Animator.start("Testing Command Injection")
        payloads = ["; whoami", "| whoami", "&& whoami"]
        for payload in payloads:
            try:
                self._random_delay()
                data = {'ip': f'127.0.0.1{payload}', 'Submit': 'Submit'}
                post_url = urljoin(self.base_url, url)
                r = self.session.post(post_url, data=data)
                if any(sig in r.text for sig in ['uid=', 'root@', 'daemon', 'www-data']):
                    Animator.stop()
                    return True
            except:
                pass
        Animator.stop(False)
        return False
    
    def scan_lfi(self, url):
        """Test for Local File Inclusion."""
        Animator.start("Testing Local File Inclusion")
        payloads = [
            "../../../../etc/passwd",
            "....//....//....//etc/passwd",
            "php://filter/convert.base64-encode/resource=index.php"
        ]
        for payload in payloads:
            try:
                self._random_delay()
                test_url = urljoin(self.base_url, url + f"?page={payload}")
                r = self.session.get(test_url)
                if 'root:' in r.text or 'bin/bash' in r.text:
                    Animator.stop()
                    return True
            except:
                pass
        Animator.stop(False)
        return False
    
    def scan_csrf(self, url):
        """Check for CSRF protection."""
        Animator.start("Checking CSRF Protection")
        try:
            self._random_delay()
            test_url = urljoin(self.base_url, url)
            r = self.session.get(test_url)
            if 'user_token' not in r.text and 'csrf' not in r.text.lower():
                Animator.stop()
                return True
        except:
            pass
        Animator.stop(False)
        return False
    
    def scan_upload(self, url):
        """Check upload page."""
        Animator.start("Analyzing File Upload Module")
        try:
            self._random_delay()
            test_url = urljoin(self.base_url, url)
            r = self.session.get(test_url)
            if 'upload' in r.text.lower() or 'file' in r.text.lower():
                Animator.stop()
                return "manual"  # Manual testing required
        except:
            pass
        Animator.stop(False)
        return False
    
    def scan_captcha(self, url):
        """Check CAPTCHA implementation."""
        Animator.start("Analyzing CAPTCHA Implementation")
        try:
            self._random_delay()
            test_url = urljoin(self.base_url, url)
            r = self.session.get(test_url)
            if 'captcha' in r.text.lower() or 'recaptcha' in r.text.lower():
                Animator.stop()
                return "manual"  # Manual testing required
        except:
            pass
        Animator.stop(False)
        return False
    
    def run_full_scan(self):
        """Execute all vulnerability scans."""
        UI.info("Starting full vulnerability assessment...")
        print()
        
        # Test each module
        for module_name, module_info in self.modules.items():
            url = module_info['url']
            full_url = urljoin(self.base_url, url)
            
            UI.info_blue(f"\nTesting module: {module_name}")
            UI.info_blue(f"Target: {full_url}")
            print("-" * 50)
            
            # Run appropriate test based on module
            if module_name == 'sqli':
                if self.scan_sqli(url):
                    self.findings.append({"id": "SQLi", "path": url, "vuln_type": f"SQL Injection in {url}"})
                    UI.vuln_found(f"SQL Injection at {full_url}")
            elif module_name == 'sqliblind':
                if self.scan_blind_sqli(url):
                    self.findings.append({"id": "SQLi", "path": url, "vuln_type": f"Blind SQL Injection in {url}"})
                    UI.vuln_found(f"Blind SQL Injection at {full_url}")
            elif module_name == 'xss_r':
                if self.scan_xss_reflected(url):
                    self.findings.append({"id": "XSS_R", "path": url, "vuln_type": f"Reflected XSS in {url}"})
                    UI.vuln_found(f"Reflected XSS at {full_url}")
            elif module_name == 'xss_s':
                if self.scan_xss_stored(url):
                    self.findings.append({"id": "XSS_S", "path": url, "vuln_type": f"Stored XSS in {url}"})
                    UI.vuln_found(f"Stored XSS at {full_url}")
            elif module_name == 'cmd_exec':
                if self.scan_command_injection(url):
                    self.findings.append({"id": "CMD_INJ", "path": url, "vuln_type": f"Command Injection in {url}"})
                    UI.vuln_found(f"Command Injection at {full_url}")
            elif module_name == 'lfi':
                if self.scan_lfi(url):
                    self.findings.append({"id": "LFI", "path": url, "vuln_type": f"LFI in {url}"})
                    UI.vuln_found(f"Local File Inclusion at {full_url}")
            elif module_name == 'csrf':
                if self.scan_csrf(url):
                    self.findings.append({"id": "CSRF", "path": url, "vuln_type": f"CSRF in {url}"})
                    UI.vuln_found(f"CSRF vulnerability at {full_url}")
            elif module_name == 'upload':
                result = self.scan_upload(url)
                if result == "manual":
                    UI.info("File upload detected - Manual testing recommended")
            elif module_name == 'captcha':
                result = self.scan_captcha(url)
                if result == "manual":
                    UI.info("CAPTCHA module found - Manual testing recommended")
        
        print()
        UI.info(f"Scan complete. Total findings: {len(self.findings)}")
        return self.findings


# ============================================================================
# ENTERPRISE PDF REPORTER (No Overlap)
# ============================================================================
class EnterpriseReporter(FPDF):
    def __init__(self, target_url):
        super().__init__()
        self.target_url = target_url
        self.set_auto_page_break(auto=True, margin=20)
    
    def header(self):
        self.set_fill_color(26, 26, 26)
        self.rect(0, 0, 210, 26, 'F')
        self.set_xy(10, 6)
        self.set_font("helvetica", "B", 15)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, "DOOM VULNERABILITY ASSESSMENT REPORT", new_x="LMARGIN", new_y="NEXT")
        self.set_x(10)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(200, 200, 200)
        self.cell(0, 5, f"Enterprise Security Audit  |  Target: {self.target_url}")
        self.set_xy(10, 32)
        self.set_text_color(0, 0, 0)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Prepared by Tayyab Akhtar  |  Confidential  |  Page {self.page_no()}", align="C")
    
    def kv_block(self, label, value, value_color=(0, 0, 0)):
        self.set_font("helvetica", "B", 9)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        self.set_font("helvetica", "", 9)
        self.set_text_color(*value_color)
        self.multi_cell(0, 6, str(value), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(1)
    
    def executive_summary(self, findings, score):
        self.add_page()
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, "1. Executive Summary", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        
        self.set_font("helvetica", "", 10)
        self.multi_cell(0, 6,
            f"This report summarizes the security posture of {self.target_url}. "
            f"A comprehensive vulnerability assessment was performed on {datetime.now().strftime('%Y-%m-%d %H:%M')} "
            f"by Tayyab Akhtar. {len(findings)} vulnerabilities were identified and are detailed below "
            f"with enterprise-grade remediation guidance.")
        self.ln(4)
        
        box_top = self.get_y()
        box_h = 18
        self.set_fill_color(245, 245, 245)
        self.rect(10, box_top, 190, box_h, 'F')
        
        self.set_xy(14, box_top + 4)
        self.set_font("helvetica", "B", 12)
        self.cell(50, 10, "Overall Threat Score:")
        
        score_color = SEVERITY_COLORS["CRITICAL"] if score >= 7.0 else SEVERITY_COLORS["MEDIUM"]
        self.set_text_color(*score_color)
        self.set_font("helvetica", "B", 15)
        self.cell(30, 10, f"{score} / 10.0")
        
        self.set_text_color(0, 0, 0)
        self.set_font("helvetica", "I", 10)
        status = "HIGH RISK" if score >= 7.0 else "MEDIUM RISK"
        self.cell(0, 10, f"Classification: {status}")
        
        self.set_y(box_top + box_h + 8)
    
    def summary_table(self, findings):
        self.set_font("helvetica", "B", 12)
        self.cell(0, 10, "2. Summary of Findings", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        
        # Header
        self.set_font("helvetica", "B", 9)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(0, 0, 0)
        self.cell(80, 8, "Vulnerability", border=1, fill=True)
        self.cell(30, 8, "Severity", border=1, fill=True, align="C")
        self.cell(25, 8, "CVSS", border=1, fill=True, align="C")
        self.cell(55, 8, "OWASP", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
        
        # Data
        self.set_font("helvetica", "", 8)
        for item in findings:
            info = VULN_DATABASE.get(item['id'])
            if not info:
                continue
            self.set_text_color(0, 0, 0)
            self.cell(80, 8, info['title'], border=1)
            
            self.set_fill_color(*SEVERITY_COLORS[info['severity']])
            self.set_text_color(255, 255, 255)
            self.set_font("helvetica", "B", 8)
            self.cell(30, 8, info['severity'], border=1, fill=True, align="C")
            
            self.set_text_color(0, 0, 0)
            self.set_font("helvetica", "", 8)
            self.cell(25, 8, str(info['cvss']), border=1, align="C")
            self.cell(55, 8, info['owasp'], border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)
    
    def detailed_findings(self, findings):
        self.add_page()
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, "3. Detailed Findings & Remediation", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        
        for idx, item in enumerate(findings, 1):
            info = VULN_DATABASE.get(item['id'])
            if not info:
                continue
            
            if self.get_y() > 235:
                self.add_page()
            
            # Title
            self.set_font("helvetica", "B", 11)
            self.set_fill_color(240, 240, 240)
            self.set_text_color(0, 0, 0)
            self.cell(0, 8, f"{idx}. {info['title']}", border="B", fill=True, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
            
            # Details
            self.kv_block("Severity:", info['severity'], SEVERITY_COLORS[info['severity']])
            self.kv_block("CVSS Score:", info['cvss'])
            self.kv_block("Reference:", f"{info['cwe']}  |  {info['owasp']}")
            self.kv_block("Affected Endpoint:", f"{self.target_url}/{item['path']}")
            
            # Impact
            self.set_font("helvetica", "B", 9)
            self.cell(0, 5, "Description & Impact:", new_x="LMARGIN", new_y="NEXT")
            self.set_font("helvetica", "", 9)
            self.multi_cell(0, 5, info['impact'], new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
            
            # Remediation
            self.set_font("helvetica", "B", 9)
            self.set_text_color(0, 102, 51)
            self.cell(0, 5, "Enterprise Remediation:", new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(0, 0, 0)
            self.set_font("helvetica", "", 9)
            self.multi_cell(0, 5, info['remediation'], new_x="LMARGIN", new_y="NEXT")
            self.ln(6)
            
            # Separator
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="DOOM - Full DVWA Vulnerability Scanner")
    parser.add_argument("-u", "--url", default="http://127.8.0.1", help="Target URL (default: http://127.8.0.1)")
    parser.add_argument("-o", "--output", help="Output PDF filename")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (default: 0.5s)")
    parser.add_argument("--stealth", action="store_true", help="Enable stealth mode (random delays)")
    parser.add_argument("--level", default="low", choices=['low', 'medium', 'high', 'impossible'], help="DVWA security level")
    parser.add_argument("--no-login", action="store_true", help="Skip DVWA login")
    args = parser.parse_args()
    
    # Display banner and loading
    UI.banner()
    UI.loading()
    
    # Initialize scanner
    scanner = DVWAScanner(args.url, delay=args.delay, stealth=args.stealth)
    
    # Login to DVWA
    if not args.no_login:
        UI.info("Attempting automated DVWA authentication...")
        if scanner.login():
            UI.info("Authentication successful")
            scanner.set_security_level(args.level)
            UI.info(f"Security level set to: {args.level}")
        else:
            UI.warning("Login failed - continuing without authentication")
    
    print()
    UI.info(f"Starting comprehensive scan of {args.url}")
    print("=" * 65)
    
    # Run full scan
    findings = scanner.run_full_scan()
    
    print()
    print("=" * 65)
    UI.info(f"Scan completed! {len(findings)} vulnerabilities discovered")
    
    # Calculate threat score
    if findings:
        cvss_vals = [VULN_DATABASE[f['id']]['cvss'] for f in findings if f['id'] in VULN_DATABASE]
        if cvss_vals:
            threat_score = round(min(10.0, max(cvss_vals) * 0.7 + (sum(cvss_vals)/len(cvss_vals)) * 0.3), 1)
        else:
            threat_score = 0.0
    else:
        threat_score = 0.0
    
    UI.info(f"Threat Score: {threat_score}/10.0")
    
    # Generate report
    output_file = args.output or f"DOOM_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    UI.info("Generating enterprise PDF report...")
    
    Animator.start("Generating PDF report")
    try:
        pdf = EnterpriseReporter(args.url)
        pdf.executive_summary(findings, threat_score)
        pdf.summary_table(findings)
        pdf.detailed_findings(findings)
        pdf.output(output_file)
        Animator.stop(True)
        UI.info(f"Report saved to: {output_file}")
    except Exception as e:
        Animator.stop(False)
        UI.error(f"Report generation failed: {e}")
    
    # Final summary
    print()
    print("=" * 65)
    print(Fore.CYAN + "SCAN COMPLETE - DOOM REPORT SUMMARY")
    print("-" * 65)
    print(f"Target: {args.url}")
    print(f"Findings: {len(findings)}")
    print(f"Threat Score: {threat_score}/10.0")
    print(f"Report: {output_file}")
    print("=" * 65)


if __name__ == "__main__":
    main()
