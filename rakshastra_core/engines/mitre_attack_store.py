"""MITRE ATT&CK Knowledge Graph Store.

SQLite-backed knowledge graph containing the full MITRE ATT&CK matrix with
tactics, techniques, sub-techniques, groups (APT actors), software, and their
relationships.  Pre-populated on first initialisation so the agent can
attribute observed TTPs to known campaigns without an external API call.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class MitreAttackStore:
    """SQLite-backed MITRE ATT&CK knowledge graph."""

    def __init__(self, db_path):
        if db_path == ":memory:":
            self.db_path = db_path
        else:
            self.db_path = str(Path(db_path))
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
        self._seed_if_empty()

    # ── Connection helpers ───────────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS mitre_tactics (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    phase_order INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS mitre_techniques (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    tactic_id TEXT,
                    description TEXT DEFAULT '',
                    is_subtechnique INTEGER DEFAULT 0,
                    parent_id TEXT DEFAULT '',
                    platforms TEXT DEFAULT '[]',
                    detection TEXT DEFAULT '',
                    data_sources TEXT DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS mitre_groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    aliases TEXT DEFAULT '[]',
                    description TEXT DEFAULT '',
                    country TEXT DEFAULT '',
                    target_sectors TEXT DEFAULT '[]',
                    target_countries TEXT DEFAULT '[]',
                    active_since TEXT DEFAULT '',
                    sophistication TEXT DEFAULT 'medium'
                );

                CREATE TABLE IF NOT EXISTS mitre_software (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    software_type TEXT DEFAULT 'malware',
                    description TEXT DEFAULT '',
                    platforms TEXT DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS mitre_group_techniques (
                    group_id TEXT,
                    technique_id TEXT,
                    usage_description TEXT DEFAULT '',
                    PRIMARY KEY (group_id, technique_id)
                );

                CREATE TABLE IF NOT EXISTS mitre_group_software (
                    group_id TEXT,
                    software_id TEXT,
                    PRIMARY KEY (group_id, software_id)
                );

                CREATE TABLE IF NOT EXISTS mitre_technique_mitigations (
                    technique_id TEXT,
                    mitigation_id TEXT,
                    mitigation_name TEXT,
                    description TEXT DEFAULT '',
                    PRIMARY KEY (technique_id, mitigation_id)
                );

                CREATE INDEX IF NOT EXISTS idx_techniques_tactic
                    ON mitre_techniques(tactic_id);
                CREATE INDEX IF NOT EXISTS idx_group_tech_group
                    ON mitre_group_techniques(group_id);
                CREATE INDEX IF NOT EXISTS idx_group_tech_tech
                    ON mitre_group_techniques(technique_id);
            """)
        finally:
            conn.close()

    # ── Seeding ──────────────────────────────────────────────────────────

    def _seed_if_empty(self) -> None:
        conn = self._get_connection()
        try:
            count = conn.execute("SELECT COUNT(*) AS c FROM mitre_tactics").fetchone()["c"]
            if count > 0:
                return
        finally:
            conn.close()

        self._seed_tactics()
        self._seed_techniques()
        self._seed_groups()
        self._seed_software()
        self._seed_group_techniques()
        self._seed_mitigations()

    def _seed_tactics(self) -> None:
        tactics = [
            ("TA0043", "Reconnaissance", "Gathering information to plan future operations.", 1),
            ("TA0042", "Resource Development", "Establishing resources to support operations.", 2),
            ("TA0001", "Initial Access", "Trying to get into the network.", 3),
            ("TA0002", "Execution", "Trying to run malicious code.", 4),
            ("TA0003", "Persistence", "Trying to maintain foothold.", 5),
            ("TA0004", "Privilege Escalation", "Trying to gain higher-level permissions.", 6),
            ("TA0005", "Defense Evasion", "Trying to avoid being detected.", 7),
            ("TA0006", "Credential Access", "Stealing account names and passwords.", 8),
            ("TA0007", "Discovery", "Trying to figure out the environment.", 9),
            ("TA0008", "Lateral Movement", "Trying to move through the environment.", 10),
            ("TA0009", "Collection", "Gathering data of interest.", 11),
            ("TA0011", "Command and Control", "Communicating with compromised systems.", 12),
            ("TA0010", "Exfiltration", "Stealing data.", 13),
            ("TA0040", "Impact", "Manipulate, interrupt, or destroy systems and data.", 14),
        ]
        conn = self._get_connection()
        try:
            conn.executemany(
                "INSERT OR IGNORE INTO mitre_tactics (id, name, description, phase_order) VALUES (?,?,?,?)",
                tactics,
            )
            conn.commit()
        finally:
            conn.close()

    def _seed_techniques(self) -> None:
        # fmt: off
        techniques = [
            # Reconnaissance
            ("T1595", "Active Scanning", "TA0043", "Scanning infrastructure to identify targets.", 0, "", '["all"]', "Monitor for suspicious network scans", '["network_traffic"]'),
            ("T1592", "Gather Victim Host Information", "TA0043", "Gathering host info before compromise.", 0, "", '["all"]', "Monitor for information gathering", '["web_logs"]'),
            ("T1589", "Gather Victim Identity Information", "TA0043", "Gathering user identity info.", 0, "", '["all"]', "Monitor phishing emails", '["email_logs"]'),
            # Initial Access
            ("T1566", "Phishing", "TA0001", "Sending phishing messages to gain access.", 0, "", '["windows","macos","linux"]', "Email filtering and user training", '["email_gateway"]'),
            ("T1566.001", "Spearphishing Attachment", "TA0001", "Sending targeted emails with malicious attachments.", 1, "T1566", '["windows","macos","linux"]', "Attachment scanning", '["email_gateway"]'),
            ("T1566.002", "Spearphishing Link", "TA0001", "Sending targeted emails with malicious links.", 1, "T1566", '["windows","macos","linux"]', "URL filtering", '["email_gateway","proxy"]'),
            ("T1190", "Exploit Public-Facing Application", "TA0001", "Exploiting vulnerabilities in internet-facing apps.", 0, "", '["windows","linux","containers"]', "WAF and vulnerability scanning", '["application_logs","waf"]'),
            ("T1133", "External Remote Services", "TA0001", "Using VPN/RDP/Citrix to gain access.", 0, "", '["windows","linux"]', "Monitor remote access logs", '["vpn_logs","auth_logs"]'),
            ("T1078", "Valid Accounts", "TA0001", "Using stolen or leaked credentials.", 0, "", '["windows","linux","macos","cloud"]', "Monitor for impossible travel", '["auth_logs"]'),
            ("T1199", "Trusted Relationship", "TA0001", "Abusing trusted third-party relationships.", 0, "", '["windows","linux","cloud"]', "Monitor third-party access", '["auth_logs"]'),
            ("T1195", "Supply Chain Compromise", "TA0001", "Manipulating products before delivery.", 0, "", '["windows","linux","macos"]', "Software integrity verification", '["file_integrity"]'),
            ("T1189", "Drive-by Compromise", "TA0001", "Compromising via visiting a website.", 0, "", '["windows","linux","macos"]', "Browser isolation", '["proxy_logs"]'),
            # Execution
            ("T1059", "Command and Scripting Interpreter", "TA0002", "Executing commands via interpreters.", 0, "", '["windows","linux","macos"]', "Script block logging", '["process_logs","script_logs"]'),
            ("T1059.001", "PowerShell", "TA0002", "Executing via PowerShell.", 1, "T1059", '["windows"]', "PowerShell logging", '["powershell_logs"]'),
            ("T1059.003", "Windows Command Shell", "TA0002", "Using cmd.exe.", 1, "T1059", '["windows"]', "Command line auditing", '["process_logs"]'),
            ("T1059.004", "Unix Shell", "TA0002", "Using bash/sh.", 1, "T1059", '["linux","macos"]', "Shell history monitoring", '["process_logs"]'),
            ("T1203", "Exploitation for Client Execution", "TA0002", "Exploiting client software.", 0, "", '["windows","linux","macos"]', "Application whitelisting", '["process_logs"]'),
            ("T1204", "User Execution", "TA0002", "Relying on user interaction.", 0, "", '["windows","linux","macos"]', "User awareness training", '["process_logs"]'),
            ("T1047", "Windows Management Instrumentation", "TA0002", "Using WMI for execution.", 0, "", '["windows"]', "WMI activity monitoring", '["wmi_logs"]'),
            ("T1053", "Scheduled Task/Job", "TA0002", "Executing via task scheduler.", 0, "", '["windows","linux","macos"]', "Task scheduler monitoring", '["scheduled_tasks"]'),
            # Persistence
            ("T1547", "Boot or Logon Autostart Execution", "TA0003", "Autostart on boot/logon.", 0, "", '["windows","linux","macos"]', "Registry and startup monitoring", '["registry","file_system"]'),
            ("T1547.001", "Registry Run Keys / Startup Folder", "TA0003", "Using Run keys or Startup folder.", 1, "T1547", '["windows"]', "Registry monitoring", '["registry"]'),
            ("T1136", "Create Account", "TA0003", "Creating new accounts.", 0, "", '["windows","linux","macos","cloud"]', "Account creation monitoring", '["auth_logs"]'),
            ("T1543", "Create or Modify System Process", "TA0003", "Installing malicious services.", 0, "", '["windows","linux","macos"]', "Service creation monitoring", '["process_logs"]'),
            ("T1505", "Server Software Component", "TA0003", "Installing web shells.", 0, "", '["windows","linux"]', "Web shell detection", '["web_logs","file_system"]'),
            ("T1505.003", "Web Shell", "TA0003", "Installing web shell on server.", 1, "T1505", '["windows","linux"]', "File integrity monitoring", '["file_system","web_logs"]'),
            # Privilege Escalation
            ("T1068", "Exploitation for Privilege Escalation", "TA0004", "Exploiting vulnerabilities for privesc.", 0, "", '["windows","linux","macos"]', "Patch management", '["process_logs"]'),
            ("T1548", "Abuse Elevation Control Mechanism", "TA0004", "Bypassing UAC or sudo.", 0, "", '["windows","linux","macos"]', "UAC/sudo monitoring", '["process_logs"]'),
            ("T1134", "Access Token Manipulation", "TA0004", "Manipulating access tokens.", 0, "", '["windows"]', "Token manipulation detection", '["process_logs"]'),
            # Defense Evasion
            ("T1027", "Obfuscated Files or Information", "TA0005", "Making files or info unreadable.", 0, "", '["windows","linux","macos"]', "Content inspection", '["file_system"]'),
            ("T1070", "Indicator Removal", "TA0005", "Deleting or modifying artifacts.", 0, "", '["windows","linux","macos"]', "Log integrity monitoring", '["event_logs"]'),
            ("T1562", "Impair Defenses", "TA0005", "Disabling security tools.", 0, "", '["windows","linux","macos"]', "Security tool health monitoring", '["process_logs"]'),
            ("T1036", "Masquerading", "TA0005", "Naming malware after legitimate files.", 0, "", '["windows","linux","macos"]', "Process name verification", '["process_logs"]'),
            ("T1055", "Process Injection", "TA0005", "Injecting code into processes.", 0, "", '["windows","linux","macos"]', "API call monitoring", '["process_logs"]'),
            ("T1112", "Modify Registry", "TA0005", "Modifying registry entries.", 0, "", '["windows"]', "Registry auditing", '["registry"]'),
            # Credential Access
            ("T1110", "Brute Force", "TA0006", "Trying many passwords.", 0, "", '["windows","linux","macos","cloud"]', "Account lockout monitoring", '["auth_logs"]'),
            ("T1003", "OS Credential Dumping", "TA0006", "Dumping credentials from OS.", 0, "", '["windows","linux"]', "LSASS protection", '["process_logs"]'),
            ("T1003.001", "LSASS Memory", "TA0006", "Dumping LSASS for credentials.", 1, "T1003", '["windows"]', "Credential Guard", '["process_logs"]'),
            ("T1555", "Credentials from Password Stores", "TA0006", "Extracting from password managers.", 0, "", '["windows","linux","macos"]', "Password store monitoring", '["file_system"]'),
            ("T1552", "Unsecured Credentials", "TA0006", "Finding plaintext credentials.", 0, "", '["windows","linux","macos","cloud"]', "File content scanning", '["file_system"]'),
            ("T1558", "Steal or Forge Kerberos Tickets", "TA0006", "Kerberoasting/Golden Ticket.", 0, "", '["windows"]', "Kerberos monitoring", '["auth_logs"]'),
            # Discovery
            ("T1082", "System Information Discovery", "TA0007", "Gathering OS/hardware info.", 0, "", '["windows","linux","macos"]', "Command monitoring", '["process_logs"]'),
            ("T1083", "File and Directory Discovery", "TA0007", "Listing files and directories.", 0, "", '["windows","linux","macos"]', "Command monitoring", '["process_logs"]'),
            ("T1057", "Process Discovery", "TA0007", "Listing running processes.", 0, "", '["windows","linux","macos"]', "Command monitoring", '["process_logs"]'),
            ("T1016", "System Network Configuration Discovery", "TA0007", "Discovering network config.", 0, "", '["windows","linux","macos"]', "Command monitoring", '["process_logs"]'),
            ("T1049", "System Network Connections Discovery", "TA0007", "Listing network connections.", 0, "", '["windows","linux","macos"]', "Command monitoring", '["process_logs"]'),
            ("T1018", "Remote System Discovery", "TA0007", "Finding remote systems on the network.", 0, "", '["windows","linux","macos"]', "Network scan detection", '["network_traffic"]'),
            ("T1087", "Account Discovery", "TA0007", "Listing user accounts.", 0, "", '["windows","linux","macos","cloud"]', "Command monitoring", '["process_logs","auth_logs"]'),
            # Lateral Movement
            ("T1021", "Remote Services", "TA0008", "Using remote services for movement.", 0, "", '["windows","linux","macos"]', "Remote service monitoring", '["auth_logs","network_traffic"]'),
            ("T1021.001", "Remote Desktop Protocol", "TA0008", "Using RDP for lateral movement.", 1, "T1021", '["windows"]', "RDP monitoring", '["auth_logs","network_traffic"]'),
            ("T1021.002", "SMB/Windows Admin Shares", "TA0008", "Using SMB shares.", 1, "T1021", '["windows"]', "SMB monitoring", '["network_traffic"]'),
            ("T1021.004", "SSH", "TA0008", "Using SSH for lateral movement.", 1, "T1021", '["linux","macos"]', "SSH monitoring", '["auth_logs"]'),
            ("T1570", "Lateral Tool Transfer", "TA0008", "Transferring tools between systems.", 0, "", '["windows","linux","macos"]', "File transfer monitoring", '["network_traffic"]'),
            ("T1550", "Use Alternate Authentication Material", "TA0008", "Using pass-the-hash/ticket.", 0, "", '["windows"]', "Authentication monitoring", '["auth_logs"]'),
            # Collection
            ("T1005", "Data from Local System", "TA0009", "Collecting data from local files.", 0, "", '["windows","linux","macos"]', "File access monitoring", '["file_system"]'),
            ("T1039", "Data from Network Shared Drive", "TA0009", "Collecting from network shares.", 0, "", '["windows","linux","macos"]', "Share access monitoring", '["network_traffic"]'),
            ("T1074", "Data Staged", "TA0009", "Staging data before exfiltration.", 0, "", '["windows","linux","macos"]', "File staging detection", '["file_system"]'),
            ("T1113", "Screen Capture", "TA0009", "Capturing screenshots.", 0, "", '["windows","linux","macos"]', "Screenshot tool detection", '["process_logs"]'),
            ("T1056", "Input Capture", "TA0009", "Capturing keystrokes.", 0, "", '["windows","linux","macos"]', "Keylogger detection", '["process_logs"]'),
            # Command and Control
            ("T1071", "Application Layer Protocol", "TA0011", "Using app-layer protocols for C2.", 0, "", '["windows","linux","macos"]', "Protocol analysis", '["network_traffic"]'),
            ("T1071.001", "Web Protocols", "TA0011", "Using HTTP/HTTPS for C2.", 1, "T1071", '["windows","linux","macos"]', "HTTP analysis", '["proxy_logs"]'),
            ("T1071.004", "DNS", "TA0011", "Using DNS for C2.", 1, "T1071", '["windows","linux","macos"]', "DNS monitoring", '["dns_logs"]'),
            ("T1105", "Ingress Tool Transfer", "TA0011", "Downloading additional tools.", 0, "", '["windows","linux","macos"]', "Download monitoring", '["network_traffic"]'),
            ("T1572", "Protocol Tunneling", "TA0011", "Tunneling through protocols.", 0, "", '["windows","linux","macos"]', "Tunnel detection", '["network_traffic"]'),
            ("T1573", "Encrypted Channel", "TA0011", "Using encryption for C2.", 0, "", '["windows","linux","macos"]', "TLS inspection", '["network_traffic"]'),
            ("T1090", "Proxy", "TA0011", "Using proxies for C2.", 0, "", '["windows","linux","macos"]', "Proxy detection", '["network_traffic"]'),
            ("T1568", "Dynamic Resolution", "TA0011", "Using dynamic DNS for C2.", 0, "", '["windows","linux","macos"]', "DNS monitoring", '["dns_logs"]'),
            # Exfiltration
            ("T1041", "Exfiltration Over C2 Channel", "TA0010", "Exfiltrating over the C2 channel.", 0, "", '["windows","linux","macos"]', "Volume monitoring", '["network_traffic"]'),
            ("T1048", "Exfiltration Over Alternative Protocol", "TA0010", "Using non-C2 protocol to exfiltrate.", 0, "", '["windows","linux","macos"]', "Protocol analysis", '["network_traffic"]'),
            ("T1567", "Exfiltration Over Web Service", "TA0010", "Using cloud storage for exfiltration.", 0, "", '["windows","linux","macos"]', "Cloud upload monitoring", '["proxy_logs"]'),
            ("T1029", "Scheduled Transfer", "TA0010", "Exfiltrating on a schedule.", 0, "", '["windows","linux","macos"]', "Periodic transfer detection", '["network_traffic"]'),
            # Impact
            ("T1486", "Data Encrypted for Impact", "TA0040", "Encrypting data for ransom.", 0, "", '["windows","linux","macos"]', "Ransomware detection", '["file_system"]'),
            ("T1489", "Service Stop", "TA0040", "Stopping services.", 0, "", '["windows","linux"]', "Service monitoring", '["process_logs"]'),
            ("T1490", "Inhibit System Recovery", "TA0040", "Deleting backups and shadow copies.", 0, "", '["windows","linux"]', "Backup monitoring", '["process_logs"]'),
            ("T1499", "Endpoint Denial of Service", "TA0040", "Crashing or overloading.", 0, "", '["windows","linux","macos"]', "Performance monitoring", '["process_logs"]'),
            ("T1531", "Account Access Removal", "TA0040", "Locking out users.", 0, "", '["windows","linux","macos","cloud"]', "Account monitoring", '["auth_logs"]'),
        ]
        # fmt: on
        conn = self._get_connection()
        try:
            conn.executemany(
                """INSERT OR IGNORE INTO mitre_techniques
                   (id, name, tactic_id, description, is_subtechnique, parent_id, platforms, detection, data_sources)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                techniques,
            )
            conn.commit()
        finally:
            conn.close()

    def _seed_groups(self) -> None:
        # fmt: off
        groups = [
            ("G0007", "APT28", '["Fancy Bear","Sofacy","Sednit","STRONTIUM","Forest Blizzard"]', "Russian state-sponsored group associated with GRU.", "Russia", '["government","defense","energy","media"]', '["USA","Europe","Ukraine","NATO"]', "2004", "high"),
            ("G0016", "APT29", '["Cozy Bear","The Dukes","NOBELIUM","Midnight Blizzard"]', "Russian state-sponsored group associated with SVR.", "Russia", '["government","technology","healthcare","think_tanks"]', '["USA","Europe","NATO"]', "2008", "high"),
            ("G0032", "Lazarus Group", '["HIDDEN COBRA","Zinc","LABYRINTH CHOLLIMA","Diamond Sleet"]', "North Korean state-sponsored group.", "North Korea", '["finance","cryptocurrency","defense","technology"]', '["global"]', "2009", "high"),
            ("G0034", "Sandworm Team", '["Voodoo Bear","IRIDIUM","Seashell Blizzard","ELECTRUM"]', "Russian military unit GRU targeting critical infrastructure.", "Russia", '["energy","government","critical_infrastructure"]', '["Ukraine","Europe","USA"]', "2009", "high"),
            ("G0010", "Turla", '["Venomous Bear","Snake","KRYPTON","Secret Blizzard"]', "Russian state-sponsored group targeting government and diplomatic.", "Russia", '["government","diplomatic","military","research"]', '["Europe","Middle_East","Central_Asia"]', "2004", "high"),
            ("G0050", "APT32", '["OceanLotus","SeaLotus","Canvas Cyclone"]', "Vietnamese state-sponsored group.", "Vietnam", '["government","media","technology","manufacturing"]', '["Southeast_Asia","China","Germany"]', "2012", "medium"),
            ("G0082", "APT38", '["Bluenoroff","BeagleBoyz","Sapphire Sleet"]', "North Korean group focused on financial theft.", "North Korea", '["finance","cryptocurrency","banking"]', '["global"]', "2014", "high"),
            ("G0059", "Magic Hound", '["APT35","Charming Kitten","Phosphorus","Mint Sandstorm"]', "Iranian state-sponsored group.", "Iran", '["government","defense","technology","academia"]', '["USA","Middle_East","Europe"]', "2014", "medium"),
            ("G0069", "MuddyWater", '["MERCURY","Mango Sandstorm","Static Kitten"]', "Iranian MOIS-sponsored group.", "Iran", '["government","telecommunications","energy","defense"]', '["Middle_East","Central_Asia","Turkey","India"]', "2017", "medium"),
            ("G0125", "HAFNIUM", '["Silk Typhoon"]', "Chinese state-sponsored group targeting Exchange servers.", "China", '["government","defense","technology","healthcare"]', '["USA","Europe","India"]', "2021", "high"),
            ("G0096", "APT41", '["Wicked Panda","Double Dragon","Brass Typhoon"]', "Chinese dual-purpose (espionage + financial) group.", "China", '["technology","healthcare","gaming","telecommunications"]', '["global"]', "2012", "high"),
            ("G0004", "Ke3chang", '["APT15","Vixen Panda","Nylon Typhoon"]', "Chinese espionage group.", "China", '["government","diplomatic","energy"]', '["Europe","South_America","Central_Asia"]', "2010", "medium"),
            ("G0027", "Threat Group-3390", '["APT27","Emissary Panda","Silk Typhoon"]', "Chinese espionage group.", "China", '["government","technology","defense"]', '["Middle_East","Europe","USA"]', "2010", "medium"),
            ("G0114", "Chimera", '[""]', "Chinese group targeting semiconductor and airline industries.", "China", '["technology","aviation","semiconductor"]', '["Taiwan","Asia"]', "2018", "medium"),
            ("G0045", "menuPass", '["APT10","Stone Panda","Red Apollo","Potassium"]', "Chinese group targeting MSPs and cloud providers.", "China", '["technology","MSP","healthcare","defense"]', '["global"]', "2006", "high"),
            # India-relevant groups
            ("G0134", "SideWinder", '["Rattlesnake","T-APT-04","Razor Tiger"]', "Indian subcontinent group targeting military and government.", "India_attrib", '["government","military","defense"]', '["Pakistan","China","Nepal","Sri_Lanka"]', "2012", "medium"),
            ("G0040", "Patchwork", '["Dropping Elephant","Chinastrats","Monsoon"]', "Group targeting South Asian diplomatic entities.", "India_attrib", '["government","diplomatic","think_tanks"]', '["Pakistan","China","Bangladesh","Sri_Lanka"]', "2015", "medium"),
            ("G0142", "DoNot Team", '["APT-C-35","SectorE02","Origami Elephant"]', "South Asian group targeting government and military.", "South_Asia", '["government","military","NGO"]', '["Pakistan","Bangladesh","Sri_Lanka","India"]', "2016", "medium"),
            ("G0038", "Transparent Tribe", '["APT36","ProjectM","Mythic Leopard","Copper Fieldstone"]', "Pakistan-based group targeting Indian military and government.", "Pakistan", '["government","military","defense","education"]', '["India","Afghanistan"]', "2013", "medium"),
            ("G0065", "Leviathan", '["APT40","Kryptonite Panda","Gingham Typhoon"]', "Chinese group targeting maritime and defense.", "China", '["maritime","defense","technology","government"]', '["USA","Southeast_Asia","India"]', "2013", "high"),
            # Additional major groups
            ("G0080", "Cobalt Group", '["Cobalt Spider","Cobalt Gang"]', "Financial crime group targeting banks via ATM jackpotting.", "Unknown", '["finance","banking"]', '["Europe","CIS","Asia"]', "2016", "medium"),
            ("G0046", "FIN7", '["Carbanak","Carbon Spider","Sangria Tempest"]', "Financially motivated group.", "Unknown", '["retail","hospitality","finance"]', '["USA","Europe"]', "2013", "high"),
            ("G0102", "Wizard Spider", '["Grim Spider","DEV-0193","Storm-0193"]', "Cybercrime group operating TrickBot and Ryuk.", "Russia", '["healthcare","government","finance","technology"]', '["global"]', "2016", "high"),
            ("G0119", "Indrik Spider", '["Evil Corp","DEV-0243","Manatee Tempest"]', "Cybercrime group deploying Dridex and WastedLocker.", "Russia", '["finance","government","technology"]', '["USA","Europe"]', "2014", "high"),
            ("G0139", "TeamTNT", '[""]', "Cloud-focused cryptojacking group.", "Unknown", '["cloud","containers","devops"]', '["global"]', "2019", "low"),
            ("G0129", "Mustang Panda", '["Bronze President","RedDelta","Camaro Dragon"]', "Chinese espionage group.", "China", '["government","NGO","religious"]', '["Southeast_Asia","Europe","Mongolia","India"]', "2017", "medium"),
            ("G0060", "BRONZE BUTLER", '["Tick","REDBALDKNIGHT","Stalker Panda"]', "Chinese espionage group targeting Japan.", "China", '["technology","defense","engineering"]', '["Japan","South_Korea"]', "2006", "medium"),
            ("G0100", "Inception", '["Cloud Atlas","Inception Framework"]', "Eastern European espionage group.", "Unknown", '["government","military","diplomatic"]', '["Russia","Central_Asia","Europe"]', "2014", "medium"),
            ("G0025", "Axiom", '["Group 72","Winnti Group"]', "Chinese state-sponsored espionage group.", "China", '["technology","government","aerospace"]', '["global"]', "2008", "high"),
            ("G0078", "Gorgon Group", '[""]', "Pakistan-based group involved in espionage and crime.", "Pakistan", '["government","military"]', '["India","USA","Europe"]', "2017", "low"),
            ("G0093", "GALLIUM", '["Granite Typhoon","Operation Soft Cell"]', "Chinese group targeting telecoms.", "China", '["telecommunications","government"]', '["global"]', "2018", "medium"),
            ("G0068", "PROMETHIUM", '["StrongPity","Callisto"]', "Turkish-linked espionage group.", "Turkey", '["government","technology","dissidents"]', '["Middle_East","Europe"]', "2012", "medium"),
            ("G0087", "APT39", '["Chafer","Remix Kitten","Cotton Sandstorm"]', "Iranian group targeting telecommunications.", "Iran", '["telecommunications","travel","technology"]', '["Middle_East","USA"]', "2014", "medium"),
            ("G0090", "TEMP.Veles", '["XENOTIME","Triton"]', "Russian group targeting industrial safety systems.", "Russia", '["energy","critical_infrastructure","ICS"]', '["Middle_East","USA"]', "2017", "high"),
            ("G0123", "Kimsuky", '["Velvet Chollima","Emerald Sleet","Thallium"]', "North Korean espionage group.", "North Korea", '["government","think_tanks","academia","defense"]', '["South_Korea","Japan","USA"]', "2012", "medium"),
            ("G0130", "Ajax Security Team", '["Flying Kitten","Charming Kitten"]', "Iranian group.", "Iran", '["government","defense","dissidents"]', '["Iran","USA","Israel"]', "2010", "low"),
            ("G0056", "TEMP.Periscope", '["APT40","Leviathan"]', "Chinese maritime espionage.", "China", '["maritime","defense","technology"]', '["USA","Southeast_Asia"]', "2013", "high"),
            ("G0131", "Tonto Team", '["CactusPete","Karma Panda"]', "Chinese group targeting Russia/Asia.", "China", '["government","military","technology"]', '["Russia","Japan","South_Korea","Mongolia"]', "2009", "medium"),
            ("G0121", "Sidewinder_PK", '["APT-C-17","Bitter"]', "South Asian group targeting Pakistan and China.", "South_Asia", '["government","military","energy"]', '["Pakistan","China","Bangladesh"]', "2013", "medium"),
            ("G0115", "GOLD SOUTHFIELD", '["Pinchy Spider"]', "REvil/Sodinokibi ransomware operators.", "Russia", '["all_sectors"]', '["global"]', "2019", "medium"),
        ]
        # fmt: on
        conn = self._get_connection()
        try:
            conn.executemany(
                """INSERT OR IGNORE INTO mitre_groups
                   (id, name, aliases, description, country, target_sectors, target_countries, active_since, sophistication)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                groups,
            )
            conn.commit()
        finally:
            conn.close()

    def _seed_software(self) -> None:
        # fmt: off
        software = [
            ("S0154", "Cobalt Strike", "tool", "Commercial penetration testing tool widely abused by threat actors.", '["windows","linux"]'),
            ("S0029", "PsExec", "tool", "Sysinternals tool for remote execution.", '["windows"]'),
            ("S0357", "Impacket", "tool", "Python toolkit for network protocol exploitation.", '["windows","linux"]'),
            ("S0002", "Mimikatz", "tool", "Credential extraction tool.", '["windows"]'),
            ("S0005", "Metasploit", "tool", "Penetration testing framework.", '["windows","linux","macos"]'),
            ("S0039", "Net", "tool", "Windows net command for network operations.", '["windows"]'),
            ("S0552", "AdFind", "tool", "Active Directory query tool.", '["windows"]'),
            ("S0160", "certutil", "tool", "Windows certificate utility used for download/encode.", '["windows"]'),
            ("S0190", "BITSAdmin", "tool", "BITS transfer tool.", '["windows"]'),
            ("S0363", "Empire", "tool", "PowerShell post-exploitation framework.", '["windows"]'),
            ("S0482", "Sardonic", "malware", "Backdoor used by FIN8.", '["windows"]'),
            ("S0600", "Dridex", "malware", "Banking trojan.", '["windows"]'),
            ("S0366", "WannaCry", "malware", "Ransomware worm exploiting EternalBlue.", '["windows"]'),
            ("S0650", "QakBot", "malware", "Banking trojan turned loader.", '["windows"]'),
            ("S0367", "NotPetya", "malware", "Destructive wiper disguised as ransomware.", '["windows"]'),
            ("S0592", "SolarWinds Compromise", "malware", "Sunburst backdoor via supply chain.", '["windows"]'),
            ("S0260", "InvisiMole", "malware", "Spyware used by Turla-linked actors.", '["windows"]'),
            ("S0458", "Ramsay", "malware", "Espionage framework for air-gapped networks.", '["windows"]'),
            ("S0201", "JPIN", "malware", "Backdoor used by menuPass.", '["windows"]'),
            ("S0266", "TrickBot", "malware", "Banking trojan turned loader platform.", '["windows"]'),
        ]
        # fmt: on
        conn = self._get_connection()
        try:
            conn.executemany(
                "INSERT OR IGNORE INTO mitre_software (id, name, software_type, description, platforms) VALUES (?,?,?,?,?)",
                software,
            )
            conn.commit()
        finally:
            conn.close()

    def _seed_group_techniques(self) -> None:
        """Maps APT groups to their known techniques."""
        # fmt: off
        mappings = [
            # APT28
            ("G0007", "T1566.001", "Spearphishing with weaponized documents."),
            ("G0007", "T1566.002", "Spearphishing with OAuth links."),
            ("G0007", "T1190", "Exploiting public web applications."),
            ("G0007", "T1059.001", "PowerShell for execution."),
            ("G0007", "T1078", "Using valid credentials."),
            ("G0007", "T1003.001", "LSASS credential dumping."),
            ("G0007", "T1027", "Obfuscating payloads."),
            ("G0007", "T1071.001", "HTTPS for C2."),
            ("G0007", "T1547.001", "Registry run keys for persistence."),
            ("G0007", "T1082", "System info discovery."),
            ("G0007", "T1041", "Exfiltration over C2 channel."),
            ("G0007", "T1105", "Downloading additional tools."),
            # APT29
            ("G0016", "T1195", "SolarWinds supply chain compromise."),
            ("G0016", "T1566.001", "Spearphishing with ISO attachments."),
            ("G0016", "T1059.001", "PowerShell execution."),
            ("G0016", "T1078", "Using stolen credentials."),
            ("G0016", "T1550", "Pass-the-hash attacks."),
            ("G0016", "T1021.001", "RDP lateral movement."),
            ("G0016", "T1071.001", "HTTPS C2 communication."),
            ("G0016", "T1573", "Encrypted C2 channel."),
            ("G0016", "T1005", "Data collection from local systems."),
            ("G0016", "T1041", "Exfiltration over C2."),
            ("G0016", "T1027", "Obfuscated files."),
            ("G0016", "T1547.001", "Registry persistence."),
            ("G0016", "T1136", "Creating accounts for persistence."),
            # Lazarus
            ("G0032", "T1566.001", "Spearphishing with malicious attachments."),
            ("G0032", "T1189", "Watering hole attacks."),
            ("G0032", "T1059.001", "PowerShell usage."),
            ("G0032", "T1059.003", "Windows command shell."),
            ("G0032", "T1547.001", "Registry run keys."),
            ("G0032", "T1543", "Creating malicious services."),
            ("G0032", "T1027", "Obfuscated payloads."),
            ("G0032", "T1055", "Process injection."),
            ("G0032", "T1003", "Credential dumping."),
            ("G0032", "T1082", "System discovery."),
            ("G0032", "T1071.001", "HTTP/HTTPS C2."),
            ("G0032", "T1486", "Ransomware deployment."),
            ("G0032", "T1105", "Tool downloads."),
            # Transparent Tribe (APT36)
            ("G0038", "T1566.001", "Spearphishing with malicious documents."),
            ("G0038", "T1566.002", "Spearphishing links."),
            ("G0038", "T1204", "Relies on user execution."),
            ("G0038", "T1059.001", "PowerShell scripts."),
            ("G0038", "T1547.001", "Registry persistence."),
            ("G0038", "T1082", "System information gathering."),
            ("G0038", "T1083", "File and directory listing."),
            ("G0038", "T1056", "Keylogging."),
            ("G0038", "T1113", "Screen capture."),
            ("G0038", "T1005", "Local data collection."),
            ("G0038", "T1071.001", "HTTP C2."),
            ("G0038", "T1041", "Exfiltration over C2."),
            # SideWinder
            ("G0134", "T1566.001", "Spearphishing with RTF/DOCX exploits."),
            ("G0134", "T1190", "Exploiting web servers."),
            ("G0134", "T1059.001", "PowerShell execution."),
            ("G0134", "T1059.003", "Command shell usage."),
            ("G0134", "T1547.001", "Registry persistence."),
            ("G0134", "T1053", "Scheduled tasks."),
            ("G0134", "T1027", "Obfuscated payloads."),
            ("G0134", "T1082", "System discovery."),
            ("G0134", "T1083", "File discovery."),
            ("G0134", "T1071.001", "HTTPS C2."),
            ("G0134", "T1105", "Tool download."),
            # Patchwork
            ("G0040", "T1566.001", "Spearphishing documents."),
            ("G0040", "T1203", "Client-side exploitation."),
            ("G0040", "T1059.001", "PowerShell."),
            ("G0040", "T1547.001", "Registry persistence."),
            ("G0040", "T1027", "Obfuscation."),
            ("G0040", "T1082", "System discovery."),
            ("G0040", "T1083", "File discovery."),
            ("G0040", "T1056", "Keylogging."),
            ("G0040", "T1005", "Local data collection."),
            ("G0040", "T1071.001", "HTTP C2."),
            # MuddyWater
            ("G0069", "T1566.001", "Spearphishing with macro-enabled docs."),
            ("G0069", "T1059.001", "PowerShell scripts."),
            ("G0069", "T1059.003", "Windows command shell."),
            ("G0069", "T1547.001", "Registry run keys."),
            ("G0069", "T1053", "Scheduled tasks."),
            ("G0069", "T1027", "Obfuscated scripts."),
            ("G0069", "T1036", "Masquerading."),
            ("G0069", "T1082", "System discovery."),
            ("G0069", "T1021.001", "RDP usage."),
            ("G0069", "T1071.001", "HTTP C2."),
            ("G0069", "T1105", "Tool download."),
            # DoNot Team
            ("G0142", "T1566.001", "Spearphishing documents."),
            ("G0142", "T1204", "User execution."),
            ("G0142", "T1059.001", "PowerShell."),
            ("G0142", "T1547.001", "Registry persistence."),
            ("G0142", "T1082", "System discovery."),
            ("G0142", "T1056", "Keylogging."),
            ("G0142", "T1113", "Screen capture."),
            ("G0142", "T1005", "Local data collection."),
            ("G0142", "T1071.001", "HTTP C2."),
            # APT41
            ("G0096", "T1190", "Exploiting public-facing apps."),
            ("G0096", "T1195", "Supply chain attacks."),
            ("G0096", "T1133", "External remote services."),
            ("G0096", "T1059.001", "PowerShell."),
            ("G0096", "T1505.003", "Web shells."),
            ("G0096", "T1068", "Privilege escalation exploits."),
            ("G0096", "T1003", "Credential dumping."),
            ("G0096", "T1021.002", "SMB lateral movement."),
            ("G0096", "T1071.001", "HTTPS C2."),
            ("G0096", "T1486", "Ransomware."),
            # Sandworm
            ("G0034", "T1190", "Exploiting public applications."),
            ("G0034", "T1566.001", "Spearphishing."),
            ("G0034", "T1059.001", "PowerShell."),
            ("G0034", "T1059.004", "Unix shell."),
            ("G0034", "T1547.001", "Registry persistence."),
            ("G0034", "T1562", "Disabling security tools."),
            ("G0034", "T1003", "Credential dumping."),
            ("G0034", "T1021.002", "SMB lateral movement."),
            ("G0034", "T1486", "Ransomware/wipers."),
            ("G0034", "T1490", "Destroying recovery options."),
            # Kimsuky
            ("G0123", "T1566.001", "Spearphishing."),
            ("G0123", "T1566.002", "Spearphishing links."),
            ("G0123", "T1059.001", "PowerShell."),
            ("G0123", "T1547.001", "Registry persistence."),
            ("G0123", "T1056", "Keylogging."),
            ("G0123", "T1082", "System discovery."),
            ("G0123", "T1005", "Data from local system."),
            ("G0123", "T1071.001", "HTTP C2."),
            # FIN7
            ("G0046", "T1566.001", "Spearphishing."),
            ("G0046", "T1059.001", "PowerShell."),
            ("G0046", "T1047", "WMI."),
            ("G0046", "T1543", "Malicious services."),
            ("G0046", "T1003", "Credential dumping."),
            ("G0046", "T1021.002", "SMB shares."),
            ("G0046", "T1074", "Data staging."),
            ("G0046", "T1041", "Exfiltration over C2."),
            # Wizard Spider
            ("G0102", "T1566.001", "Spearphishing."),
            ("G0102", "T1059.001", "PowerShell."),
            ("G0102", "T1547.001", "Registry persistence."),
            ("G0102", "T1003.001", "LSASS dumping."),
            ("G0102", "T1021.001", "RDP."),
            ("G0102", "T1021.002", "SMB."),
            ("G0102", "T1486", "Ryuk/Conti ransomware."),
            ("G0102", "T1490", "Deleting shadow copies."),
            # Mustang Panda
            ("G0129", "T1566.001", "Spearphishing with archives."),
            ("G0129", "T1204", "User execution."),
            ("G0129", "T1059.003", "Command shell."),
            ("G0129", "T1547.001", "Registry run keys."),
            ("G0129", "T1036", "Masquerading."),
            ("G0129", "T1082", "System info discovery."),
            ("G0129", "T1071.001", "HTTP C2."),
            ("G0129", "T1105", "Tool download."),
        ]
        # fmt: on
        conn = self._get_connection()
        try:
            conn.executemany(
                "INSERT OR IGNORE INTO mitre_group_techniques (group_id, technique_id, usage_description) VALUES (?,?,?)",
                mappings,
            )
            conn.commit()
        finally:
            conn.close()

    def _seed_mitigations(self) -> None:
        # fmt: off
        mitigations = [
            ("T1566.001", "M1049", "Antivirus/Antimalware", "Deploy email attachment scanning and sandboxing."),
            ("T1566.001", "M1031", "Network Intrusion Prevention", "Use email gateway with attachment detonation."),
            ("T1566.001", "M1017", "User Training", "Train users to identify spearphishing."),
            ("T1566.002", "M1021", "Restrict Web-Based Content", "Use URL filtering and web proxies."),
            ("T1190", "M1048", "Application Isolation and Sandboxing", "Isolate internet-facing applications."),
            ("T1190", "M1051", "Update Software", "Patch known vulnerabilities promptly."),
            ("T1078", "M1032", "Multi-factor Authentication", "Enforce MFA on all accounts."),
            ("T1078", "M1027", "Password Policies", "Enforce strong password policies."),
            ("T1059.001", "M1042", "Disable or Remove Feature", "Constrained Language Mode for PowerShell."),
            ("T1059.001", "M1045", "Code Signing", "Require signed scripts."),
            ("T1003.001", "M1043", "Credential Access Protection", "Enable Credential Guard."),
            ("T1003.001", "M1025", "Privileged Process Integrity", "Protect LSASS process."),
            ("T1547.001", "M1024", "Restrict Registry Permissions", "Lock down registry run keys."),
            ("T1021.001", "M1035", "Limit Access to Resource Over Network", "Restrict RDP access by IP."),
            ("T1021.002", "M1035", "Limit Access to Resource Over Network", "Disable unnecessary SMB shares."),
            ("T1486", "M1053", "Data Backup", "Maintain offline backups."),
            ("T1486", "M1040", "Behavior Prevention on Endpoint", "Deploy EDR with ransomware protection."),
            ("T1505.003", "M1042", "Disable or Remove Feature", "Remove unused web components."),
            ("T1505.003", "M1018", "User Account Management", "Restrict web server permissions."),
            ("T1068", "M1051", "Update Software", "Apply security patches."),
            ("T1071.001", "M1031", "Network Intrusion Prevention", "Deploy network IDS/IPS."),
            ("T1055", "M1040", "Behavior Prevention on Endpoint", "Use EDR to detect injection."),
            ("T1041", "M1031", "Network Intrusion Prevention", "Monitor and limit outbound traffic."),
            ("T1195", "M1016", "Vulnerability Scanning", "Verify software supply chain integrity."),
        ]
        # fmt: on
        conn = self._get_connection()
        try:
            conn.executemany(
                """INSERT OR IGNORE INTO mitre_technique_mitigations
                   (technique_id, mitigation_id, mitigation_name, description) VALUES (?,?,?,?)""",
                mitigations,
            )
            conn.commit()
        finally:
            conn.close()

    # ── Query API ────────────────────────────────────────────────────────

    def get_all_tactics(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM mitre_tactics ORDER BY phase_order").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_all_techniques(self, tactic_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            if tactic_id:
                rows = conn.execute(
                    "SELECT * FROM mitre_techniques WHERE tactic_id = ? ORDER BY id",
                    (tactic_id,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM mitre_techniques ORDER BY id").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_all_groups(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM mitre_groups ORDER BY name").fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["aliases"] = json.loads(d.get("aliases") or "[]")
                d["target_sectors"] = json.loads(d.get("target_sectors") or "[]")
                d["target_countries"] = json.loads(d.get("target_countries") or "[]")
                results.append(d)
            return results
        finally:
            conn.close()

    def lookup_technique(self, technique_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM mitre_techniques WHERE id = ?", (technique_id,)).fetchone()
            if row:
                d = dict(row)
                d["platforms"] = json.loads(d.get("platforms") or "[]")
                d["data_sources"] = json.loads(d.get("data_sources") or "[]")
                return d
        finally:
            conn.close()
        return None

    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM mitre_groups WHERE id = ?", (group_id,)).fetchone()
            if row:
                d = dict(row)
                d["aliases"] = json.loads(d.get("aliases") or "[]")
                d["target_sectors"] = json.loads(d.get("target_sectors") or "[]")
                d["target_countries"] = json.loads(d.get("target_countries") or "[]")
                return d
        finally:
            conn.close()
        return None

    def get_group_ttps(self, group_id: str) -> List[Dict[str, Any]]:
        """Return all techniques used by a specific APT group."""
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """SELECT t.*, gt.usage_description
                   FROM mitre_techniques t
                   JOIN mitre_group_techniques gt ON t.id = gt.technique_id
                   WHERE gt.group_id = ?
                   ORDER BY t.tactic_id, t.id""",
                (group_id,),
            ).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["platforms"] = json.loads(d.get("platforms") or "[]")
                d["data_sources"] = json.loads(d.get("data_sources") or "[]")
                results.append(d)
            return results
        finally:
            conn.close()

    def find_groups_by_techniques(self, technique_ids: List[str]) -> List[Dict[str, Any]]:
        """Find all APT groups that use any of the given techniques,
        ranked by how many of the provided techniques they use (overlap score)."""
        if not technique_ids:
            return []
        conn = self._get_connection()
        try:
            placeholders = ",".join("?" for _ in technique_ids)
            rows = conn.execute(
                f"""SELECT g.*, COUNT(gt.technique_id) as overlap_count,
                           GROUP_CONCAT(gt.technique_id) as matched_techniques
                    FROM mitre_groups g
                    JOIN mitre_group_techniques gt ON g.id = gt.group_id
                    WHERE gt.technique_id IN ({placeholders})
                    GROUP BY g.id
                    ORDER BY overlap_count DESC""",
                technique_ids,
            ).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["aliases"] = json.loads(d.get("aliases") or "[]")
                d["target_sectors"] = json.loads(d.get("target_sectors") or "[]")
                d["target_countries"] = json.loads(d.get("target_countries") or "[]")
                d["matched_techniques"] = d.get("matched_techniques", "").split(",")
                results.append(d)
            return results
        finally:
            conn.close()

    def get_technique_rarity(self, technique_id: str) -> float:
        """Return rarity score (0..1). Rare techniques (used by few groups) score higher."""
        conn = self._get_connection()
        try:
            total_groups = conn.execute("SELECT COUNT(*) AS c FROM mitre_groups").fetchone()["c"]
            using_groups = conn.execute(
                "SELECT COUNT(DISTINCT group_id) AS c FROM mitre_group_techniques WHERE technique_id = ?",
                (technique_id,),
            ).fetchone()["c"]
            if total_groups == 0:
                return 0.5
            return 1.0 - (using_groups / total_groups)
        finally:
            conn.close()

    def get_mitigations(self, technique_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM mitre_technique_mitigations WHERE technique_id = ?",
                (technique_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_tactic_for_technique(self, technique_id: str) -> Optional[Dict[str, Any]]:
        tech = self.lookup_technique(technique_id)
        if tech and tech.get("tactic_id"):
            conn = self._get_connection()
            try:
                row = conn.execute("SELECT * FROM mitre_tactics WHERE id = ?", (tech["tactic_id"],)).fetchone()
                return dict(row) if row else None
            finally:
                conn.close()
        return None

    def get_technique_chain(self, tactic_ids: List[str]) -> List[Dict[str, Any]]:
        """Given a list of tactic IDs, return all techniques for each tactic in phase order."""
        conn = self._get_connection()
        try:
            result = []
            for tid in tactic_ids:
                tactic_row = conn.execute("SELECT * FROM mitre_tactics WHERE id = ?", (tid,)).fetchone()
                if not tactic_row:
                    continue
                tech_rows = conn.execute(
                    "SELECT * FROM mitre_techniques WHERE tactic_id = ? ORDER BY id", (tid,)
                ).fetchall()
                result.append({
                    "tactic": dict(tactic_row),
                    "techniques": [dict(r) for r in tech_rows],
                })
            return sorted(result, key=lambda x: x["tactic"]["phase_order"])
        finally:
            conn.close()

    def get_all_software(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM mitre_software ORDER BY name").fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["platforms"] = json.loads(d.get("platforms") or "[]")
                results.append(d)
            return results
        finally:
            conn.close()

    def search_groups_by_name(self, query: str) -> List[Dict[str, Any]]:
        """Search groups by name or alias substring."""
        conn = self._get_connection()
        try:
            q = f"%{query}%"
            rows = conn.execute(
                "SELECT * FROM mitre_groups WHERE name LIKE ? OR aliases LIKE ? ORDER BY name",
                (q, q),
            ).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["aliases"] = json.loads(d.get("aliases") or "[]")
                d["target_sectors"] = json.loads(d.get("target_sectors") or "[]")
                d["target_countries"] = json.loads(d.get("target_countries") or "[]")
                results.append(d)
            return results
        finally:
            conn.close()
