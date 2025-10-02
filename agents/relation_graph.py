#!/usr/bin/env python3
"""
Module pour gérer et visualiser le graphe de relations entre entités Alteir
"""
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

sys.path.append(str(Path(__file__).parent.parent))

class EntityType(Enum):
    """Types d'entités dans le GDD"""
    PERSONNAGE = "personnage"
    LIEU = "lieu"
    COMMUNAUTE = "communauté"
    ESPECE = "espèce"
    OBJET = "objet"
    EVENEMENT = "événement"

class RelationType(Enum):
    """Types de relations entre entités"""
    # Relations personnages
    CONNAIT = "connaît"
    AMI = "ami"
    ENNEMI = "ennemi"
    FAMILLE = "famille"
    MENTOR = "mentor"
    RIVAL = "rival"
    
    # Relations spatiales
    HABITE = "habite"
    VISITE = "visite"
    CONTIENT = "contient"
    ADJACENT = "adjacent à"
    
    # Relations communautaires
    MEMBRE_DE = "membre de"
    DIRIGE = "dirige"
    OPPOSE_A = "opposé à"
    ALLIE_A = "allié à"
    
    # Relations objets/espèces
    POSSEDE = "possède"
    CREE = "crée"
    DETRUIT = "détruit"
    EST_DE_ESPECE = "est de l'espèce"
    
    # Relations événements
    PARTICIPE_A = "participe à"
    CAUSE = "cause"
    RESULTE_DE = "résulte de"

@dataclass
class Entity:
    """Représente une entité du GDD"""
    id: str
    name: str
    type: EntityType
    url: str
    properties: Dict[str, any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.id == other.id
        return False

@dataclass
class Relation:
    """Représente une relation entre deux entités"""
    source: Entity
    target: Entity
    type: RelationType
    properties: Dict[str, any] = field(default_factory=dict)
    bidirectional: bool = False
    weight: float = 1.0
    
    def reverse(self) -> 'Relation':
        """Retourne la relation inverse"""
        return Relation(
            source=self.target,
            target=self.source,
            type=self.type,
            properties=self.properties,
            bidirectional=self.bidirectional,
            weight=self.weight
        )

class RelationGraph:
    """Graphe de relations entre entités"""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self._adjacency: Dict[str, Set[str]] = {}
    
    def add_entity(self, entity: Entity):
        """Ajoute une entité au graphe"""
        self.entities[entity.id] = entity
        if entity.id not in self._adjacency:
            self._adjacency[entity.id] = set()
    
    def add_relation(self, relation: Relation):
        """Ajoute une relation au graphe"""
        # Ajouter les entités si elles n'existent pas
        if relation.source.id not in self.entities:
            self.add_entity(relation.source)
        if relation.target.id not in self.entities:
            self.add_entity(relation.target)
        
        # Ajouter la relation
        self.relations.append(relation)
        self._adjacency[relation.source.id].add(relation.target.id)
        
        # Si bidirectionnelle, ajouter la relation inverse
        if relation.bidirectional:
            self._adjacency[relation.target.id].add(relation.source.id)
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Récupère une entité par son ID"""
        return self.entities.get(entity_id)
    
    def get_relations_from(self, entity_id: str) -> List[Relation]:
        """Récupère toutes les relations partant d'une entité"""
        return [r for r in self.relations if r.source.id == entity_id]
    
    def get_relations_to(self, entity_id: str) -> List[Relation]:
        """Récupère toutes les relations arrivant à une entité"""
        return [r for r in self.relations if r.target.id == entity_id]
    
    def get_all_relations(self, entity_id: str) -> List[Relation]:
        """Récupère toutes les relations d'une entité (sortantes et entrantes)"""
        return self.get_relations_from(entity_id) + self.get_relations_to(entity_id)
    
    def get_neighbors(self, entity_id: str) -> Set[Entity]:
        """Récupère tous les voisins directs d'une entité"""
        neighbors = set()
        for relation in self.get_all_relations(entity_id):
            if relation.source.id == entity_id:
                neighbors.add(relation.target)
            else:
                neighbors.add(relation.source)
        return neighbors
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Récupère toutes les entités d'un type donné"""
        return [e for e in self.entities.values() if e.type == entity_type]
    
    def get_relations_by_type(self, relation_type: RelationType) -> List[Relation]:
        """Récupère toutes les relations d'un type donné"""
        return [r for r in self.relations if r.type == relation_type]
    
    def get_subgraph(self, entity_ids: List[str], depth: int = 1) -> 'RelationGraph':
        """Extrait un sous-graphe centré sur des entités avec une profondeur donnée"""
        subgraph = RelationGraph()
        visited = set()
        queue = [(eid, 0) for eid in entity_ids]
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            entity = self.get_entity(current_id)
            if entity:
                subgraph.add_entity(entity)
                
                # Ajouter les relations et voisins
                for relation in self.get_relations_from(current_id):
                    subgraph.add_relation(relation)
                    if current_depth < depth:
                        queue.append((relation.target.id, current_depth + 1))
        
        return subgraph
    
    def to_networkx(self):
        """Convertit le graphe en graphe NetworkX"""
        import networkx as nx
        
        G = nx.DiGraph()
        
        # Ajouter les nœuds
        for entity in self.entities.values():
            G.add_node(
                entity.id,
                name=entity.name,
                type=entity.type.value,
                url=entity.url,
                **entity.properties
            )
        
        # Ajouter les arêtes
        for relation in self.relations:
            G.add_edge(
                relation.source.id,
                relation.target.id,
                type=relation.type.value,
                weight=relation.weight,
                bidirectional=relation.bidirectional,
                **relation.properties
            )
        
        return G
    
    def stats(self) -> Dict[str, any]:
        """Retourne des statistiques sur le graphe"""
        entity_type_counts = {}
        for entity_type in EntityType:
            entity_type_counts[entity_type.value] = len(self.get_entities_by_type(entity_type))
        
        relation_type_counts = {}
        for relation_type in RelationType:
            relation_type_counts[relation_type.value] = len(self.get_relations_by_type(relation_type))
        
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entity_types": entity_type_counts,
            "relation_types": relation_type_counts,
            "avg_connections_per_entity": len(self.relations) / len(self.entities) if self.entities else 0
        }


