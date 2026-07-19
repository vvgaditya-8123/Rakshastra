"""Threat Intelligence RAG (Retrieval-Augmented Generation).

FTS5-backed document store that indexes CVE databases, CERT-In advisories,
and APT campaign reports, integrated with Qdrant vector database for semantic search.

Uses Qdrant vector search first (with fallback to SQLite FTS5 BM25 ranking).
Supports OpenAI, Gemini, and Hugging Face Serverless Inference API for embeddings.
"""

import os
import json
import uuid
import sqlite3
import random
import hashlib
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional


class ThreatIntelRAG:
    """Hybrid threat intelligence retrieval engine (Qdrant vector search + SQLite FTS5)."""

    def __init__(self, db_path, qdrant_url=None):
        self._memory_conn = None
        if db_path == ":memory:":
            self.db_path = db_path
            # Keep a persistent connection for in-memory DB so schema persists
            self._memory_conn = sqlite3.connect(":memory:")
            self._memory_conn.row_factory = sqlite3.Row
        else:
            self.db_path = str(Path(db_path))
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.qdrant_url = qdrant_url or os.environ.get("QDRANT_URL", "http://localhost:6333")
        self._ensure_schema()
        
        # Test connection and initialize Qdrant
        self.qdrant_enabled = self._init_qdrant()
        
        self._seed_if_empty()

    def _get_connection(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _close_connection(self, conn: sqlite3.Connection) -> None:
        if self._memory_conn is None:
            conn.close()

    def _ensure_schema(self) -> None:
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS rag_documents (
                    id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    published_date TEXT DEFAULT '',
                    severity TEXT DEFAULT '',
                    tags TEXT DEFAULT '[]',
                    cve_ids TEXT DEFAULT '[]',
                    apt_groups TEXT DEFAULT '[]',
                    affected_products TEXT DEFAULT '[]',
                    mitigations TEXT DEFAULT ''
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS rag_documents_fts USING fts5(
                    id UNINDEXED,
                    title,
                    content,
                    tags,
                    cve_ids,
                    apt_groups,
                    tokenize="unicode61"
                );

                CREATE TRIGGER IF NOT EXISTS rag_ai AFTER INSERT ON rag_documents BEGIN
                    INSERT INTO rag_documents_fts(id, title, content, tags, cve_ids, apt_groups)
                    VALUES (new.id, new.title, new.content, new.tags, new.cve_ids, new.apt_groups);
                END;

                CREATE TRIGGER IF NOT EXISTS rag_ad AFTER DELETE ON rag_documents BEGIN
                    DELETE FROM rag_documents_fts WHERE id = old.id;
                END;

                CREATE TRIGGER IF NOT EXISTS rag_au AFTER UPDATE ON rag_documents BEGIN
                    DELETE FROM rag_documents_fts WHERE id = old.id;
                    INSERT INTO rag_documents_fts(id, title, content, tags, cve_ids, apt_groups)
                    VALUES (new.id, new.title, new.content, new.tags, new.cve_ids, new.apt_groups);
                END;
            """)
        finally:
            self._close_connection(conn)

    def _get_embedding_dimension(self) -> int:
        """Dynamically determine embedding dimension size depending on active provider."""
        if os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY"):
            model = os.environ.get("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            if "large" in model:
                return 1024
            return 384
        if os.environ.get("OPENAI_API_KEY"):
            return 1536
        if os.environ.get("GEMINI_API_KEY"):
            return 1536
        return 1536  # Default fallback size

    def _init_qdrant(self) -> bool:
        """Initialize Qdrant collection for semantic vector search."""
        try:
            resp = requests.get(f"{self.qdrant_url}/collections", timeout=1.5)
            if resp.status_code != 200:
                return False
            
            vector_size = self._get_embedding_dimension()
            collections = [c["name"] for c in resp.json().get("result", {}).get("collections", [])]
            if "threat_intel" not in collections:
                create_resp = requests.put(
                    f"{self.qdrant_url}/collections/threat_intel",
                    json={
                        "vectors": {
                            "size": vector_size,
                            "distance": "Cosine"
                        }
                    },
                    timeout=2.0
                )
                return create_resp.status_code == 200
            return True
        except Exception:
            return False

    def _get_embeddings(self, text: str) -> List[float]:
        """Generate an embedding vector for text using Hugging Face, OpenAI, or Gemini APIs."""
        # 1. Try Hugging Face Inference API
        hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
        if hf_token:
            try:
                model_id = os.environ.get("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
                headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
                resp = requests.post(
                    f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}",
                    headers=headers,
                    json={"inputs": text},
                    timeout=5.0
                )
                if resp.status_code == 200:
                    embeddings = resp.json()
                    if isinstance(embeddings, list):
                        if len(embeddings) > 0 and isinstance(embeddings[0], list):
                            return embeddings[0]
                        return embeddings
            except Exception:
                pass

        # 2. Try OpenAI Embeddings
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            try:
                headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
                resp = requests.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=headers,
                    json={"input": text, "model": "text-embedding-3-small"},
                    timeout=4.0
                )
                if resp.status_code == 200:
                    return resp.json()["data"][0]["embedding"]
            except Exception:
                pass

        # 3. Try Gemini Embeddings
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={gemini_key}"
                resp = requests.post(
                    url,
                    json={"content": {"parts": [{"text": text}]}},
                    timeout=4.0
                )
                if resp.status_code == 200:
                    return resp.json()["embedding"]["values"]
            except Exception:
                pass

        # 4. Fallback: Deterministic vector generated from text hash (L2 Normalized)
        h = hashlib.sha256(text.encode('utf-8')).hexdigest()
        seed = int(h, 16) % (2**32)
        rng = random.Random(seed)
        dim = self._get_embedding_dimension()
        vec = [rng.uniform(-1, 1) for _ in range(dim)]
        norm = sum(x*x for x in vec) ** 0.5
        return [x/norm for x in vec]

    # ── Seeding ──────────────────────────────────────────────────────────

    def _seed_if_empty(self) -> None:
        conn = self._get_connection()
        try:
            count = conn.execute("SELECT COUNT(*) AS c FROM rag_documents").fetchone()["c"]
            if count > 0:
                # If SQLite is already populated but Qdrant is newly enabled,
                # sync SQLite records to Qdrant.
                if self.qdrant_enabled:
                    self._sync_sqlite_to_qdrant()
                return
        finally:
            self._close_connection(conn)

        self._seed_certin_advisories()
        self._seed_cve_entries()
        self._seed_campaign_reports()

    def _sync_sqlite_to_qdrant(self) -> None:
        """Sync SQLite documents to Qdrant vector database."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM rag_documents").fetchall()
            for r in rows:
                doc = self._row_to_dict(r)
                # Re-ingest to sync to Qdrant
                self.ingest_advisory(
                    doc_id=doc["id"],
                    source_type=doc["source_type"],
                    title=doc["title"],
                    content=doc["content"],
                    published_date=doc.get("published_date", ""),
                    severity=doc.get("severity", ""),
                    tags=doc.get("tags", []),
                    cve_ids=doc.get("cve_ids", []),
                    apt_groups=doc.get("apt_groups", []),
                    affected_products=doc.get("affected_products", []),
                    mitigations=doc.get("mitigations", "")
                )
        except Exception:
            pass
        finally:
            self._close_connection(conn)

    def _seed_certin_advisories(self) -> None:
        advisories = [
            ("CIAD-2024-0001", "cert_in", "Advisory on SideWinder APT Targeting Indian Government",
             "CERT-In has observed SideWinder (APT-T-04) actively targeting Indian government organisations and military establishments through spearphishing campaigns using weaponised RTF documents exploiting CVE-2017-11882. The threat actor deploys custom HTA-based downloaders for initial access followed by credential harvesting using modified Mimikatz variants. Organisations are advised to patch Microsoft Office immediately, enable macro restrictions, deploy email gateway filtering for RTF attachments, and monitor for suspicious HTA process execution chains.",
             "2024-03-15", "HIGH", ["apt","sidewinder","spearphishing","indian_government"],
             ["CVE-2017-11882"], ["SideWinder","APT-T-04"], ["Microsoft Office"],
             "Patch CVE-2017-11882, block HTA execution, enable email attachment scanning."),

            ("CIAD-2024-0002", "cert_in", "Advisory on Transparent Tribe Operations Against Indian Defence Sector",
             "CERT-In has identified ongoing Transparent Tribe (APT36) operations targeting the Indian defence sector. The group uses CrimsonRAT and ObliqueRAT delivered via spearphishing emails with defence-themed lure documents. The RATs establish persistence via registry run keys and scheduled tasks, perform keylogging, screen capture, and exfiltrate sensitive documents. CERT-In recommends implementing application whitelisting, monitoring outbound connections to Pakistani IP ranges, and deploying EDR solutions.",
             "2024-04-22", "CRITICAL", ["apt","transparent_tribe","apt36","defence","crimsonrat"],
             [], ["Transparent Tribe","APT36"], ["Windows endpoints"],
             "Deploy EDR, application whitelisting, monitor outbound connections to suspicious geographies."),

            ("CIAD-2024-0003", "cert_in", "Alert on Increased Phishing Campaigns Targeting Indian Banking Sector",
             "CERT-In warns of a significant increase in phishing campaigns targeting Indian banking and financial institutions. Attackers use SMS and email phishing with fake KYC verification pages mimicking RBI and major bank portals. Stolen credentials are used for unauthorised fund transfers. Banks are advised to implement transaction monitoring, deploy anti-phishing solutions, and conduct customer awareness campaigns.",
             "2024-05-10", "HIGH", ["phishing","banking","finance","kyc_fraud"],
             [], [], ["Banking portals","UPI applications"],
             "Deploy anti-phishing gateway, conduct user awareness training, implement transaction anomaly detection."),

            ("CIAD-2024-0004", "cert_in", "Advisory on DoNot Team APT Targeting South Asian Governments",
             "CERT-In has observed DoNot Team (APT-C-35) conducting espionage operations against South Asian government entities using the yty malware framework. Initial access is via spearphishing with macro-enabled Office documents. The framework deploys multiple modules for keylogging, browser credential theft, file collection, and USB drive data theft. The malware uses HTTP-based C2 communication with hardcoded domains. Organisations should monitor for suspicious Office macro execution and implement DNS sinkholing.",
             "2024-06-05", "HIGH", ["apt","donot_team","apt-c-35","espionage","yty_framework"],
             [], ["DoNot Team","APT-C-35"], ["Microsoft Office","Windows"],
             "Block Office macros, DNS sinkholing for C2 domains, monitor USB device activity."),

            ("CIAD-2024-0005", "cert_in", "Advisory on MuddyWater Targeting Indian Energy and Telecom Sectors",
             "CERT-In has identified MuddyWater (MERCURY/Mango Sandstorm) targeting Indian energy and telecommunications organisations. The group uses macro-laced Office documents and PowerShell-based first-stage payloads (POWERSTATS). Lateral movement is achieved through RDP and administrative shares. CERT-In recommends restricting PowerShell execution, implementing network segmentation between IT and OT networks, and monitoring for unusual RDP connections.",
             "2024-07-12", "CRITICAL", ["apt","muddywater","energy","telecom","powershell"],
             [], ["MuddyWater","MERCURY","Mango Sandstorm"], ["Energy SCADA","Telecom systems"],
             "Restrict PowerShell, segment IT/OT networks, monitor RDP connections, deploy network IDS."),

            ("CIAD-2024-0006", "cert_in", "Alert on Ransomware Targeting Indian Healthcare Organisations",
             "CERT-In has observed targeted ransomware campaigns against Indian healthcare organisations using LockBit and BlackCat/ALPHV variants. Initial access is through exploiting unpatched VPN concentrators and RDP brute force. Attackers establish persistence, move laterally via SMB, and deploy ransomware after exfiltrating sensitive patient data. Healthcare organisations must maintain offline backups, patch VPN devices, disable unnecessary RDP, and implement network segmentation.",
             "2024-08-20", "CRITICAL", ["ransomware","healthcare","lockbit","alphv","vpn"],
             ["CVE-2023-46805","CVE-2024-21887"], [], ["VPN concentrators","Windows servers"],
             "Patch VPN appliances, disable RDP, maintain offline backups, segment medical device networks."),

            ("CIAD-2024-0007", "cert_in", "Advisory on Chinese APT Groups Targeting Indian Critical Infrastructure",
             "CERT-In has observed multiple Chinese APT groups (APT41, GALLIUM, Mustang Panda) conducting operations against Indian critical infrastructure including power grid, telecommunications, and transportation sectors. The groups exploit public-facing applications, deploy web shells for persistence, and use custom backdoors for long-term espionage. CERT-In recommends comprehensive vulnerability scanning of internet-facing assets, web application firewall deployment, and monitoring for web shell indicators.",
             "2024-09-15", "CRITICAL", ["apt","china","critical_infrastructure","web_shell","espionage"],
             [], ["APT41","GALLIUM","Mustang Panda"], ["Web servers","SCADA systems"],
             "Deploy WAF, scan for web shells, monitor DNS for C2 beaconing, implement zero-trust architecture."),

            ("CIAD-2024-0008", "cert_in", "Advisory on Supply Chain Attacks Targeting Indian IT Service Providers",
             "CERT-In has identified sophisticated supply chain attacks targeting Indian IT service providers and managed service providers (MSPs). Threat actors compromise update mechanisms and deploy backdoored software updates to downstream customers. The attack mirrors techniques used in SolarWinds and Kaseya incidents. IT service providers must implement code signing verification, secure CI/CD pipelines, and monitor software update integrity.",
             "2024-10-01", "CRITICAL", ["supply_chain","msp","it_services","backdoor"],
             [], [], ["CI/CD pipelines","Software update servers"],
             "Implement code signing, secure CI/CD, verify update integrity, deploy SBOM analysis."),

            ("CIAD-2024-0009", "cert_in", "Alert on Patchwork APT Targeting Indian Think Tanks and Research Institutions",
             "CERT-In warns of Patchwork (Dropping Elephant) APT targeting Indian think tanks, policy research institutions, and academic organisations studying China-India relations. The group uses BADNEWS RAT delivered via spearphishing with geopolitical-themed lure documents. The malware exfiltrates documents matching specific keywords related to foreign policy, border disputes, and defence procurement.",
             "2024-11-08", "HIGH", ["apt","patchwork","think_tanks","academia","badnews_rat"],
             [], ["Patchwork","Dropping Elephant"], ["Windows workstations"],
             "Deploy DLP for sensitive documents, email gateway scanning, application whitelisting."),

            ("CIAD-2025-0001", "cert_in", "Advisory on Kimsuky Targeting Indian Space and Nuclear Research",
             "CERT-In has identified Kimsuky (Velvet Chollima) conducting targeted operations against Indian space research and nuclear energy organisations. The group uses credential phishing via fake webmail portals and deploys custom malware for data exfiltration. CERT-In recommends implementing FIDO2 hardware security keys for email authentication and deploying network monitoring for data exfiltration indicators.",
             "2025-01-20", "CRITICAL", ["apt","kimsuky","space","nuclear","credential_phishing"],
             [], ["Kimsuky","Velvet Chollima","Emerald Sleet"], ["Email systems","Research databases"],
             "Deploy FIDO2 MFA, monitor for credential phishing domains, DLP for research data."),
        ]
        for adv in advisories:
            self.ingest_advisory(
                doc_id=adv[0],
                source_type=adv[1],
                title=adv[2],
                content=adv[3],
                published_date=adv[4],
                severity=adv[5],
                tags=adv[6],
                cve_ids=adv[7],
                apt_groups=adv[8],
                affected_products=adv[9],
                mitigations=adv[10]
            )

    def _seed_cve_entries(self) -> None:
        cves = [
            ("CVE-2021-44228", "cve", "Log4Shell — Apache Log4j Remote Code Execution",
             "Apache Log4j2 versions 2.0-beta9 through 2.14.1 contain a critical remote code execution vulnerability via JNDI LDAP lookup in log messages. An attacker who can control log messages or log message parameters can execute arbitrary code loaded from LDAP servers. This vulnerability has been widely exploited by APT groups including HAFNIUM and APT41 for initial access to enterprise environments. CVSS Score: 10.0. Immediate patching to Log4j 2.17.1+ is required.",
             "2021-12-10", "CRITICAL", ["rce","log4j","java","jndi"],
             ["CVE-2021-44228"], ["HAFNIUM","APT41"], ["Apache Log4j"],
             "Upgrade Log4j to 2.17.1+, set log4j2.formatMsgNoLookups=true, deploy WAF rules."),

            ("CVE-2023-46805", "cve", "Ivanti Connect Secure Authentication Bypass",
             "Ivanti Connect Secure (formerly Pulse Secure) VPN appliances contain an authentication bypass vulnerability that allows unauthenticated attackers to access restricted resources. When chained with CVE-2024-21887 (command injection), attackers achieve remote code execution. Actively exploited by Chinese state-sponsored actors and ransomware groups for initial access to enterprise networks.",
             "2024-01-10", "CRITICAL", ["vpn","authentication_bypass","ivanti","pulse_secure"],
             ["CVE-2023-46805","CVE-2024-21887"], [], ["Ivanti Connect Secure"],
             "Apply Ivanti patches immediately, deploy integrity checking tool, monitor for web shells."),

            ("CVE-2023-34362", "cve", "MOVEit Transfer SQL Injection (Cl0p Ransomware)",
             "Progress MOVEit Transfer contains a SQL injection vulnerability that allows unauthenticated attackers to gain access to the database and execute arbitrary code. Widely exploited by the Cl0p ransomware group in mass exploitation campaigns affecting thousands of organisations globally.",
             "2023-06-02", "CRITICAL", ["sqli","moveit","file_transfer","cl0p"],
             ["CVE-2023-34362"], [], ["MOVEit Transfer"],
             "Patch MOVEit Transfer, audit file transfer logs, block IOCs."),

            ("CVE-2024-3400", "cve", "Palo Alto PAN-OS GlobalProtect Command Injection",
             "Palo Alto Networks PAN-OS GlobalProtect feature contains a command injection vulnerability allowing unauthenticated attackers to execute arbitrary code with root privileges on the firewall. Actively exploited in the wild by UTA0218 threat actor.",
             "2024-04-12", "CRITICAL", ["firewall","command_injection","paloalto","globalprotect"],
             ["CVE-2024-3400"], [], ["PAN-OS"],
             "Apply PAN-OS hotfix, enable Threat Prevention signatures, disable GlobalProtect if not needed."),

            ("CVE-2017-11882", "cve", "Microsoft Office Equation Editor Memory Corruption",
             "Microsoft Office Equation Editor contains a memory corruption vulnerability allowing remote code execution via specially crafted documents. Despite being patched in 2017, this vulnerability continues to be heavily exploited by APT groups including SideWinder, Patchwork, and Transparent Tribe in campaigns targeting South Asian governments.",
             "2017-11-14", "HIGH", ["office","equation_editor","memory_corruption","rtf"],
             ["CVE-2017-11882"], ["SideWinder","Patchwork","Transparent Tribe"], ["Microsoft Office"],
             "Patch Microsoft Office, disable Equation Editor component, block RTF attachments."),

            ("CVE-2021-26855", "cve", "Microsoft Exchange Server ProxyLogon SSRF",
             "Microsoft Exchange Server contains a server-side request forgery (SSRF) vulnerability that allows unauthenticated attackers to send arbitrary HTTP requests and authenticate as the Exchange server. Chained with additional vulnerabilities (ProxyLogon chain) for complete server compromise. Exploited by HAFNIUM and multiple other threat actors.",
             "2021-03-02", "CRITICAL", ["exchange","ssrf","proxylogon","email"],
             ["CVE-2021-26855"], ["HAFNIUM","APT41"], ["Microsoft Exchange Server"],
             "Apply Exchange CU patches, scan for web shells, enable Enhanced Protection."),

            ("CVE-2023-23397", "cve", "Microsoft Outlook Privilege Escalation (NTLM Relay)",
             "Microsoft Outlook contains a critical elevation of privilege vulnerability where a specially crafted email can trigger NTLM authentication relay without user interaction. Exploited by APT28 (Forest Blizzard) against European government and military targets.",
             "2023-03-14", "CRITICAL", ["outlook","ntlm","privilege_escalation","email"],
             ["CVE-2023-23397"], ["APT28","Forest Blizzard"], ["Microsoft Outlook"],
             "Patch Outlook, block outbound NTLM to external IPs, deploy detection script."),

            ("CVE-2022-30190", "cve", "Follina — MSDT Remote Code Execution",
             "A remote code execution vulnerability exists in the Microsoft Support Diagnostic Tool (MSDT) when called via URL protocol from applications like Word. Weaponised documents can execute arbitrary PowerShell without macros enabled. Exploited by multiple APT groups.",
             "2022-05-30", "HIGH", ["msdt","follina","office","powershell"],
             ["CVE-2022-30190"], ["APT28","Sandworm"], ["Microsoft Office","MSDT"],
             "Disable MSDT URL protocol, apply Microsoft patch, monitor for MSDT process execution."),

            ("CVE-2024-21887", "cve", "Ivanti Connect Secure Command Injection",
             "Ivanti Connect Secure and Ivanti Policy Secure contain a command injection vulnerability in web components allowing authenticated administrators to execute arbitrary commands. When chained with CVE-2023-46805 (auth bypass), unauthenticated RCE is achieved.",
             "2024-01-10", "CRITICAL", ["vpn","command_injection","ivanti"],
             ["CVE-2024-21887"], [], ["Ivanti Connect Secure","Ivanti Policy Secure"],
             "Apply patches, run integrity checker, factory reset if compromise detected."),

            ("CVE-2023-4966", "cve", "Citrix Bleed — NetScaler Information Disclosure",
             "Citrix NetScaler ADC and NetScaler Gateway contain a buffer overflow vulnerability allowing unauthenticated attackers to extract sensitive information including session tokens. Exploited by LockBit ransomware affiliates and state-sponsored actors.",
             "2023-10-10", "CRITICAL", ["citrix","netscaler","session_hijack","buffer_overflow"],
             ["CVE-2023-4966"], [], ["Citrix NetScaler ADC","Citrix NetScaler Gateway"],
             "Patch NetScaler, kill all active sessions, rotate certificates."),
        ]
        for cve in cves:
            self.ingest_advisory(
                doc_id=cve[0],
                source_type=cve[1],
                title=cve[2],
                content=cve[3],
                published_date=cve[4],
                severity=cve[5],
                tags=cve[6],
                cve_ids=cve[7],
                apt_groups=cve[8],
                affected_products=cve[9],
                mitigations=cve[10]
            )

    def _seed_campaign_reports(self) -> None:
        reports = [
            ("RPT-2024-001", "campaign_report", "Operation Honey Trap: Transparent Tribe Targets Indian Defence in 2024",
             "Transparent Tribe (APT36) continues to target Indian defence and government organisations through sophisticated social engineering campaigns. The group operates CrimsonRAT, ObliqueRAT, and a new Android malware variant targeting military personnel's mobile devices. The campaign uses defence procurement-themed lure documents and fake job portals targeting armed forces personnel. Key IOCs include C2 servers hosted in Pakistani IP space and domains mimicking Indian government portals. The group's TTPs include T1566.001 (Spearphishing Attachment), T1204 (User Execution), T1059.001 (PowerShell), T1547.001 (Registry Run Keys), T1056 (Keylogging), T1113 (Screen Capture), and T1041 (Exfiltration Over C2).",
             "2024-06-15", "CRITICAL", ["apt36","transparent_tribe","india","defence","crimsonrat"],
             [], ["Transparent Tribe","APT36"], ["Windows endpoints","Android devices"],
             "Deploy mobile device management, email gateway scanning, endpoint detection and response."),

            ("RPT-2024-002", "campaign_report", "SideWinder APT: Evolution of Tactics Against South Asian Targets",
             "SideWinder has evolved its toolkit to include server-side exploits and living-off-the-land techniques alongside its traditional client-side exploitation approach. The group now leverages HTA downloaders, .NET-based implants, and steganography for payload delivery. New campaigns target Pakistani military, Chinese government, and Nepali diplomatic entities. The group demonstrates increasing sophistication with multi-stage infection chains and anti-analysis techniques. Attribution confidence: HIGH based on infrastructure overlap, code reuse, and targeting patterns.",
             "2024-08-20", "HIGH", ["sidewinder","south_asia","hta","steganography","anti_analysis"],
             ["CVE-2017-11882"], ["SideWinder","Razor Tiger"], ["Windows endpoints"],
             "Monitor for HTA execution, implement macro controls, deploy network traffic analysis."),

            ("RPT-2024-003", "campaign_report", "Chinese APT Activity Against Indian Infrastructure: 2024 Landscape",
             "Multiple Chinese APT groups continue to target Indian critical infrastructure. APT41 targets healthcare and pharmaceutical research. GALLIUM targets telecommunications providers. Mustang Panda focuses on government and NGO targets. Common TTPs include exploitation of internet-facing applications (T1190), web shell deployment (T1505.003), and use of legitimate cloud services for C2 (T1071.001). The groups demonstrate coordination in target selection and shared infrastructure use, suggesting possible centralised tasking by Chinese intelligence services.",
             "2024-10-01", "CRITICAL", ["china","apt41","gallium","mustang_panda","india","critical_infrastructure"],
             [], ["APT41","GALLIUM","Mustang Panda"], ["Web servers","Telecom infrastructure"],
             "Implement zero-trust, scan internet-facing assets, deploy web shell detection."),

            ("RPT-2024-004", "campaign_report", "Ransomware Landscape in India: LockBit, BlackCat and Emerging Threats",
             "India faces an escalating ransomware threat with LockBit 3.0, BlackCat/ALPHV, and emerging groups targeting healthcare, financial services, and manufacturing. Attack vectors include exploitation of unpatched VPN appliances (Ivanti, Fortinet, Citrix), RDP brute force, and phishing with ISO/LNK attachments. Average dwell time is 12 days. Double extortion is standard practice. CERT-In reported a 53% increase in ransomware incidents targeting Indian organisations in 2024. Key mitigations: offline backups, network segmentation, MFA on all remote access, patch management program.",
             "2024-11-15", "CRITICAL", ["ransomware","lockbit","blackcat","india","healthcare","finance"],
             ["CVE-2023-46805","CVE-2024-21887","CVE-2023-4966"], [],
             ["VPN appliances","Windows servers","Active Directory"],
             "Implement offline backups, patch VPN appliances, deploy EDR, enable MFA."),

            ("RPT-2025-001", "campaign_report", "APT28 Forest Blizzard: Global Campaign Analysis 2025",
             "APT28 (Forest Blizzard/Fancy Bear) continues global espionage operations with updated tooling including custom Go-based implants and exploitation of cloud services. Key techniques include OAuth token theft via spearphishing (T1566.002), exploitation of CVE-2023-23397 for NTLM relay attacks, and abuse of Microsoft Graph API for C2 communication. Primary targets include European government, NATO organisations, and defence contractors. The group maintains overlapping infrastructure with Sandworm Team for disruptive operations.",
             "2025-02-10", "CRITICAL", ["apt28","forest_blizzard","fancy_bear","europe","nato"],
             ["CVE-2023-23397"], ["APT28","Forest Blizzard","Fancy Bear"],
             ["Microsoft 365","Government networks"],
             "Enforce FIDO2 MFA, block outbound NTLM, monitor Microsoft Graph API abuse."),
        ]
        for rpt in reports:
            self.ingest_advisory(
                doc_id=rpt[0],
                source_type=rpt[1],
                title=rpt[2],
                content=rpt[3],
                published_date=rpt[4],
                severity=rpt[5],
                tags=rpt[6],
                cve_ids=rpt[7],
                apt_groups=rpt[8],
                affected_products=rpt[9],
                mitigations=rpt[10]
            )

    # ── Query API ────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search threat intelligence documents. Try Qdrant vector search first, fall back to SQLite FTS5."""
        if self.qdrant_enabled:
            try:
                vector = self._get_embeddings(query)
                resp = requests.post(
                    f"{self.qdrant_url}/collections/threat_intel/points/search",
                    json={
                        "vector": vector,
                        "limit": top_k,
                        "with_payload": True
                    },
                    timeout=3.0
                )
                if resp.status_code == 200:
                    results = resp.json().get("result", [])
                    return [r["payload"] for r in results if r.get("payload")]
            except Exception:
                pass

        # Fallback to SQLite FTS5 search
        conn = self._get_connection()
        try:
            clean = query.replace('"', '""')
            escaped = f'"{clean}"'
            rows = conn.execute(
                """SELECT d.*, rank
                   FROM rag_documents d
                   JOIN rag_documents_fts f ON d.id = f.id
                   WHERE rag_documents_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (escaped, top_k),
            ).fetchall()

            if not rows:
                words = query.strip().split()
                if len(words) > 1:
                    or_query = " OR ".join(f'"{w}"' for w in words if len(w) > 2)
                    if or_query:
                        rows = conn.execute(
                            """SELECT d.*, rank
                               FROM rag_documents d
                               JOIN rag_documents_fts f ON d.id = f.id
                               WHERE rag_documents_fts MATCH ?
                               ORDER BY rank
                               LIMIT ?""",
                            (or_query, top_k),
                        ).fetchall()

            return [self._row_to_dict(r) for r in rows]
        finally:
            self._close_connection(conn)

    def search_by_cve(self, cve_id: str) -> List[Dict[str, Any]]:
        """Search for documents mentioning a specific CVE."""
        conn = self._get_connection()
        try:
            q = f"%{cve_id}%"
            rows = conn.execute(
                "SELECT * FROM rag_documents WHERE cve_ids LIKE ? OR content LIKE ? ORDER BY published_date DESC",
                (q, q),
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            self._close_connection(conn)

    def search_by_apt_group(self, group_name: str) -> List[Dict[str, Any]]:
        """Search for documents mentioning a specific APT group."""
        conn = self._get_connection()
        try:
            q = f"%{group_name}%"
            rows = conn.execute(
                "SELECT * FROM rag_documents WHERE apt_groups LIKE ? OR content LIKE ? ORDER BY published_date DESC",
                (q, q),
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            self._close_connection(conn)

    def search_by_source_type(self, source_type: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve documents by source type (cert_in, cve, campaign_report)."""
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM rag_documents WHERE source_type = ? ORDER BY published_date DESC LIMIT ?",
                (source_type, limit),
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            self._close_connection(conn)

    def get_context_for_attribution(
        self, ttps: List[str], iocs: Optional[List[str]] = None, group_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant threat intel context to support attribution analysis."""
        results: List[Dict[str, Any]] = []
        seen_ids: set = set()

        # Search by group name
        if group_name:
            for doc in self.search_by_apt_group(group_name):
                if doc["id"] not in seen_ids:
                    seen_ids.add(doc["id"])
                    results.append(doc)

        # Search by TTPs
        ttp_str = " ".join(ttps[:5])
        if ttp_str.strip():
            for doc in self.search(ttp_str, top_k=5):
                if doc["id"] not in seen_ids:
                    seen_ids.add(doc["id"])
                    results.append(doc)

        # Search by IOCs
        if iocs:
            for ioc in iocs[:3]:
                for doc in self.search(ioc, top_k=3):
                    if doc["id"] not in seen_ids:
                        seen_ids.add(doc["id"])
                        results.append(doc)

        return results[:15]  # Cap at 15 results

    def ingest_advisory(
        self,
        doc_id: str,
        source_type: str,
        title: str,
        content: str,
        published_date: str = "",
        severity: str = "",
        tags: Optional[List[str]] = None,
        cve_ids: Optional[List[str]] = None,
        apt_groups: Optional[List[str]] = None,
        affected_products: Optional[List[str]] = None,
        mitigations: str = "",
    ) -> str:
        """Ingest a new advisory/document into the RAG store. Syncs to Qdrant vector DB if active."""
        tags = tags or []
        cve_ids = cve_ids or []
        apt_groups = apt_groups or []
        affected_products = affected_products or []

        # 1. Ingest to SQLite
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO rag_documents
                   (id, source_type, title, content, published_date, severity, tags, cve_ids, apt_groups, affected_products, mitigations)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    doc_id, source_type, title, content, published_date, severity,
                    json.dumps(tags), json.dumps(cve_ids),
                    json.dumps(apt_groups), json.dumps(affected_products),
                    mitigations,
                ),
            )
            if self._memory_conn is None:
                conn.commit()
        finally:
            self._close_connection(conn)

        # 2. Sync to Qdrant if enabled
        if self.qdrant_enabled:
            try:
                vector = self._get_embeddings(content)
                # Generate deterministic UUID based on doc_id
                pt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))
                payload = {
                    "id": doc_id,
                    "source_type": source_type,
                    "title": title,
                    "content": content,
                    "published_date": published_date,
                    "severity": severity,
                    "tags": tags,
                    "cve_ids": cve_ids,
                    "apt_groups": apt_groups,
                    "affected_products": affected_products,
                    "mitigations": mitigations
                }
                requests.put(
                    f"{self.qdrant_url}/collections/threat_intel/points?wait=true",
                    json={
                        "points": [
                            {
                                "id": pt_id,
                                "vector": vector,
                                "payload": payload
                            }
                        ]
                    },
                    timeout=3.0
                )
            except Exception:
                pass

        return doc_id

    def get_summary(self) -> Dict[str, Any]:
        """Return summary statistics of the RAG store."""
        conn = self._get_connection()
        try:
            total = conn.execute("SELECT COUNT(*) AS c FROM rag_documents").fetchone()["c"]
            by_type = {}
            for row in conn.execute("SELECT source_type, COUNT(*) AS c FROM rag_documents GROUP BY source_type").fetchall():
                by_type[row["source_type"]] = row["c"]
            by_severity = {}
            for row in conn.execute("SELECT severity, COUNT(*) AS c FROM rag_documents GROUP BY severity").fetchall():
                by_severity[row["severity"]] = row["c"]
            return {
                "total_documents": total,
                "by_source_type": by_type,
                "by_severity": by_severity,
                "qdrant_connected": self.qdrant_enabled,
                "qdrant_url": self.qdrant_url if self.qdrant_enabled else None
            }
        finally:
            self._close_connection(conn)

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        for field in ("tags", "cve_ids", "apt_groups", "affected_products"):
            try:
                d[field] = json.loads(d.get(field) or "[]")
            except (json.JSONDecodeError, TypeError):
                d[field] = []
        return d
