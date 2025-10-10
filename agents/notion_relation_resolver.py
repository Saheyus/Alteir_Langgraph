"""
Résolveur de relations Notion avec fuzzy matching

Permet de :
- Fetch les noms d'entités existantes dans Notion (léger)
- Fuzzy matching pour correspondances approximatives
- Cache en mémoire pour performances
- Architecture extensible pour auto-création future
"""

import os
import requests
import unicodedata
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
from dataclasses import dataclass
from config.notion_config import NotionConfig


@dataclass
class EntityMatch:
    """Résultat d'un match fuzzy"""
    original_name: str
    matched_name: str
    notion_id: str
    confidence: float
    domain: str


class NotionRelationResolver:
    """
    Résolveur intelligent de relations Notion
    
    Features:
    - Fetch léger (noms uniquement)
    - Fuzzy matching configurable
    - Cache session
    - Extensible pour auto-création
    """
    
    def __init__(self, fuzzy_threshold: float = 0.80, auto_create: bool = False):
        """
        Args:
            fuzzy_threshold: Score minimum pour considérer un match (0-1)
            auto_create: Si True, crée automatiquement les entités manquantes (Phase 2)
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.auto_create = auto_create
        self.cache: Dict[str, Dict[str, str]] = {}  # {domain: {name_normalized: notion_id}}
        self.cache_metadata: Dict[str, Dict[str, dict]] = {}  # {domain: {notion_id: metadata}}
        
        # Configuration Notion (centralisée)
        self.notion_token = NotionConfig.NOTION_TOKEN or os.getenv("NOTION_TOKEN")
        self.notion_version = NotionConfig.API_VERSION
        
        # Mapping domaines → Database IDs (PRINCIPALES pour relations)
        # Note: Les entités créées vont dans les sandbox,
        # mais peuvent référencer les bases principales
        self.database_ids = {
            "personnages": "1886e4d21b4581a29340f77f5f2e5885",  # Personnages (principale)
            "lieux": "1886e4d21b4581eda022ea4e0f1aba5f",        # Lieux (principale)
            "communautes": "1886e4d21b4581dea4f4d01beb5e1be2",  # Communautés (principale)
            "especes": "1886e4d21b4581e9a768df06185c1aea",      # Espèces (principale)
            "objets": "1886e4d21b4581098024c61acd801f52",       # Objets (principale)
            # Alias pour compatibilité
            "espèces": "1886e4d21b4581e9a768df06185c1aea",
            "communautés": "1886e4d21b4581dea4f4d01beb5e1be2",
        }
    
    def normalize_name(self, name: str) -> str:
        """Normalise un nom pour comparaison (minuscules, sans accents, articles)"""
        # Retirer accents
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        
        # Minuscules
        name = name.lower().strip()
        
        # Retirer articles courants
        for article in ['le ', 'la ', 'les ', 'l\'', 'un ', 'une ', 'des ']:
            if name.startswith(article):
                name = name[len(article):]
        
        # Nettoyer espaces multiples
        name = ' '.join(name.split())
        
        return name
    
    def fetch_entity_names(self, domain: str, force_refresh: bool = False) -> Dict[str, str]:
        """
        Fetch les noms d'entités depuis Notion (léger, noms uniquement)
        
        Args:
            domain: 'personnages', 'lieux', etc.
            force_refresh: Force le re-fetch même si en cache
        
        Returns:
            Dict {name_normalized: notion_id}
        """
        if domain in self.cache and not force_refresh:
            return self.cache[domain]
        
        database_id = self.database_ids.get(domain)
        if not database_id:
            print(f"Warning: Domain '{domain}' not configured")
            return {}
        
        # Formater l'ID avec tirets (format UUID)
        # 2806e4d21b458012a744d8d6723c8be1 → 2806e4d2-1b45-8012-a744-d8d6723c8be1
        if "-" not in database_id and len(database_id) == 32:
            database_id = f"{database_id[:8]}-{database_id[8:12]}-{database_id[12:16]}-{database_id[16:20]}-{database_id[20:]}"
        
        entities = {}
        metadata = {}
        
        try:
            # Fetch depuis Notion (Database Query API)
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Notion-Version": self.notion_version,
                "Content-Type": "application/json"
            }
            
            # Query pour récupérer toutes les pages de la database
            url = f"https://api.notion.com/v1/databases/{database_id}/query"
            
            has_more = True
            start_cursor = None
            
            while has_more:
                payload = {"page_size": 100}
                if start_cursor:
                    payload["start_cursor"] = start_cursor
                
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    print(f"Error fetching from Notion: {response.status_code} - {response.text}")
                    return {}
                
                data = response.json()
                results = data.get("results", [])
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")
                
                # Extraire les titres
                for page in results:
                    properties = page.get("properties", {})
                    
                    # Trouver la propriété title (peut s'appeler "Nom", "Name", etc.)
                    title_prop = None
                    for prop_name, prop_value in properties.items():
                        if prop_value.get("type") == "title":
                            title_prop = prop_value
                            break
                    
                    if title_prop:
                        title_array = title_prop.get("title", [])
                        if title_array and len(title_array) > 0:
                            name = title_array[0].get("plain_text", "").strip()
                            if name:
                                notion_id = page["id"]
                                normalized = self.normalize_name(name)
                                entities[normalized] = notion_id
                                metadata[notion_id] = {
                                    "name": name,
                                    "url": page.get("url", "")
                                }
            
        except Exception as e:
            print(f"Error in fetch_entity_names: {e}")
            return {}
        
        # Mise en cache
        self.cache[domain] = entities
        self.cache_metadata[domain] = metadata
        
        return entities
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calcule la similarité entre deux chaînes (0-1)
        
        Combine plusieurs méthodes :
        - Ratio global (pour correspondances exactes)
        - Partial ratio (pour substrings)
        - Début de chaîne (pour préfixes)
        - Mots composés (ex: "Humain modifié" → "Humains")
        """
        # 1. Ratio global classique
        global_ratio = SequenceMatcher(None, str1, str2).ratio()
        
        # 2. Partial matching : vérifier si l'un est dans l'autre
        shorter, longer = (str1, str2) if len(str1) < len(str2) else (str2, str1)
        
        if shorter in longer:
            # Substring exacte : score élevé basé sur la proportion
            base_ratio = len(shorter) / len(longer)
            
            # Boost important si c'est au début (préfixe)
            if longer.startswith(shorter):
                # Préfixe exact : score minimum 0.75 (très bon match)
                partial_ratio = max(0.75, base_ratio * 2)
            else:
                # Substring au milieu/fin : score minimum 0.60
                partial_ratio = max(0.60, base_ratio * 1.5)
        else:
            # Pas de substring exacte : utiliser le ratio des mots communs
            words1 = set(str1.split())
            words2 = set(str2.split())
            if words1 and words2:
                common_words = words1.intersection(words2)
                partial_ratio = len(common_words) / max(len(words1), len(words2))
            else:
                partial_ratio = 0.0
        
        # 3. Mots composés : si le 1er mot matche bien, boost le score
        # Ex: "humain modifie" → "humains" (premier mot très similaire)
        words1_list = str1.split()
        words2_list = str2.split()
        if words1_list and words2_list:
            first_word_ratio = SequenceMatcher(None, words1_list[0], words2_list[0]).ratio()
            # Si le premier mot matche à > 80%, considérer comme bon match
            if first_word_ratio >= 0.80:
                partial_ratio = max(partial_ratio, 0.85)
        
        # 4. Prendre le meilleur score
        return max(global_ratio, partial_ratio)
    
    def find_match(self, name: str, domain: str) -> Optional[EntityMatch]:
        """
        Trouve la meilleure correspondance pour un nom
        
        Args:
            name: Nom à rechercher (peut être approximatif)
            domain: Domaine de recherche
        
        Returns:
            EntityMatch si match trouvé avec confiance > threshold, sinon None
        """
        # Fetch les entités si pas en cache
        entities = self.fetch_entity_names(domain)
        
        if not entities:
            return None
        
        # Normaliser le nom recherché
        normalized_query = self.normalize_name(name)
        
        # Recherche exacte d'abord
        if normalized_query in entities:
            notion_id = entities[normalized_query]
            metadata = self.cache_metadata[domain][notion_id]
            return EntityMatch(
                original_name=name,
                matched_name=metadata["name"],
                notion_id=notion_id,
                confidence=1.0,
                domain=domain
            )
        
        # Fuzzy matching
        best_match = None
        best_score = 0.0
        
        # Itérer de façon déterministe (ordre lexical)
        for normalized_name, notion_id in sorted(entities.items(), key=lambda it: it[0]):
            score = self.calculate_similarity(normalized_query, normalized_name)
            if score > best_score:
                best_score = score
                best_match = (normalized_name, notion_id)
        
        # Vérifier si le score dépasse le threshold
        if best_match and best_score >= self.fuzzy_threshold:
            notion_id = best_match[1]
            metadata = self.cache_metadata[domain][notion_id]
            return EntityMatch(
                original_name=name,
                matched_name=metadata["name"],
                notion_id=notion_id,
                confidence=best_score,
                domain=domain
            )
        
        return None
    
    def resolve_relations(self, names: List[str], domain: str) -> List[Tuple[str, Optional[EntityMatch]]]:
        """
        Résout une liste de noms vers leurs IDs Notion
        
        Args:
            names: Liste de noms à résoudre
            domain: Domaine cible
        
        Returns:
            Liste de (name, EntityMatch or None)
        """
        results: List[Tuple[str, Optional[EntityMatch]]] = []
        seen_ids: set[str] = set()
        for name in names:
            match = self.find_match(name, domain)
            if match and match.notion_id in seen_ids:
                # Déduplication des relations sur l'ID Notion
                results.append((name, None))
                continue
            if match:
                seen_ids.add(match.notion_id)
            results.append((name, match))
        return results
    
    def create_stub(self, name: str, domain: str) -> Optional[str]:
        """
        Crée une fiche "stub" pour une entité manquante
        
        Phase 2 - Désactivé par défaut
        
        Args:
            name: Nom de l'entité
            domain: Domaine cible
        
        Returns:
            ID Notion de la fiche créée, ou None si désactivé
        """
        if not self.auto_create:
            return None
        
        # TODO: Implémenter création automatique (Phase 2)
        # - Créer page minimale dans Notion
        # - Tag "Auto-créé"
        # - Retourner l'ID
        
        print(f"Auto-creation not yet implemented for: {name} ({domain})")
        return None