def extract_relations_from_notion_entity(entity_data: Dict) -> List[Tuple[str, str, RelationType]]:
    """
    Extrait les relations depuis les données Notion d'une entité
    
    Args:
        entity_data: Données d'une entité depuis Notion (avec properties)
    
    Returns:
        Liste de tuples (source_id, target_id, relation_type)
    """
    relations = []
    entity_id = entity_data.get('id')
    properties = entity_data.get('properties', {})
    
    # Mapping des propriétés Notion vers les types de relations
    property_to_relation = {
        # Personnages
        "Communautés": RelationType.MEMBRE_DE,
        "Lieux de vie": RelationType.HABITE,
        "Détient": RelationType.POSSEDE,
        "Espèce": RelationType.EST_DE_ESPECE,
        
        # Lieux
        "Contient": RelationType.CONTIENT,
        "Zones limitrophes": RelationType.ADJACENT,
        "Communautés présentes": RelationType.MEMBRE_DE,  # inverse
        "Personnages présents": RelationType.HABITE,  # inverse
        "Objets présents": RelationType.POSSEDE,  # inverse
        "Faunes & Flores présentes": RelationType.EST_DE_ESPECE,  # inverse
        
        # Événements
        "Participants": RelationType.PARTICIPE_A,
    }
    
    # Extraire les relations
    for prop_name, relation_type in property_to_relation.items():
        if prop_name in properties:
            targets = properties[prop_name]
            if isinstance(targets, list):
                for target in targets:
                    target_id = target.get('id') if isinstance(target, dict) else target
                    if target_id:
                        relations.append((entity_id, target_id, relation_type))
    
    return relations

