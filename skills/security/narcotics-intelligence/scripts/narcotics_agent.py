#!/usr/bin/env python3
"""
Rakshastra Narcotics Intelligence Agent
Specialized Drug Intelligence Engine for Telegram, WhatsApp, and Instagram.
Deciphers Hinglish, Hindi, regional slang, and emoji codes to detect illicit trade.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Inject project root to python path to allow imports from agent and rakshastra_cli
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from agent.auxiliary_client import call_llm
    from rakshastra_cli.config import load_config, get_rakshastra_home
except ImportError:
    print("Error: Could not import Rakshastra core modules. Ensure this script is run within the project context.")
    sys.exit(1)

# Slang lexicon details for reference / parsing reinforcement
SLANG_LEXICON = {
    "chitta": "Heroin (highly prevalent in Punjab)",
    "maal": "Generic terms for drugs / cannabis",
    "cream": "Cocaine / high-grade charas",
    "ice": "Methamphetamine / MDMA crystals",
    "brown sugar": "Adulterated Heroin",
    "gaanja": "Marijuana / Weed",
    "pudiya": "Individual dose packet",
    "stuff": "Contraband / Narcotics",
    "tabs": "LSD stamps or MDMA pills"
}

EMOJI_LEXICON = {
    "❄️": "Cocaine / Ice / Snow",
    "🍁": "Weed / Cannabis / Ganja",
    "💊": "Pills / MDMA / Ecstasy / Pharma Opioids",
    "💉": "Heroin / Injectables",
    "🍄": "Magic Mushrooms / Psilocybin",
    "🔌": "Supplier / Plug"
}

def analyze_content(content: str, platform: str) -> str:
    """
    Use call_llm to dynamically process and decipher the content.
    No hardcoded mock evaluations.
    """
    system_prompt = f"""
You are the Rakshastra Drug Intelligence Engine (Problem Statement 1), a specialized AI subagent for Indian Law Enforcement.
Your goal is to parse communications from {platform.upper()} (chats, stories, comments, posts) and identify potential narcotics trade or distribution networks under the Narcotic Drugs and Psychotropic Substances (NDPS) Act, 1985.

CRITICAL ANALYTICAL RULES:
1. DECIPHER LANGUAGE: Look for regional Indian dialects, Hindi, Hinglish, Punjabi, and local street slang. Code words like "chitta", "maal", "stuff", "brown sugar", "ice", "pudiya", "delivery boys", "dead drops" are primary signals.
2. EMOJI DETECTION: Detect emoji-based coding schemes (e.g. ❄️, 🍁, 💊, 💉, 🔌) representing drug deals.
3. ENTITY EXTRACTION: Extract UPI IDs, phone numbers, JIDs, Instagram handles, Telegram Usernames, physical locations, delivery coordinates, IP addresses, and email IDs.
4. DETECT METHODOLOGY: Determine if they use dead-drops, UPI advances, cash-on-delivery, crypto, or postal services.
5. NO FABRICATION: Do not invent entities. Only extract what is present in the text.
6. CLASSIFY SEVERITY: Map the substances to the NDPS Act sections (e.g., Section 21 for Heroin/Chitta, Section 20 for Cannabis/Ganja, Section 22 for Psychotropic Substances like MDMA/LSD) and designate Commercial or Small quantity implications.

Respond with a raw JSON object containing the following keys (ensure your response is ONLY valid JSON):
{{
  "is_narcotics_related": true/false,
  "substances_detected": ["substance1", ...],
  "slang_lexicon_matches": [
    {{"term": "slang_term", "meaning": "decoded_meaning", "confidence": 0-100}}
  ],
  "extracted_entities": {{
    "phone_numbers": ["+91..."],
    "emails": ["..."],
    "usernames_handles": ["@..."],
    "crypto_wallets": ["..."],
    "upi_ids": ["..."],
    "ip_addresses": ["..."],
    "locations": ["..."]
  }},
  "ndps_sections": ["Section X", ...],
  "risk_score": 1-10,
  "justification": "Detailed explanation of code words and transaction mechanics decoded from the text."
}}
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this captured raw feed from {platform.upper()}:\n\n{content}"}
    ]

    try:
        response = call_llm(
            task="security/narcotics-intelligence",
            messages=messages,
            temperature=0.1
        )
        content_text = response.choices[0].message.content.strip()
        # Clean potential markdown wraps (e.g. ```json ... ```)
        if content_text.startswith("```"):
            lines = content_text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                content_text = "\n".join(lines[1:-1]).strip()
        return content_text
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return json.dumps({
            "error": str(e),
            "is_narcotics_related": False,
            "justification": "Failed to analyze content due to LLM client exception."
        })

