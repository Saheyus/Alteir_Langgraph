"""
Extracteur de relations depuis les fiches générées

Parse les fichiers JSON générés pour extraire les entités et leurs relations.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from agents.relation_graph import Entity, Relation, RelationGraph, EntityType, RelationType


class RelationExtractor:
    """Extrait les relations depuis les fiches générées"""
    
    def __init__(self, outputs_dir: str = "outputs"):
        self.outputs_dir = Path(outputs_dir)
    
    def extract_from_outputs(self) -> RelationGraph:
        """
        Extrait toutes les relations depuis le dossier outputs
        
        Returns:
            RelationGraph avec toutes les entités et relations
        """
        graph = RelationGraph()
        
        # Charger tous les fichiers JSON
        json_files = list(self.outputs_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._extract_from_data(data, graph)
            except Exception as e:
                print(f"Erreur lors du chargement de {json_file}: {e}")
        
        return graph
    
    def _extract_from_data(self, data: Dict, graph: RelationGraph):
        """Extrait entités et relations d'une fiche"""
        domain = data.get('domain', 'personnages').lower()
        content = data.get('content', '')
        
        # Déterminer le type d'entité
        if domain == 'personnages':
            entity_type = EntityType.CHARACTER
        elif domain == 'lieux':
            entity_type = EntityType.LOCATION
        elif domain == 'communautes':
            entity_type = EntityType.COMMUNITY
        elif domain == 'objets':
            entity_type = EntityType.ITEM
        else:
            entity_type = EntityType.OTHER
        
        # Extraire le nom de l'entité principale
        nom = self._extract_field("Nom", content)
        if not nom:
            return
        
        # Créer l'entité principale
        entity = Entity(
            id=self._generate_id(nom),
            name=nom,
            type=entity_type,
            metadata={
                'domain': domain,
                'coherence_score': data.get('coherence_score', 0.0),
                'quality_score': data.get('quality_score', 0.0)
            }
        )
        graph.add_entity(entity)
        
        # Extraire les relations selon le domaine
        if domain == 'personnages':
            self._extract_personnage_relations(entity, content, graph)
        elif domain == 'lieux':
            self._extract_lieu_relations(entity, content, graph)
    
    def _extract_personnage_relations(self, entity: Entity, content: str, graph: RelationGraph):
        """Extrait les relations d'un personnage"""
        # Communautés
        communautes = self._extract_field("Communautés", content)
        if communautes:
            for comm in self._split_list(communautes):
                comm_entity = Entity(
                    id=self._generate_id(comm),
                    name=comm,
                    type=EntityType.COMMUNITY
                )
                graph.add_entity(comm_entity)
                graph.add_relation(Relation(
                    source_id=entity.id,
                    target_id=comm_entity.id,
                    type=RelationType.MEMBER_OF,
                    metadata={'extracted_from': 'Communautés'}
                ))
        
        # Lieux de vie
        lieux = self._extract_field("Lieux de vie", content)
        if lieux:
            for lieu in self._split_list(lieux):
                lieu_entity = Entity(
                    id=self._generate_id(lieu),
                    name=lieu,
                    type=EntityType.LOCATION
                )
                graph.add_entity(lieu_entity)
                graph.add_relation(Relation(
                    source_id=entity.id,
                    target_id=lieu_entity.id,
                    type=RelationType.LIVES_IN,
                    metadata={'extracted_from': 'Lieux de vie'}
                ))
        
        # Objets détenus
        objets = self._extract_field("Détient", content)
        if objets:
            for obj in self._split_list(objets):
                obj_entity = Entity(
                    id=self._generate_id(obj),
                    name=obj,
                    type=EntityType.ITEM
                )
                graph.add_entity(obj_entity)
                graph.add_relation(Relation(
                    source_id=entity.id,
                    target_id=obj_entity.id,
                    type=RelationType.OWNS,
                    metadata={'extracted_from': 'Détient'}
                ))
        
        # Relations interpersonnelles (parsing du texte)
        self._extract_interpersonal_relations(entity, content, graph)
    
    def _extract_lieu_relations(self, entity: Entity, content: str, graph: RelationGraph):
        """Extrait les relations d'un lieu"""
        # Communautés présentes
        communautes = self._extract_field("Communautés présentes", content)
        if communautes:
            for comm in self._split_list(communautes):
                comm_entity = Entity(
                    id=self._generate_id(comm),
                    name=comm,
                    type=EntityType.COMMUNITY
                )
                graph.add_entity(comm_entity)
                graph.add_relation(Relation(
                    source_id=comm_entity.id,
                    target_id=entity.id,
                    type=RelationType.LOCATED_IN,
                    metadata={'extracted_from': 'Communautés présentes'}
                ))
        
        # Personnages présents
        personnages = self._extract_field("Personnages présents", content)
        if personnages:
            for perso in self._split_list(personnages):
                perso_entity = Entity(
                    id=self._generate_id(perso),
                    name=perso,
                    type=EntityType.CHARACTER
                )
                graph.add_entity(perso_entity)
                graph.add_relation(Relation(
                    source_id=perso_entity.id,
                    target_id=entity.id,
                    type=RelationType.LOCATED_IN,
                    metadata={'extracted_from': 'Personnages présents'}
                ))
        
        # Zones limitrophes
        zones = self._extract_field("Zones limitrophes", content)
        if zones:
            for zone in self._split_list(zones):
                zone_entity = Entity(
                    id=self._generate_id(zone),
                    name=zone,
                    type=EntityType.LOCATION
                )
                graph.add_entity(zone_entity)
                graph.add_relation(Relation(
                    source_id=entity.id,
                    target_id=zone_entity.id,
                    type=RelationType.ADJACENT_TO,
                    metadata={'extracted_from': 'Zones limitrophes'}
                ))
        
        # Contenu par / Contient
        contenu_par = self._extract_field("Contenu par", content)
        if contenu_par:
            for parent in self._split_list(contenu_par):
                parent_entity = Entity(
                    id=self._generate_id(parent),
                    name=parent,
                    type=EntityType.LOCATION
                )
                graph.add_entity(parent_entity)
                graph.add_relation(Relation(
                    source_id=parent_entity.id,
                    target_id=entity.id,
                    type=RelationType.CONTAINS,
                    metadata={'extracted_from': 'Contenu par'}
                ))
        
        contient = self._extract_field("Contient", content)
        if contient:
            for child in self._split_list(contient):
                child_entity = Entity(
                    id=self._generate_id(child),
                    name=child,
                    type=EntityType.LOCATION
                )
                graph.add_entity(child_entity)
                graph.add_relation(Relation(
                    source_id=entity.id,
                    target_id=child_entity.id,
                    type=RelationType.CONTAINS,
                    metadata={'extracted_from': 'Contient'}
                ))
    
    def _extract_interpersonal_relations(self, entity: Entity, content: str, graph: RelationGraph):
        """Extrait les relations interpersonnelles depuis le texte narratif"""
        # Parser la section Relations
        relations_section = re.search(
            r'##\s*Relations\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        
        if not relations_section:
            return
        
        relations_text = relations_section.group(1)
        
        # Patterns pour détecter des noms propres (majuscules)
        # Ex: "sa mère, Miro, un Gedroth"
        names = re.findall(r'\b([A-Z][a-zéèêà]+(?:\s+[A-Z][a-zéèêà]+)?)\b', relations_text)
        
        for name in set(names):
            # Éviter les mots courants en français
            if name.lower() in ['il', 'elle', 'ils', 'elles', 'sa', 'son', 'ses', 'les', 'la', 'le']:
                continue
            
            related_entity = Entity(
                id=self._generate_id(name),
                name=name,
                type=EntityType.CHARACTER
            )
            graph.add_entity(related_entity)
            graph.add_relation(Relation(
                source_id=entity.id,
                target_id=related_entity.id,
                type=RelationType.KNOWS,
                metadata={'extracted_from': 'Relations (texte)'}
            ))
    
    def _extract_field(self, field_name: str, content: str) -> str:
        """Extrait un champ du contenu (réutilise la logique de app_streamlit)"""
        # Format 1: "- **Nom**: valeur"
        pattern_bold = rf'^-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
        match = re.search(pattern_bold, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Format 2: "- Nom: valeur"
        pattern_plain = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
        match = re.search(pattern_plain, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Format 3: Section "CHAMPS NOTION"
        section_match = re.search(
            r'CHAMPS NOTION.*?\n(.*?)(?:\n\n|CONTENU NARRATIF|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if section_match:
            section_content = section_match.group(1)
            pattern_in_section = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
            match = re.search(pattern_in_section, section_content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _split_list(self, text: str) -> List[str]:
        """Split une liste de valeurs séparées par virgules ou points-virgules"""
        # Nettoyer et splitter
        items = re.split(r'[,;]\s*', text)
        return [item.strip() for item in items if item.strip()]
    
    def _generate_id(self, name: str) -> str:
        """Génère un ID unique depuis un nom"""
        # Normaliser: minuscules, sans accents, tirets au lieu d'espaces
        import unicodedata
        normalized = unicodedata.normalize('NFD', name.lower())
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        normalized = re.sub(r'[^a-z0-9]+', '-', normalized).strip('-')
        return normalized


if __name__ == "__main__":
    # Test extraction
    extractor = RelationExtractor()
    graph = extractor.extract_from_outputs()
    
    print(f"Entités extraites: {len(graph.entities)}")
    print(f"Relations extraites: {len(graph.relations)}")
    
    # Afficher quelques exemples
    for entity_id, entity in list(graph.entities.items())[:5]:
        print(f"\n{entity.name} ({entity.type.value})")
        relations = graph.get_relations_for_entity(entity_id)
        print(f"  {len(relations)} relation(s)")

