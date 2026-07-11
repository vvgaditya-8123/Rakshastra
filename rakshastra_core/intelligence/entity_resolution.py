import re
import hashlib
from typing import Dict, Any, List, Set, Tuple

class EntityResolutionEngine:
    """Links disparate target footprints (phones, emails, wallets, handles, IPs) into operator profiles."""

    def __init__(self):
        # Union-Find parent pointer representation for entity linkage
        self.parent: Dict[str, str] = {}
        # Stores metadata for each entity: {entity_token: {"type": "...", "confidence": 0.8}}
        self.entity_metadata: Dict[str, Dict[str, Any]] = {}

    def _find(self, item: str) -> str:
        """Find root representative of an item with path compression."""
        if item not in self.parent:
            self.parent[item] = item
            return item
        
        path = []
        curr = item
        while self.parent[curr] != curr:
            path.append(curr)
            curr = self.parent[curr]
            
        for node in path:
            self.parent[node] = curr
            
        return curr

    def _union(self, item_a: str, item_b: str):
        """Union two sets represented by item_a and item_b."""
        root_a = self._find(item_a)
        root_b = self._find(item_b)
        if root_a != root_b:
            self.parent[root_b] = root_a

    def link_entities(self, entity_a: str, entity_b: str):
        """Link two entity tokens together as belonging to the same network profile."""
        self._union(entity_a, entity_b)
        for entity in (entity_a, entity_b):
            if entity not in self.entity_metadata:
                etype = "unknown"
                if entity.startswith("+") or (entity.isdigit() and len(entity) >= 10):
                    etype = "phone"
                elif entity.startswith("@"):
                    etype = "telegram"
                elif entity.startswith("0x") and len(entity) == 42:
                    etype = "wallet"
                elif "@" in entity and not entity.startswith("@"):
                    etype = "upi_id"
                self.entity_metadata[entity] = {"type": etype, "confidence": 1.0}

    def extract_entities_from_text(self, text: str, source_type: str = "text") -> List[Tuple[str, str, float]]:
        """Extract typed entities from a text payload.
        
        Returns a list of tuples: (entity_token, entity_type, confidence)
        """
        if not text:
            return []

        # Confidence modifiers based on source reliability
        source_conf = {
            "text": 0.90,
            "chat": 0.95,
            "ocr": 0.80,
            "url": 0.70
        }.get(source_type, 0.80)

        extracted = []

        # Regex definitions
        patterns = {
            "phone": r'\+?\d{10,15}',
            "email": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,7}\b',
            "wallet": r'\b(?:0x[a-fA-F0-9]{40}|bc1[a-zA-Z0-9]{39,59})\b',
            "telegram": r'\bt\.me\/([a-zA-Z0-9_]{5,32})\b',
            "instagram": r'\binstagram\.com\/([a-zA-Z0-9_.]+)\b',
            "discord": r'\bdiscordapp\.com\/users\/(\d+)\b',
            "url": r'https?://[^\s/$.?#].[^\s]*',
            "hashtag": r'#\w+',
            "mention": r'@\w+',
            "ip": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        }

        # Sub-extraction matching
        for etype, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                token = match.group(0).strip()
                # Clean specific tokens
                if etype in ["telegram", "instagram", "discord"] and "/" in token:
                    # Extract just the handle/id from URL
                    token = match.group(1).strip()
                
                # Exclude general mentions if they match telegram/instagram patterns
                if etype == "mention" and token.startswith("@"):
                    # We can categorize mentions of length 5-32 as telegram defaults
                    if len(token) >= 6:
                        etype = "telegram"

                # Extract domains from URLs
                if etype == "url":
                    domain_match = re.search(r'https?://([^/:\s]+)', token)
                    if domain_match:
                        domain = domain_match.group(1)
                        if domain and not re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', domain):
                            extracted.append((domain, "domain", source_conf * 0.95))

                extracted.append((token, etype, source_conf))

        # Register metadata
        for token, etype, conf in extracted:
            if token not in self.entity_metadata:
                self.entity_metadata[token] = {"type": etype, "confidence": conf}
            else:
                # Upgrade confidence on multiple discoveries
                self.entity_metadata[token]["confidence"] = min(self.entity_metadata[token]["confidence"] + 0.05, 1.0)

        return extracted

    def process_input(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process various inputs (Text, Chat, Screenshot OCR, URL) to extract and resolve entities."""
        # 1. Extraction from inputs
        all_extracted: List[Tuple[str, str, float]] = []
        
        # Text
        if "text" in payload and payload["text"]:
            all_extracted.extend(self.extract_entities_from_text(payload["text"], "text"))
            
        # Chat (list of messages)
        if "chat" in payload and isinstance(payload["chat"], list):
            for msg in payload["chat"]:
                all_extracted.extend(self.extract_entities_from_text(msg, "chat"))
                
        # Screenshot OCR
        if "ocr" in payload and payload["ocr"]:
            all_extracted.extend(self.extract_entities_from_text(payload["ocr"], "ocr"))
            
        # URL Content
        if "url" in payload and payload["url"]:
            # Normally fetches content, we parse the URL itself and any mock content provided
            all_extracted.extend(self.extract_entities_from_text(payload["url"], "url"))
            if "url_content" in payload and payload["url_content"]:
                all_extracted.extend(self.extract_entities_from_text(payload["url_content"], "url"))

        # Deduplicate list of tokens found in this processing run
        tokens_found = list(set([item[0] for item in all_extracted]))

        # Group/link all entities extracted from the same context together
        if len(tokens_found) > 1:
            first = tokens_found[0]
            for other in tokens_found[1:]:
                self.link_entities(first, other)

        return self.resolve_graph()

    def resolve_graph(self) -> Dict[str, Any]:
        """Resolves all links into unified operator profiles and returns graph-ready JSON."""
        # 1. Group entities by their root representative
        groups: Dict[str, List[str]] = {}
        for token in self.entity_metadata.keys():
            root = self._find(token)
            if root not in groups:
                groups[root] = []
            groups[root].append(token)

        # 2. Build resolved profile structures
        nodes = []
        edges = []
        resolved_profiles = {}

        for root, members in groups.items():
            # Build profile identifier
            profile_sig = hashlib.sha256("".join(sorted(members)).encode()).hexdigest()[:12]
            op_id = f"OP-{profile_sig.upper()}"
            
            # Segment members by type
            segmented: Dict[str, List[str]] = {}
            total_conf = 0.0
            
            for m in members:
                meta = self.entity_metadata.get(m, {"type": "unknown", "confidence": 0.8})
                etype = meta["type"]
                total_conf += meta["confidence"]
                
                if etype not in segmented:
                    segmented[etype] = []
                segmented[etype].append(m)

            avg_confidence = round(total_conf / len(members), 3)

            # Node representing the Operator group itself
            nodes.append({
                "id": op_id,
                "type": "operator",
                "label": f"Operator Profile {op_id}",
                "confidence": avg_confidence,
                "size": len(members)
            })

            # Add node for each member and link it to the Operator node
            for m in members:
                meta = self.entity_metadata.get(m, {"type": "unknown", "confidence": 0.8})
                nodes.append({
                    "id": m,
                    "type": meta["type"],
                    "label": m,
                    "confidence": round(meta["confidence"], 3)
                })
                # Edge linking member to Operator
                edges.append({
                    "source": m,
                    "target": op_id,
                    "type": "belongs_to"
                })

            resolved_profiles[op_id] = {
                "operator_id": op_id,
                "confidence": avg_confidence,
                "entities": segmented,
                "raw_members": members
            }

        return {
            "resolved_profiles": resolved_profiles,
            "graph": {
                "nodes": nodes,
                "edges": edges
            }
        }

    def resolve_operator(self, seed_entity: str) -> Dict[str, Any]:
        """Deltas backwards compatibility: Resolve a single operator profile from seed."""
        root = self._find(seed_entity)
        graph_data = self.resolve_graph()
        
        # Find which operator contains the root/seed
        for op_id, profile in graph_data["resolved_profiles"].items():
            if seed_entity in profile["raw_members"]:
                # Back-compat fields
                return {
                    "operator_id": op_id,
                    "linked_nodes_count": len(profile["raw_members"]),
                    "usernames": profile["entities"].get("telegram", []) + profile["entities"].get("instagram", []),
                    "phone_numbers": profile["entities"].get("phone", []),
                    "crypto_wallets": profile["entities"].get("wallet", []),
                    "upi_ids": profile["entities"].get("upi_id", []),
                    "resolved_identifiers": profile["raw_members"]
                }
                
        # Default fallback
        return {
            "operator_id": "OP-UNKNOWN",
            "linked_nodes_count": 1,
            "usernames": [seed_entity] if "@" in seed_entity else [],
            "phone_numbers": [seed_entity] if seed_entity.startswith("+") else [],
            "crypto_wallets": [],
            "upi_ids": [],
            "resolved_identifiers": [seed_entity]
        }