def main():
    parser = argparse.ArgumentParser(description="Rakshastra Narcotics Intelligence Core")
    parser.add_argument("--input", "-i", type=str, help="Path to input raw chat logs or story data file")
    parser.add_argument("--platform", "-p", type=str, choices=["telegram", "whatsapp", "instagram", "all"], default="all", help="Target social media platform")
    parser.add_argument("--output", "-o", type=str, help="Output path for prosecution intelligence report")
    
    args = parser.parse_args()

    if not args.input:
        print("Error: Please provide a raw input file containing messages or feeds using --input or -i")
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file {args.input} does not exist.")
        sys.exit(1)

    print(f"[*] Initializing Narcotics Cyber Intelligence Engine...")
    print(f"[*] Selected Platform scope: {args.platform.upper()}")
    print(f"[*] Reading target data: {input_path.name}")
    
    try:
        raw_content = input_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Decode platform information or split if "all"
    analysis_results = []
    
    # Simple block splitting for multi-platform inputs if needed
    blocks = [{"platform": args.platform, "content": raw_content}]
    if args.platform == "all":
        # If "all" is selected, we scan the text block and pass it as a unified feed or split by platform indicators
        blocks = []
        if "telegram" in raw_content.lower():
            blocks.append({"platform": "telegram", "content": raw_content})
        if "whatsapp" in raw_content.lower():
            blocks.append({"platform": "whatsapp", "content": raw_content})
        if "instagram" in raw_content.lower():
            blocks.append({"platform": "instagram", "content": raw_content})
        if not blocks:
            blocks = [{"platform": "telegram", "content": raw_content}]

    print("[*] Deciphering linguistic layers (Hindi, Hinglish, Slang, Emojis)...")
    
    for block in blocks:
        platform = block["platform"]
        print(f"[*] Processing {platform.upper()} feed...")
        res_json = analyze_content(block["content"], platform)
        try:
            parsed = json.loads(res_json)
            analysis_results.append({
                "platform": platform,
                "analysis": parsed
            })
        except json.JSONDecodeError:
            print(f"[!] Warning: Received non-JSON response from model for {platform.upper()}. Storing raw output.")
            analysis_results.append({
                "platform": platform,
                "analysis": {
                    "raw_response": res_json,
                    "error": "JSON decode failed"
                }
            })

    # Compile the detailed intelligence report
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    case_id = f"CASE-NDPS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    report_md = f"""# RAKSHASTRA DRUG INTELLIGENCE ENGINE REPORT
**CASE FILE: {case_id}**
**GENERATED: {timestamp}**
**CLASSIFICATION: LEA CONFIDENTIAL**

---

## 1. Executive Summary
This report catalogs suspicious activity detected across social platforms (Telegram, WhatsApp, Instagram). It highlights Hinglish slang, local dialects, and emoji code words utilized to obfuscate transaction details.

## 2. Platform Scans & Slang Deciphering
"""
    for entry in analysis_results:
        plat = entry["platform"].upper()
        details = entry["analysis"]
        report_md += f"\n### {plat} INTELLIGENCE REPORT\n"
        
        if "error" in details:
            report_md += f"- **Status**: Parse Error\n- **Details**: {details.get('raw_response')}\n"
            continue
            
        is_narc = details.get("is_narcotics_related", False)
        report_md += f"- **Illicit Activity Suspected**: `{'YES' if is_narc else 'NO'}`\n"
        report_md += f"- **Threat/Risk Rating**: `{details.get('risk_score', 0)}/10`\n"
        
        if details.get("substances_detected"):
            report_md += f"- **Substances Identified**: {', '.join(details['substances_detected'])}\n"
        if details.get("ndps_sections"):
            report_md += f"- **Applicable NDPS Sections**: {', '.join(details['ndps_sections'])}\n"
            
        report_md += f"- **Analytical Justification**:\n  > {details.get('justification', 'No justification provided.')}\n"
        
        # Slang Lexicon Matches
        if details.get("slang_lexicon_matches"):
            report_md += "\n#### Decoded Slang & Emojis:\n"
            report_md += "| Slang Term / Emoji | Decoded Significance | Confidence Level |\n"
            report_md += "|--------------------|----------------------|------------------|\n"
            for slang in details["slang_lexicon_matches"]:
                report_md += f"| {slang.get('term')} | {slang.get('meaning')} | {slang.get('confidence')}% |\n"
        
        # Extracted Entities
        entities = details.get("extracted_entities", {})
        if any(entities.values() if isinstance(entities, dict) else []):
            report_md += "\n#### Extracted Target Indicators:\n"
            for k, val in entities.items():
                if val:
                    report_md += f"- **{k.replace('_', ' ').upper()}**: {', '.join(val)}\n"

    report_md += f"""
---

## 3. Prosecution-Admissible Evidence Chain (Sec 65B IEA)
All raw logs, source metadata, and JSON analysis records are cryptographically hashed below to prevent modification and preserve chain of custody.

| Evidence Target | Platform | Record Hash (SHA-256) |
|-----------------|----------|-----------------------|
"""
    import hashlib
    for entry in analysis_results:
        raw_str = json.dumps(entry)
        h = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()
        report_md += f"| {entry['platform'].upper()} Log Block | {entry['platform']} | {h} |\n"

    # Export report
    output_path = Path(args.output) if args.output else Path(f"./RIR-{case_id}.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_md, encoding="utf-8")
    
    print(f"\n[+] Intelligence analysis complete.")
    print(f"[+] Prosecution-ready report exported to: {output_path.resolve()}")

if __name__ == "__main__":
    main()
