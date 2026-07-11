import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from rakshastra_core.models import Asset, AssetType, AssetRelation

class InfrastructureGraph:
    """Graph of infrastructure components and their relationships.

    Models employees, devices, VPNs, servers, cloud resources, certificates,
    secrets, and any other entity — not just traditional "assets".

    Backed by SQLite with FTS5 for natural language search.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    name TEXT,
                    asset_type TEXT,
                    hostname TEXT,
                    ip_address TEXT,
                    properties TEXT,
                    tags TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    source_id TEXT,
                    target_id TEXT,
                    relation_type TEXT,
                    properties TEXT
                )
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS assets_fts USING fts5(
                    id UNINDEXED,
                    name,
                    hostname,
                    ip_address,
                    properties,
                    tags,
                    tokenize="unicode61"
                )
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS assets_ai AFTER INSERT ON assets BEGIN
                    INSERT INTO assets_fts(id, name, hostname, ip_address, properties, tags)
                    VALUES (new.id, new.name, new.hostname, new.ip_address, new.properties, new.tags);
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS assets_ad AFTER DELETE ON assets BEGIN
                    DELETE FROM assets_fts WHERE id = old.id;
                END;
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS assets_au AFTER UPDATE ON assets BEGIN
                    DELETE FROM assets_fts WHERE id = old.id;
                    INSERT INTO assets_fts(id, name, hostname, ip_address, properties, tags)
                    VALUES (new.id, new.name, new.hostname, new.ip_address, new.properties, new.tags);
                END;
            """)
            conn.commit()
        finally:
            conn.close()

    def add_asset(self, asset: Asset) -> str:
        """Add or update an asset. Returns asset ID."""
        tags_str = json.dumps(asset.tags)
        props_str = json.dumps(asset.properties)
        conn = self._get_connection()
        try:
            exists = conn.execute("SELECT 1 FROM assets WHERE id = ?", (asset.id,)).fetchone()
            if exists:
                conn.execute(
                    """
                    UPDATE assets 
                    SET name = ?, asset_type = ?, hostname = ?, ip_address = ?, properties = ?, tags = ?
                    WHERE id = ?
                    """,
                    (
                        asset.name,
                        asset.asset_type.value if isinstance(asset.asset_type, AssetType) else str(asset.asset_type),
                        asset.hostname,
                        asset.ip_address,
                        props_str,
                        tags_str,
                        asset.id
                    )
                )
            else:
                conn.execute(
                    """
                    INSERT INTO assets (id, created_at, name, asset_type, hostname, ip_address, properties, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset.id,
                        asset.created_at,
                        asset.name,
                        asset.asset_type.value if isinstance(asset.asset_type, AssetType) else str(asset.asset_type),
                        asset.hostname,
                        asset.ip_address,
                        props_str,
                        tags_str
                    )
                )
            conn.commit()
        finally:
            conn.close()
        return asset.id

    def add_relation(self, relation: AssetRelation) -> str:
        """Add a relationship between two assets."""
        props_str = json.dumps(relation.properties)
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO relations (id, created_at, source_id, target_id, relation_type, properties)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    relation.id,
                    relation.created_at,
                    relation.source_id,
                    relation.target_id,
                    relation.relation_type,
                    props_str
                )
            )
            conn.commit()
        finally:
            conn.close()
        return relation.id

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
            if row:
                return self._row_to_asset(row)
        finally:
            conn.close()
        return None

    def find_assets(self, query: str = None, asset_type: AssetType = None,
                    tags: List[str] = None) -> List[Asset]:
        """Search assets by text query (FTS5) or filters."""
        conn = self._get_connection()
        try:
            if query:
                clean_query = query.replace('"', '""')
                escaped_query = f'"{clean_query}"'
                rows = conn.execute(
                    """
                    SELECT a.* FROM assets a
                    JOIN assets_fts f ON a.id = f.id
                    WHERE assets_fts MATCH ?
                    """,
                    (escaped_query,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM assets").fetchall()

            results = [self._row_to_asset(row) for row in rows]
        finally:
            conn.close()

        if asset_type:
            target_type = asset_type.value if isinstance(asset_type, AssetType) else str(asset_type)
            results = [a for a in results if (a.asset_type.value if isinstance(a.asset_type, AssetType) else str(a.asset_type)) == target_type]

        if tags:
            results = [a for a in results if any(tag in a.tags for tag in tags)]

        return results

    def neighbors(self, asset_id: str, depth: int = 1,
                  relation_types: List[str] = None) -> Dict[str, Any]:
        """Return neighboring assets and relations up to `depth` hops."""
        visited_assets: Set[str] = {asset_id}
        current_layer: Set[str] = {asset_id}
        
        all_relations: List[Dict[str, Any]] = []
        all_assets: Dict[str, Asset] = {}

        asset = self.get_asset(asset_id)
        if asset:
            all_assets[asset_id] = asset

        conn = self._get_connection()
        try:
            for _ in range(depth):
                if not current_layer:
                    break
                
                placeholders = ",".join("?" for _ in current_layer)
                query_args = list(current_layer)
                
                rel_query = f"SELECT * FROM relations WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})"
                rows = conn.execute(rel_query, query_args + query_args).fetchall()
                
                next_layer: Set[str] = set()
                for row in rows:
                    source = row["source_id"]
                    target = row["target_id"]
                    rel_type = row["relation_type"]

                    if relation_types and rel_type not in relation_types:
                        continue

                    rel_dict = {
                        "id": row["id"],
                        "source_id": source,
                        "target_id": target,
                        "relation_type": rel_type,
                        "properties": json.loads(row["properties"] or "{}")
                    }
                    if rel_dict not in all_relations:
                        all_relations.append(rel_dict)

                    for neighbor_id in (source, target):
                        if neighbor_id not in visited_assets:
                            visited_assets.add(neighbor_id)
                            next_layer.add(neighbor_id)
                            neighbor_asset = self.get_asset(neighbor_id)
                            if neighbor_asset:
                                all_assets[neighbor_id] = neighbor_asset

                current_layer = next_layer
        finally:
            conn.close()

        return {
            "assets": {k: v.to_dict() for k, v in all_assets.items()},
            "relations": all_relations
        }

    def attack_surface(self, asset_id: str) -> List[Asset]:
        """Return all assets reachable (downstream) from the given asset."""
        visited: Set[str] = {asset_id}
        queue: List[str] = [asset_id]
        results: List[Asset] = []

        conn = self._get_connection()
        try:
            while queue:
                curr = queue.pop(0)
                rows = conn.execute("SELECT target_id FROM relations WHERE source_id = ?", (curr,)).fetchall()
                for row in rows:
                    target = row["target_id"]
                    if target not in visited:
                        visited.add(target)
                        queue.append(target)
                        target_asset = self.get_asset(target)
                        if target_asset:
                            results.append(target_asset)
        finally:
            conn.close()

        return results

    def link_investigation_chain(self, host: Asset, container: Optional[Asset] = None,
                                 service: Optional[Asset] = None, vulnerability: Optional[Asset] = None,
                                 incident: Optional[Asset] = None, evidence: Optional[Asset] = None,
                                 report: Optional[Asset] = None) -> None:
        """Create assets and links along the deterministic investigation chain:
        Host -> Container -> Service -> Vulnerability -> Incident -> Evidence -> Report
        """
        # 1. Add all assets
        self.add_asset(host)
        last_asset = host

        if container:
            self.add_asset(container)
            self.add_relation(AssetRelation(
                source_id=last_asset.id,
                target_id=container.id,
                relation_type="runs_container"
            ))
            last_asset = container

        if service:
            self.add_asset(service)
            self.add_relation(AssetRelation(
                source_id=last_asset.id,
                target_id=service.id,
                relation_type="runs_service"
            ))
            last_asset = service

        if vulnerability:
            self.add_asset(vulnerability)
            self.add_relation(AssetRelation(
                source_id=last_asset.id,
                target_id=vulnerability.id,
                relation_type="has_vulnerability"
            ))
            last_asset = vulnerability

        if incident:
            self.add_asset(incident)
            self.add_relation(AssetRelation(
                source_id=last_asset.id,
                target_id=incident.id,
                relation_type="triggers_incident"
            ))
            last_asset = incident

        if evidence:
            self.add_asset(evidence)
            self.add_relation(AssetRelation(
                source_id=last_asset.id,
                target_id=evidence.id,
                relation_type="proves_incident" if incident else "proves_vulnerability"
            ))
            last_asset = evidence

        if report:
            self.add_asset(report)
            self.add_relation(AssetRelation(
                source_id=last_asset.id,
                target_id=report.id,
                relation_type="documented_in"
            ))

    def to_mermaid(self, asset_ids: List[str] = None) -> str:
        """Render a subgraph as a Mermaid diagram."""
        conn = self._get_connection()
        try:
            if asset_ids:
                placeholders = ",".join("?" for _ in asset_ids)
                assets_rows = conn.execute(f"SELECT * FROM assets WHERE id IN ({placeholders})", asset_ids).fetchall()
                rel_rows = conn.execute(f"SELECT * FROM relations WHERE source_id IN ({placeholders}) AND target_id IN ({placeholders})", asset_ids + asset_ids).fetchall()
            else:
                assets_rows = conn.execute("SELECT * FROM assets").fetchall()
                rel_rows = conn.execute("SELECT * FROM relations").fetchall()
        finally:
            conn.close()

        mermaid_lines = ["graph TD"]
        for row in assets_rows:
            node_id = row["id"].replace("-", "")
            name = row["name"]
            asset_type = row["asset_type"]
            mermaid_lines.append(f'    {node_id}["{name} ({asset_type})"]')

        for row in rel_rows:
            source = row["source_id"].replace("-", "")
            target = row["target_id"].replace("-", "")
            rel_type = row["relation_type"]
            mermaid_lines.append(f"    {source} -->|{rel_type}| {target}")

        return "\n".join(mermaid_lines)

    def _row_to_asset(self, row: sqlite3.Row) -> Asset:
        tags = []
        try:
            tags = json.loads(row["tags"]) if row["tags"] else []
        except Exception:
            pass

        properties = {}
        try:
            properties = json.loads(row["properties"]) if row["properties"] else {}
        except Exception:
            pass

        return Asset(
            id=row["id"],
            created_at=row["created_at"],
            name=row["name"],
            asset_type=AssetType(row["asset_type"]),
            hostname=row["hostname"],
            ip_address=row["ip_address"],
            properties=properties,
            tags=tags
        )


# Backward compatibility alias
AssetGraph = InfrastructureGraph