# Fonction helper pour usage direct
def resolve_relation_list(
    raw_text: str,
    domain: str,
    resolver: Optional[NotionRelationResolver] = None
) -> List[dict]:
    """
    Helper: Parse une liste de noms séparés par virgules et résout vers Notion
    
    Args:
        raw_text: "Les Cartographes, Guilde des Enlumineurs"
        domain: "communautes"
        resolver: Instance du resolver (créé si None)
    
    Returns:
        Liste de dicts pour Notion API: [{"id": "xxx"}, {"id": "yyy"}]
    """
    if not resolver:
        resolver = NotionRelationResolver()
    
    # Split par virgules/points-virgules
    import re
    names = re.split(r'[,;]\s*', raw_text)
    names = [n.strip() for n in names if n.strip()]
    
    # Résoudre
    resolved_ids = []
    unresolved = []
    
    for name in names:
        match = resolver.find_match(name, domain)
        if match:
            resolved_ids.append({"id": match.notion_id})
        else:
            unresolved.append(name)
    
    # Log des non-résolus
    if unresolved:
        print(f"[WARNING] Unresolved {domain}: {', '.join(unresolved)}")
    
    return resolved_ids


if __name__ == "__main__":
    # Fix encodage Windows
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Test du resolver
    print("=== Test NotionRelationResolver ===\n")
    
    resolver = NotionRelationResolver(fuzzy_threshold=0.80)
    
    # Test fetch
    print("1. Fetch personnages...")
    entities = resolver.fetch_entity_names("personnages")
    print(f"   > {len(entities)} personnages en cache")
    
    # Afficher les 5 premiers pour debug
    print("\n   Premiers personnages:")
    for i, (normalized, notion_id) in enumerate(list(entities.items())[:5]):
        metadata = resolver.cache_metadata["personnages"][notion_id]
        print(f"   - {metadata['name']} (normalisé: '{normalized}')")
    print()
    
    # Test matching exact
    print("2. Test matching exact: 'Bardin Kerlain'")
    match = resolver.find_match("Bardin Kerlain", "personnages")
    if match:
        print(f"   [OK] Match: '{match.matched_name}' (confiance: {match.confidence:.0%})")
        print(f"   ID: {match.notion_id}\n")
    else:
        print(f"   [X] Pas de match\n")
    
    # Test fuzzy matching
    print("3. Test fuzzy matching: 'bardin' (minuscules partiel)")
    match = resolver.find_match("bardin", "personnages")
    if match:
        print(f"   [OK] Match: '{match.matched_name}' (confiance: {match.confidence:.0%})\n")
    else:
        print(f"   [X] Pas de match\n")
    
    # Test no match
    print("4. Test no match: 'Jean-Michel Inexistant'")
    match = resolver.find_match("Jean-Michel Inexistant", "personnages")
    if match:
        print(f"   [OK] Match trouve: '{match.matched_name}'")
    else:
        print(f"   [X] Pas de match (normal)\n")
    
    print("=== Test terminé ===")

