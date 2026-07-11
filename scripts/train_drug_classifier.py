#!/usr/bin/env python3
"""
Train Drug Classifier from Twitter Drug Detection CSV Dataset.

Reads a CSV of (url, label) rows where label='T' means drug-related and 'F'
means non-drug.  Extracts Twitter handles, generates drug-vocabulary via LLM
analysis, and outputs learned artifacts that the keyword engine loads at
runtime.

Outputs (written to rakshastra_core/intelligence/):
  - flagged_handles.json          updated handle list
  - learned_drug_vocab.json       weighted drug vocabulary with categories
  - learned_drug_patterns.json    regex patterns, hashtag clusters, emoji combos

Usage:
    poetry run python scripts/train_drug_classifier.py [--csv PATH]
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
INTELLIGENCE_DIR = PROJECT_ROOT / "rakshastra_core" / "intelligence"

DEFAULT_CSV = r"C:\Users\intel\Downloads\Published dataset\Publish dataset\Main_data.csv"

HANDLES_OUT = INTELLIGENCE_DIR / "flagged_handles.json"
VOCAB_OUT = INTELLIGENCE_DIR / "learned_drug_vocab.json"
PATTERNS_OUT = INTELLIGENCE_DIR / "learned_drug_patterns.json"

# ---------------------------------------------------------------------------
# Known drug vocabulary seed (used for TF-IDF boosting)
# ---------------------------------------------------------------------------
SEED_DRUG_TERMS = {
    "mdma", "ecstasy", "molly", "mandy", "weed", "ganja", "maal", "bhang",
    "hash", "charas", "cocaine", "coke", "blow", "snow", "meth", "ice",
    "crystal", "speed", "heroin", "chitta", "smack", "brown sugar", "lsd",
    "acid", "shrooms", "mushrooms", "ketamine", "xanax", "percocet", "oxy",
    "oxycodone", "fentanyl", "adderall", "pills", "tabs", "dope", "crack",
    "lean", "codeine", "promethazine", "tramadol", "diazepam", "valium",
    "plug", "stash", "dealer", "trap", "pack", "score", "re-up", "reup",
    "eighth", "quarter", "ounce", "gram", "kilo", "dime bag", "nickel bag",
    "joint", "blunt", "bong", "edible", "cart", "cartridge", "vape", "dab",
    "wax", "shatter", "rosin", "tincture", "thc", "cbd", "sativa", "indica",
    "hybrid", "kush", "og", "haze", "diesel", "purp", "loud", "gas",
    "fire", "pressure", "exotic", "runtz", "gelato", "zkittlez",
    "perc", "percs", "bars", "benzos", "script", "scripts",
    "meow meow", "mephedrone", "bath salts", "spice", "k2",
    "poppers", "ghb", "pcp", "dmt", "ayahuasca", "mescaline", "peyote",
    "opium", "afeem", "morphine", "hydrocodone",
    # Hindi/Hinglish drug slang
    "nasha", "nashe", "sulfa", "gard", "garad", "pudiya", "talli",
    "phoonk", "phoonkna", "chilam", "chillum",
    # Transaction / delivery slang
    "drop", "dead drop", "wickr", "signal me", "dm for menu",
    "upi", "crypto", "btc", "bitcoin", "monero", "cashapp",
    "delivery", "shipping", "overnight", "express",
}

DRUG_EMOJIS = {
    "\U0001f48a",  # pill
    "\U0001f33f",  # herb
    "\U0001f6ac",  # smoking
    "\u2744\ufe0f",  # snowflake
    "\U0001f340",  # four-leaf clover
    "\U0001f36c",  # candy
    "\U0001f984",  # unicorn
    "\u26a1",      # lightning
    "\U0001f4a8",  # dash / smoke
    "\U0001f525",  # fire
    "\U0001f48e",  # gem (crystal)
    "\U0001f332",  # evergreen tree
    "\U0001f343",  # leaf fluttering
    "\U0001f31f",  # glowing star
    "\U0001f30a",  # wave (lean)
    "\U0001f9ea",  # test tube
    "\U0001f52c",  # microscope
    "\U0001f3af",  # bullseye
    "\U0001f4b0",  # money bag
    "\U0001f4b5",  # dollar
}

# System-reserved Twitter handles to exclude
RESERVED_HANDLES = frozenset({
    "twitter", "home", "search", "explore", "messages",
    "notifications", "i", "settings", "login", "signup",
    "help", "about", "tos", "privacy", "status",
})


def extract_handle_from_url(url: str) -> str | None:
    """Pull the Twitter username from a status URL."""
    parts = url.strip().split("/")
    if len(parts) > 3:
        handle = parts[3].strip()
        if handle and handle.lower() not in RESERVED_HANDLES:
            return handle
    return None


def extract_tweet_id(url: str) -> str | None:
    """Pull the tweet/status ID from a URL."""
    parts = url.strip().split("/")
    for i, p in enumerate(parts):
        if p == "status" and i + 1 < len(parts):
            tid = parts[i + 1].strip().split("?")[0]
            if tid.isdigit():
                return tid
    return None


# ---------------------------------------------------------------------------
# LLM-based vocabulary extraction (best-effort)
# ---------------------------------------------------------------------------

def _generate_vocabulary_via_llm(drug_handles: list[str], sample_size: int = 200) -> dict:
    """Ask the LLM to infer drug vocabulary from a sample of flagged handles."""
    try:
        from agent.auxiliary_client import call_llm
    except Exception:
        print("  [INFO] LLM not available, skipping LLM vocabulary extraction.")
        return {}

    sample = drug_handles[:sample_size]
    handles_text = ", ".join(sample)

    prompt = f"""You are a drug intelligence vocabulary analyst. Given a list of Twitter handles that have been labeled as drug-related accounts, analyze the usernames and infer:

1. Drug-related slang terms, code words, and abbreviations commonly used in their communities
2. Common transaction/delivery phrases
3. Platform-specific code words (Twitter drug trade lingo)
4. Hindi/Hinglish drug slang

Handles to analyze:
{handles_text}

Return a JSON object with this exact structure:
{{
  "inferred_slang": {{
    "category_name": ["term1", "term2", ...]
  }},
  "transaction_phrases": ["phrase1", "phrase2", ...],
  "hinglish_patterns": ["pattern1", "pattern2", ...],
  "emoji_sequences": ["emoji_combo1", "emoji_combo2", ...]
}}

Return ONLY the JSON, no explanations or markdown fences."""

    try:
        response = call_llm(
            task="security/narcotics-intelligence",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Analyze these handles and extract drug vocabulary."},
            ],
            temperature=0.3,
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown fences
        if text.startswith("```"):
            lines = text.splitlines()
            end = -1 if lines[-1].strip() == "```" else len(lines)
            text = "\n".join(lines[1:end]).strip()
        return json.loads(text)
    except Exception as e:
        print(f"  [WARN] LLM vocabulary extraction failed: {e}")
        return {}


# ---------------------------------------------------------------------------
# Core training pipeline
# ---------------------------------------------------------------------------

def train(csv_path: str) -> dict:
    """Run the full training pipeline. Returns summary stats."""
    print(f"[1/6] Reading CSV: {csv_path}")
    drug_urls = []
    nondrug_urls = []
    drug_handles = []
    nondrug_handles = []

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            raise ValueError("CSV file is empty or has no header.")
        print(f"       Columns: {header}")

        for row in reader:
            if len(row) < 2:
                continue
            url, label = row[0].strip(), row[1].strip()
            handle = extract_handle_from_url(url)

            if label == "T":
                drug_urls.append(url)
                if handle:
                    drug_handles.append(handle)
            else:
                nondrug_urls.append(url)
                if handle:
                    nondrug_handles.append(handle)

    total = len(drug_urls) + len(nondrug_urls)
    print(f"       Total rows: {total}")
    print(f"       Drug (T): {len(drug_urls)}, Non-drug (F): {len(nondrug_urls)}")
    print(f"       Drug handles: {len(drug_handles)}, Non-drug handles: {len(nondrug_handles)}")

    # ------------------------------------------------------------------
    # Step 2: Handle frequency analysis
    # ------------------------------------------------------------------
    print("[2/6] Analyzing handle frequencies...")
    drug_handle_counts = Counter(drug_handles)
    nondrug_handle_counts = Counter(nondrug_handles)

    # Handles that appear in drug tweets but NOT in non-drug tweets
    exclusive_drug_handles = set()
    for h, count in drug_handle_counts.items():
        if count >= 1 and h not in nondrug_handle_counts:
            exclusive_drug_handles.add(h)

    # Handles that appear in BOTH but predominantly in drug tweets
    mixed_drug_handles = set()
    for h, count in drug_handle_counts.items():
        if h in nondrug_handle_counts:
            drug_ratio = count / (count + nondrug_handle_counts[h])
            if drug_ratio >= 0.75:
                mixed_drug_handles.add(h)

    all_flagged = exclusive_drug_handles | mixed_drug_handles
    print(f"       Exclusive drug handles: {len(exclusive_drug_handles)}")
    print(f"       Mixed (>75%% drug): {len(mixed_drug_handles)}")
    print(f"       Total flagged handles: {len(all_flagged)}")

    # ------------------------------------------------------------------
    # Step 3: Handle-name-based vocabulary extraction
    # ------------------------------------------------------------------
    print("[3/6] Extracting vocabulary from handle names...")
    handle_word_freq = Counter()
    for h in all_flagged:
        # Split camelCase and underscores
        words = re.findall(r"[a-zA-Z]+", h.lower())
        for w in words:
            if len(w) >= 3 and w not in RESERVED_HANDLES:
                handle_word_freq[w] += 1

    # Words from handles that match seed terms get boosted
    handle_drug_words = {}
    for word, freq in handle_word_freq.most_common(500):
        if word in SEED_DRUG_TERMS:
            handle_drug_words[word] = {"frequency": freq, "source": "handle_seed_match", "confidence": 0.9}
        elif freq >= 5:
            handle_drug_words[word] = {"frequency": freq, "source": "handle_frequent", "confidence": 0.5}

    print(f"       Vocabulary from handles: {len(handle_drug_words)} terms")

    # ------------------------------------------------------------------
    # Step 4: URL pattern analysis
    # ------------------------------------------------------------------
    print("[4/6] Analyzing URL patterns...")
    tweet_ids = []
    for url in drug_urls:
        tid = extract_tweet_id(url)
        if tid:
            tweet_ids.append(tid)
    print(f"       Extracted {len(tweet_ids)} tweet IDs for potential future API fetch")

    # ------------------------------------------------------------------
    # Step 5: LLM vocabulary enrichment
    # ------------------------------------------------------------------
    print("[5/6] LLM vocabulary enrichment (best-effort)...")
    llm_vocab = _generate_vocabulary_via_llm(list(all_flagged))

    # Merge LLM-inferred vocabulary
    learned_slang = defaultdict(list)

    # Start with seed terms organized by category
    seed_categories = {
        "mdma": ["ecstasy", "molly", "mandy", "md", "mumbai rolling", "rolls"],
        "weed": ["ganja", "stuff", "greens", "maal", "bhang", "hash", "charas",
                 "kush", "og", "haze", "diesel", "purp", "loud", "gas", "fire",
                 "pressure", "exotic", "runtz", "gelato", "sativa", "indica",
                 "hybrid", "joint", "blunt", "bong", "edible", "dab", "wax",
                 "shatter", "rosin", "thc", "cbd"],
        "cocaine": ["coke", "blow", "snow", "white", "didi", "crack", "rock"],
        "meth": ["ice", "glass", "crystal", "meth", "speed", "crank", "tina"],
        "heroin": ["chitta", "smack", "brown sugar", "dope", "tar", "junk"],
        "lsd": ["acid", "tabs", "blotter", "microdot", "trip"],
        "pills": ["xanax", "bars", "benzos", "percocet", "percs", "oxy",
                  "oxycodone", "hydrocodone", "fentanyl", "adderall",
                  "tramadol", "diazepam", "valium", "lean", "codeine",
                  "promethazine", "script", "scripts"],
        "psychedelics": ["shrooms", "mushrooms", "dmt", "ketamine", "pcp",
                        "ayahuasca", "mescaline", "peyote", "k2", "spice"],
        "other": ["ghb", "poppers", "meow meow", "mephedrone", "bath salts",
                 "opium", "afeem", "morphine", "nasha", "nashe", "sulfa",
                 "gard", "garad", "pudiya"],
        "transaction": ["plug", "stash", "dealer", "trap", "pack", "score",
                       "re-up", "reup", "drop", "dead drop", "wickr",
                       "dm for menu", "delivery", "shipping", "overnight",
                       "upi", "crypto", "btc", "bitcoin", "monero", "cashapp"],
    }

    for cat, terms in seed_categories.items():
        learned_slang[cat].extend(terms)

    # Merge LLM inferred slang
    if llm_vocab.get("inferred_slang"):
        for cat, terms in llm_vocab["inferred_slang"].items():
            if isinstance(terms, list):
                for t in terms:
                    if isinstance(t, str) and t.lower() not in learned_slang.get(cat, []):
                        learned_slang[cat].append(t.lower())

    # Build final vocab with confidence scores
    final_vocab = {}
    for cat, terms in learned_slang.items():
        for term in terms:
            existing_conf = handle_drug_words.get(term, {}).get("confidence", 0)
            conf = max(0.7, existing_conf)  # seed terms get at least 0.7
            final_vocab[term] = {
                "category": cat,
                "confidence": conf,
                "source": "seed+llm" if term in SEED_DRUG_TERMS else "learned",
            }

    # Add high-frequency handle words not in seed — but FILTER stopwords
    # to avoid common names/words polluting the vocabulary
    _HANDLE_STOPWORDS = frozenset({
        # Common English words
        "the", "and", "not", "all", "its", "who", "just", "much", "only",
        "ever", "your", "lol", "ooo", "com", "org", "abc", "sir", "six",
        "bot", "fan", "dev", "art", "ace", "god", "guy", "man", "boy",
        "boi", "girl", "miss", "dad", "daddy", "baby", "love", "life",
        "mind", "joy", "day", "red", "blue", "black", "brown", "purple",
        "live", "real", "big", "lil", "young", "yung", "old", "new",
        "random", "official", "news", "daily", "times", "updates",
        "world", "usa", "london", "india", "health", "law", "music",
        "stock", "money", "truth", "freedom", "justice", "patriot",
        "police", "coach", "writer", "journal", "ebooks", "online",
        "tweet", "tweets", "info", "iam", "thereal",
        # Common first names
        "aaron", "adam", "alex", "ali", "andrew", "andy", "angel",
        "anthony", "ashley", "bee", "ben", "bill", "bob", "brandon",
        "brian", "cam", "carol", "charles", "charlie", "chris", "christi",
        "christo", "cody", "cole", "cynthia", "dan", "dash", "dave",
        "david", "dee", "dominic", "don", "doug", "dude", "eddie",
        "elle", "eric", "eva", "fox", "frank", "george", "ian", "isaac",
        "james", "jamie", "jane", "jason", "jay", "jeff", "jeremy",
        "jess", "jim", "joe", "john", "johnny", "jon", "jonathan",
        "joseph", "josh", "justin", "king", "queen", "star", "wolf",
        "kris", "lee", "lewis", "lisa", "logan", "mac", "marc", "marie",
        "mark", "martin", "matt", "matthew", "max", "michael", "michelle",
        "mike", "nic", "nick", "nicole", "noah", "paul", "pete", "phil",
        "philly", "renee", "richard", "rob", "ron", "ronnie", "rose",
        "ryan", "sam", "scott", "shane", "smith", "steph", "stephen",
        "steve", "steven", "thomas", "tiffany", "tmj", "tom", "tony",
        "tori", "tyler", "uncle", "will", "william", "wright", "zach",
        "zay",
    })
    for word, info in handle_drug_words.items():
        if word not in final_vocab and info["confidence"] >= 0.5:
            if word in _HANDLE_STOPWORDS:
                continue  # skip common words/names
            if len(word) <= 3:
                continue  # skip very short words
            final_vocab[word] = {
                "category": "handle_derived",
                "confidence": info["confidence"],
                "source": info["source"],
            }


    print(f"       Final vocabulary: {len(final_vocab)} terms across {len(learned_slang)} categories")

    # ------------------------------------------------------------------
    # Step 6: Build patterns file
    # ------------------------------------------------------------------
    print("[6/6] Building patterns file...")

    # Hinglish patterns (expanded)
    hinglish_patterns = [
        r"maal ready hai",
        r"chahiye to dm karo",
        r"delivery mil jayegi",
        r"stock available hai",
        r"pure quality ka maal",
        r"naya maal aaya hai",
        r"rate bhej raha",
        r"cash on delivery",
        r"payment first",
        r"sample available",
        r"msg for details",
        r"dm for price",
        r"check bio for menu",
        r"telegram pe contact karo",
        r"wickr pe msg karo",
        r"order place karo",
        r"saman ready hai",
        r"phoonk ke dekho",
        r"first class maal",
    ]
    if llm_vocab.get("hinglish_patterns"):
        for p in llm_vocab["hinglish_patterns"]:
            if isinstance(p, str) and p not in hinglish_patterns:
                hinglish_patterns.append(p)

    # Transaction phrases
    transaction_phrases = [
        r"dm for (menu|price|details|order)",
        r"check (bio|link|pinned)",
        r"hit me up",
        r"hmu",
        r"contact via (wickr|signal|telegram)",
        r"payment (via|through|by) (upi|crypto|btc|cashapp)",
        r"dead drop",
        r"same day delivery",
        r"overnight (shipping|delivery)",
        r"(bulk|wholesale) (order|discount|price)",
        r"discreet (packaging|shipping)",
        r"no (cops|feds|narcs)",
        r"legit (plug|vendor|seller)",
        r"verified (seller|vendor)",
    ]
    if llm_vocab.get("transaction_phrases"):
        for p in llm_vocab["transaction_phrases"]:
            if isinstance(p, str) and p not in transaction_phrases:
                transaction_phrases.append(p)

    # Expanded emoji set
    emoji_list = sorted(DRUG_EMOJIS)

    patterns_data = {
        "hinglish_patterns": hinglish_patterns,
        "transaction_phrases": transaction_phrases,
        "drug_emojis": emoji_list,
        "version": "1.0",
        "trained_from": os.path.basename(csv_path),
        "total_drug_tweets": len(drug_urls),
        "total_nondrug_tweets": len(nondrug_urls),
    }

    # ------------------------------------------------------------------
    # Write output files
    # ------------------------------------------------------------------
    print("\n[SAVE] Writing output files...")

    # 1. Flagged handles
    existing_handles = set()
    if HANDLES_OUT.exists():
        try:
            existing_handles = set(json.loads(HANDLES_OUT.read_text(encoding="utf-8")))
        except Exception:
            pass
    merged_handles = sorted(existing_handles | all_flagged)
    HANDLES_OUT.write_text(json.dumps(merged_handles, indent=2), encoding="utf-8")
    print(f"  flagged_handles.json: {len(merged_handles)} handles (was {len(existing_handles)})")

    # 2. Learned vocabulary
    VOCAB_OUT.write_text(json.dumps(final_vocab, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  learned_drug_vocab.json: {len(final_vocab)} terms")

    # 3. Patterns
    PATTERNS_OUT.write_text(json.dumps(patterns_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  learned_drug_patterns.json: {len(hinglish_patterns)} hinglish + {len(transaction_phrases)} transaction patterns")

    stats = {
        "total_rows_processed": total,
        "drug_tweets": len(drug_urls),
        "nondrug_tweets": len(nondrug_urls),
        "flagged_handles": len(merged_handles),
        "new_handles_added": len(merged_handles) - len(existing_handles),
        "vocabulary_size": len(final_vocab),
        "categories": list(learned_slang.keys()),
        "hinglish_patterns": len(hinglish_patterns),
        "transaction_patterns": len(transaction_phrases),
        "drug_emojis": len(emoji_list),
    }

    print("\n=== Training Complete ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train drug classifier from Twitter CSV dataset")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to the CSV file")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"ERROR: CSV file not found: {args.csv}")
        sys.exit(1)

    train(args.csv)
