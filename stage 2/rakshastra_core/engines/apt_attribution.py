"""APT Campaign Attribution Engine.

Maps observed attack indicators and TTPs to known APT campaigns using
probabilistic scoring against the MITRE ATT&CK Knowledge Graph.

Attribution formula:
    score = (TTP_overlap × 0.40) + (IOC_match × 0.25)
          + (target_sector_match × 0.20) + (geographic_alignment × 0.15)

TTP overlap uses Jaccard similarity weighted by technique rarity — rare
techniques receive higher weight because they are more discriminating.
"""

import json
import math
from typing import Any, Dict, List, Optional, Set, Tuple

from rakshastra_core.engines.mitre_attack_store import MitreAttackStore


# ── Known Campaign Database ─────────────────────────────────────────────

_KNOWN_CAMPAIGNS: List[Dict[str, Any]] = [
    {
        "id": "CAMP-001", "name": "SolarWinds (SUNBURST)",
        "group_id": "G0016", "year": 2020,
        "ttps": ["T1195", "T1059.001", "T1071.001", "T1573", "T1005", "T1041", "T1027"],
        "iocs": ["avsvmcloud.com", "SolarWinds.Orion.Core.BusinessLayer.dll"],
        "target_sectors": ["government", "technology"], "target_countries": ["USA", "Europe"],
    },
    {
        "id": "CAMP-002", "name": "Operation Sharpshooter",
        "group_id": "G0032", "year": 2018,
        "ttps": ["T1566.001", "T1059.003", "T1547.001", "T1027", "T1071.001", "T1082"],
        "iocs": ["Rising Sun malware", "Lazarus implant"],
        "target_sectors": ["defense", "technology", "finance"], "target_countries": ["global"],
    },
    {
        "id": "CAMP-003", "name": "Operation Cloud Hopper",
        "group_id": "G0045", "year": 2017,
        "ttps": ["T1199", "T1078", "T1059.001", "T1021.001", "T1003.001", "T1005", "T1041"],
        "iocs": ["ChChes RAT", "RedLeaves malware"],
        "target_sectors": ["MSP", "technology", "healthcare"], "target_countries": ["global"],
    },
    {
        "id": "CAMP-004", "name": "NotPetya",
        "group_id": "G0034", "year": 2017,
        "ttps": ["T1195", "T1059.001", "T1003", "T1021.002", "T1486", "T1490"],
        "iocs": ["M.E.Doc update", "EternalBlue exploit"],
        "target_sectors": ["critical_infrastructure", "finance"], "target_countries": ["Ukraine", "Europe"],
    },
    {
        "id": "CAMP-005", "name": "Operation Honey Trap",
        "group_id": "G0038", "year": 2021,
        "ttps": ["T1566.001", "T1566.002", "T1204", "T1059.001", "T1547.001", "T1056", "T1113", "T1041"],
        "iocs": ["CrimsonRAT", "ObliqueRAT"],
        "target_sectors": ["military", "defense", "government"], "target_countries": ["India"],
    },
    {
        "id": "CAMP-006", "name": "Operation SideCopy",
        "group_id": "G0038", "year": 2020,
        "ttps": ["T1566.001", "T1204", "T1059.001", "T1547.001", "T1082", "T1005", "T1071.001"],
        "iocs": ["ActionRAT", "MargulasRAT"],
        "target_sectors": ["defense", "government"], "target_countries": ["India"],
    },
    {
        "id": "CAMP-007", "name": "Operation RattleSnake",
        "group_id": "G0134", "year": 2019,
        "ttps": ["T1566.001", "T1190", "T1059.001", "T1547.001", "T1027", "T1071.001", "T1105"],
        "iocs": ["SideWinder.AntiBot", "HTA downloader"],
        "target_sectors": ["government", "military"], "target_countries": ["Pakistan", "China"],
    },
    {
        "id": "CAMP-008", "name": "Operation Patchwork (Hangover)",
        "group_id": "G0040", "year": 2018,
        "ttps": ["T1566.001", "T1203", "T1059.001", "T1547.001", "T1027", "T1056", "T1071.001"],
        "iocs": ["BADNEWS RAT", "Ragnatela"],
        "target_sectors": ["diplomatic", "government", "think_tanks"], "target_countries": ["Pakistan", "China"],
    },
    {
        "id": "CAMP-009", "name": "MuddyWater Campaigns",
        "group_id": "G0069", "year": 2020,
        "ttps": ["T1566.001", "T1059.001", "T1059.003", "T1547.001", "T1027", "T1036", "T1071.001"],
        "iocs": ["POWERSTATS", "MuddyC2Go"],
        "target_sectors": ["government", "telecommunications", "energy"], "target_countries": ["Middle_East", "India"],
    },
    {
        "id": "CAMP-010", "name": "Operation GhostShell",
        "group_id": "G0059", "year": 2021,
        "ttps": ["T1566.001", "T1059.001", "T1078", "T1003", "T1082", "T1071.001", "T1573"],
        "iocs": ["ShellClient RAT"],
        "target_sectors": ["defense", "technology"], "target_countries": ["Middle_East", "USA", "India"],
    },
    {
        "id": "CAMP-011", "name": "APT41 Double Dragon",
        "group_id": "G0096", "year": 2020,
        "ttps": ["T1190", "T1195", "T1133", "T1505.003", "T1068", "T1003", "T1021.002", "T1486"],
        "iocs": ["Winnti malware", "ShadowPad"],
        "target_sectors": ["technology", "healthcare", "gaming"], "target_countries": ["global"],
    },
    {
        "id": "CAMP-012", "name": "WannaCry",
        "group_id": "G0032", "year": 2017,
        "ttps": ["T1190", "T1059.003", "T1486", "T1489", "T1490"],
        "iocs": ["EternalBlue", "DoublePulsar"],
        "target_sectors": ["healthcare", "critical_infrastructure"], "target_countries": ["global"],
    },
    {
        "id": "CAMP-013", "name": "Conti Ransomware",
        "group_id": "G0102", "year": 2021,
        "ttps": ["T1566.001", "T1059.001", "T1547.001", "T1003.001", "T1021.001", "T1021.002", "T1486", "T1490"],
        "iocs": ["BazarLoader", "Conti ransomware"],
        "target_sectors": ["healthcare", "government", "finance"], "target_countries": ["global"],
    },
    {
        "id": "CAMP-014", "name": "Operation Bitter",
        "group_id": "G0121", "year": 2021,
        "ttps": ["T1566.001", "T1203", "T1059.001", "T1547.001", "T1082", "T1083", "T1071.001"],
        "iocs": ["ArtraDownloader", "BitterRAT"],
        "target_sectors": ["government", "military", "energy"], "target_countries": ["Pakistan", "China", "Bangladesh"],
    },
    {
        "id": "CAMP-015", "name": "Kimsuky Campaigns 2022",
        "group_id": "G0123", "year": 2022,
        "ttps": ["T1566.001", "T1566.002", "T1059.001", "T1547.001", "T1056", "T1082", "T1071.001"],
        "iocs": ["BabyShark", "AppleSeed"],
        "target_sectors": ["think_tanks", "academia", "defense"], "target_countries": ["South_Korea", "Japan", "USA"],
    },
    {
        "id": "CAMP-016", "name": "HAFNIUM Exchange Exploitation",
        "group_id": "G0125", "year": 2021,
        "ttps": ["T1190", "T1505.003", "T1059.001", "T1003", "T1005", "T1071.001"],
        "iocs": ["ProxyLogon", "China Chopper"],
        "target_sectors": ["government", "defense", "technology"], "target_countries": ["USA", "Europe", "India"],
    },
    {
        "id": "CAMP-017", "name": "FIN7 Carbanak",
        "group_id": "G0046", "year": 2019,
        "ttps": ["T1566.001", "T1059.001", "T1047", "T1543", "T1003", "T1021.002", "T1074", "T1041"],
        "iocs": ["Carbanak backdoor", "Pillowmint POS"],
        "target_sectors": ["retail", "hospitality", "finance"], "target_countries": ["USA", "Europe"],
    },
    {
        "id": "CAMP-018", "name": "DoNot Team Campaigns",
        "group_id": "G0142", "year": 2022,
        "ttps": ["T1566.001", "T1204", "T1059.001", "T1547.001", "T1082", "T1056", "T1113", "T1071.001"],
        "iocs": ["yty framework", "Jaca backdoor"],
        "target_sectors": ["government", "military", "NGO"], "target_countries": ["Pakistan", "India", "Bangladesh"],
    },
    {
        "id": "CAMP-019", "name": "Mustang Panda PlugX",
        "group_id": "G0129", "year": 2022,
        "ttps": ["T1566.001", "T1204", "T1059.003", "T1547.001", "T1036", "T1082", "T1071.001", "T1105"],
        "iocs": ["PlugX RAT", "Korplug"],
        "target_sectors": ["government", "NGO", "religious"], "target_countries": ["Southeast_Asia", "Europe", "India"],
    },
    {
        "id": "CAMP-020", "name": "Turla Snake Campaign",
        "group_id": "G0010", "year": 2023,
        "ttps": ["T1566.001", "T1190", "T1059.001", "T1027", "T1055", "T1071.004", "T1573", "T1041"],
        "iocs": ["Snake implant", "ComRAT"],
        "target_sectors": ["government", "diplomatic", "military"], "target_countries": ["Europe", "Middle_East"],
    },
]


