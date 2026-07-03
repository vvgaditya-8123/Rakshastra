from typing import Dict, Any, List, Set
import hashlib

class EntityResolutionEngine:
    """Links disparate target footprints (usernames, phone numbers, UPI IDs, cryptocurrency wallets) into Operator Profiles."""

    def __init__(self):
        # In-memory mapping to simulate the links repository
        self.identity_links: Dict[str, Set[str]] = {}

    def link_entities(self, entity_a: str, entity_b: str):
        """Link two entity tokens together as belonging to the same network profile."""
        if entity_a not in self.identity_links:
            self.identity_links[entity_a] = set()
        if entity_b not in self.identity_links:
            self.identity_links[entity_b] = set()
            
        self.identity_links[entity_a].add(entity_b)
        self.identity_links[entity_b].add(entity_a)

    def resolve_operator(self, seed_entity: str) -> Dict[str, Any]:
        """Resolves all linked identities and profiles reachable from a seed token."""
        visited: Set[str] = set()
        queue: List[str] = [seed_entity]

        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                neighbors = self.identity_links.get(curr, set())
                for n in neighbors:
                    if n not in visited:
                        queue.append(n)

        # Categorize the resolved profile values
        usernames = []
        phones = []
        crypto_wallets = []
        upi_ids = []
        
        for item in visited:
            if item.startswith("@") or len(item) < 8:
                usernames.append(item)
            elif item.startswith("+") or (item.isdigit() and len(item) >= 10):
                phones.append(item)
            elif item.startswith("0x") or item.startswith("bc1") or len(item) >= 30:
                crypto_wallets.append(item)
            elif "@" in item and not item.startswith("@"):
                upi_ids.append(item)

        # Generate a unique hash signature for the resolved profile
        profile_sig = hashlib.sha256("".join(sorted(visited)).encode()).hexdigest()[:12]

        return {
            "operator_id": f"OP-{profile_sig.upper()}",
            "linked_nodes_count": len(visited),
            "usernames": usernames,
            "phone_numbers": phones,
            "crypto_wallets": crypto_wallets,
            "upi_ids": upi_ids,
            "resolved_identifiers": list(visited)
        }