class APTAttributionEngine:
    """Maps observed TTPs and IOCs to known APT campaigns."""

    # Attribution weights
    W_TTP = 0.40
    W_IOC = 0.25
    W_SECTOR = 0.20
    W_GEO = 0.15

    def __init__(self, mitre_store: MitreAttackStore):
        self.mitre_store = mitre_store

    def attribute_campaign(
        self,
        observed_ttps: List[str],
        observed_iocs: Optional[List[str]] = None,
        target_sector: Optional[str] = None,
        target_country: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run full attribution pipeline. Returns ranked candidate groups and campaigns."""
        observed_iocs = observed_iocs or []
        observed_set: Set[str] = set(observed_ttps)

        # 1. Find groups by TTP overlap (via MITRE store)
        group_matches = self.mitre_store.find_groups_by_techniques(observed_ttps)

        # 2. Score each group
        scored_groups: List[Dict[str, Any]] = []
        for gm in group_matches:
            group_id = gm["id"]
            group_ttps = [t["id"] for t in self.mitre_store.get_group_ttps(group_id)]
            group_ttp_set = set(group_ttps)

            # TTP overlap — weighted Jaccard
            ttp_score = self._weighted_jaccard(observed_set, group_ttp_set)

            # IOC match against known campaigns
            ioc_score = self._ioc_match_score(group_id, observed_iocs)

            # Sector alignment
            group_sectors = gm.get("target_sectors", [])
            sector_score = 1.0 if target_sector and target_sector.lower() in [s.lower() for s in group_sectors] else 0.0

            # Geographic alignment
            group_countries = gm.get("target_countries", [])
            geo_score = 0.0
            if target_country:
                tc = target_country.lower()
                for gc in group_countries:
                    if gc.lower() == tc or gc.lower() == "global":
                        geo_score = 1.0
                        break

            # Composite score
            composite = (
                self.W_TTP * ttp_score
                + self.W_IOC * ioc_score
                + self.W_SECTOR * sector_score
                + self.W_GEO * geo_score
            )

            # Build reasoning
            reasoning = []
            matched = list(observed_set & group_ttp_set)
            if matched:
                reasoning.append(f"TTP overlap ({len(matched)}/{len(observed_set)} observed techniques match): {matched}")
            if ioc_score > 0:
                reasoning.append(f"IOC matches found in known campaigns (score: {ioc_score:.2f})")
            if sector_score > 0:
                reasoning.append(f"Target sector '{target_sector}' aligns with group's known targets: {group_sectors}")
            if geo_score > 0:
                reasoning.append(f"Geographic target '{target_country}' aligns with group's known targets: {group_countries}")

            # Find matching campaigns
            matching_campaigns = self._find_matching_campaigns(group_id, observed_set, observed_iocs)

            scored_groups.append({
                "group_id": group_id,
                "group_name": gm["name"],
                "aliases": gm.get("aliases", []),
                "country": gm.get("country", "Unknown"),
                "confidence": round(composite, 4),
                "ttp_score": round(ttp_score, 4),
                "ioc_score": round(ioc_score, 4),
                "sector_score": round(sector_score, 4),
                "geo_score": round(geo_score, 4),
                "matching_ttps": matched,
                "matching_campaigns": matching_campaigns,
                "attribution_reasoning": reasoning,
                "sophistication": gm.get("sophistication", "medium"),
            })

        # Sort by composite confidence
        scored_groups.sort(key=lambda x: x["confidence"], reverse=True)

        # Classification
        top_confidence = scored_groups[0]["confidence"] if scored_groups else 0
        attribution_status = "UNKNOWN"
        if top_confidence >= 0.65:
            attribution_status = "HIGH_CONFIDENCE"
        elif top_confidence >= 0.40:
            attribution_status = "MODERATE_CONFIDENCE"
        elif top_confidence >= 0.20:
            attribution_status = "LOW_CONFIDENCE"

        return {
            "attribution_status": attribution_status,
            "top_confidence": round(top_confidence, 4),
            "candidate_groups": scored_groups[:10],  # Top 10
            "observed_ttps": observed_ttps,
            "observed_iocs": observed_iocs,
            "target_sector": target_sector,
            "target_country": target_country,
            "total_groups_evaluated": len(scored_groups),
        }

    def _weighted_jaccard(self, observed: Set[str], group: Set[str]) -> float:
        """Jaccard similarity weighted by technique rarity."""
        if not observed and not group:
            return 0.0
        intersection = observed & group
        union = observed | group
        if not union:
            return 0.0

        # Weight each technique by rarity
        weighted_intersection = 0.0
        weighted_union = 0.0
        for tech_id in union:
            rarity = self.mitre_store.get_technique_rarity(tech_id)
            weight = 0.5 + (rarity * 0.5)  # Scale rarity to 0.5–1.0 weight
            weighted_union += weight
            if tech_id in intersection:
                weighted_intersection += weight

        return weighted_intersection / weighted_union if weighted_union > 0 else 0.0

    def _ioc_match_score(self, group_id: str, observed_iocs: List[str]) -> float:
        """Check observed IOCs against known campaign IOCs for this group."""
        if not observed_iocs:
            return 0.0

        obs_lower = {ioc.lower() for ioc in observed_iocs}
        max_match = 0.0

        for campaign in _KNOWN_CAMPAIGNS:
            if campaign["group_id"] != group_id:
                continue
            campaign_iocs = {ioc.lower() for ioc in campaign.get("iocs", [])}
            matches = obs_lower & campaign_iocs
            if campaign_iocs:
                match_ratio = len(matches) / len(campaign_iocs)
                max_match = max(max_match, match_ratio)

        return max_match

    def _find_matching_campaigns(
        self, group_id: str, observed_ttps: Set[str], observed_iocs: List[str]
    ) -> List[Dict[str, Any]]:
        """Find known campaigns for this group that match observed activity."""
        results = []
        obs_iocs_lower = {ioc.lower() for ioc in observed_iocs}

        for campaign in _KNOWN_CAMPAIGNS:
            if campaign["group_id"] != group_id:
                continue
            camp_ttps = set(campaign.get("ttps", []))
            ttp_overlap = observed_ttps & camp_ttps
            camp_iocs = {ioc.lower() for ioc in campaign.get("iocs", [])}
            ioc_overlap = obs_iocs_lower & camp_iocs

            if ttp_overlap or ioc_overlap:
                results.append({
                    "campaign_id": campaign["id"],
                    "campaign_name": campaign["name"],
                    "year": campaign["year"],
                    "ttp_overlap_count": len(ttp_overlap),
                    "ttp_overlap": list(ttp_overlap),
                    "ioc_overlap": list(ioc_overlap),
                    "target_sectors": campaign.get("target_sectors", []),
                })

        return results

    def get_group_profile(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Return a full profile of an APT group including TTPs and campaigns."""
        group = self.mitre_store.get_group(group_id)
        if not group:
            return None

        ttps = self.mitre_store.get_group_ttps(group_id)
        campaigns = [c for c in _KNOWN_CAMPAIGNS if c["group_id"] == group_id]

        return {
            **group,
            "techniques": ttps,
            "known_campaigns": campaigns,
            "technique_count": len(ttps),
            "campaign_count": len(campaigns),
        }

    def get_all_campaigns(self) -> List[Dict[str, Any]]:
        """Return all known campaigns."""
        return _KNOWN_CAMPAIGNS
