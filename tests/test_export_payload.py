"""
Tests de construction du payload Notion

Vérifie que les propriétés sont correctement formatées pour l'API Notion
"""

import pytest
import re
from tests.test_export_extraction import extract_field, sample_personnage_content, sample_lieu_content


# ============================================================================
# Helper - Construction payload (simplifié de app_streamlit.py)
# ============================================================================

def build_notion_properties_personnage(content: str) -> dict:
    """Construit les propriétés Notion pour un personnage"""
    properties = {}
    
    # Nom (title)
    if nom := extract_field("Nom", content):
        properties["Nom"] = {"title": [{"text": {"content": nom}}]}
    
    # Selects
    if type_val := extract_field("Type", content):
        properties["Type"] = {"select": {"name": type_val}}
    if genre := extract_field("Genre", content):
        properties["Genre"] = {"select": {"name": genre}}
    if axe := extract_field("Axe idéologique", content):
        axe_clean = axe.split(',')[0].split(';')[0].strip()
        properties["Axe idéologique"] = {"select": {"name": axe_clean}}
    
    # Rich text
    if alias := extract_field("Alias", content):
        properties["Alias"] = {"rich_text": [{"text": {"content": alias}}]}
    if occupation := extract_field("Occupation", content):
        properties["Occupation"] = {"rich_text": [{"text": {"content": occupation}}]}
    if reponse := extract_field("Réponse au problème moral", content):
        properties["Réponse au problème moral"] = {
            "rich_text": [{"text": {"content": reponse[:2000]}}]
        }
    
    # Number
    if age_str := extract_field("Âge", content):
        try:
            age = int(re.search(r'\d+', age_str).group())
            properties["Âge"] = {"number": age}
        except:
            pass
    
    # Multi-select
    if archetype_raw := extract_field("Archétype littéraire", content):
        archetypes = [a.strip() for a in re.split(r'[,;]\s*', archetype_raw) if a.strip()]
        if archetypes:
            properties["Archétype littéraire"] = {
                "multi_select": [{"name": arch} for arch in archetypes]
            }
    
    if qualites_raw := extract_field("Qualités", content):
        qualites = [q.strip() for q in re.split(r'[,;]\s*', qualites_raw) if q.strip()]
        if qualites:
            properties["Qualités"] = {
                "multi_select": [{"name": qual} for qual in qualites]
            }
    
    if defauts_raw := extract_field("Défauts", content):
        defauts = [d.strip() for d in re.split(r'[,;]\s*', defauts_raw) if d.strip()]
        if defauts:
            properties["Défauts"] = {
                "multi_select": [{"name": def_} for def_ in defauts]
            }
    
    # État par défaut
    properties["État"] = {"status": {"name": "Brouillon IA"}}
    
    return properties


def build_notion_properties_lieu(content: str) -> dict:
    """Construit les propriétés Notion pour un lieu"""
    properties = {}
    
    # Nom (title)
    if nom := extract_field("Nom", content):
        properties["Nom"] = {"title": [{"text": {"content": nom}}]}
    
    # Selects
    for field_name in ["Catégorie", "Taille", "Rôle", "Sprint"]:
        if value := extract_field(field_name, content):
            value_clean = value.split(',')[0].split(';')[0].strip()[:100]
            properties[field_name] = {"select": {"name": value_clean}}
    
    # État par défaut
    properties["État"] = {"status": {"name": "Brouillon IA"}}
    
    return properties


# ============================================================================
# TESTS - Payload Personnage
# ============================================================================

@pytest.mark.unit
class TestPayloadPersonnage:
    """Tests de construction du payload Notion pour personnages"""
    
    def test_payload_has_title(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        assert "Nom" in props
        assert props["Nom"]["title"][0]["text"]["content"] == "Drarus Lumenflex"
    
    def test_payload_has_selects(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        
        assert "Type" in props
        assert props["Type"]["select"]["name"] == "PNJ"
        
        assert "Genre" in props
        assert props["Genre"]["select"]["name"] == "Masculin"
        
        assert "Axe idéologique" in props
        assert props["Axe idéologique"]["select"]["name"] == "Subversion"
    
    def test_payload_has_rich_text(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        
        assert "Alias" in props
        assert props["Alias"]["rich_text"][0]["text"]["content"] == "Le Tisseur d'Ombres"
        
        assert "Occupation" in props
        assert props["Occupation"]["rich_text"][0]["text"]["content"] == "Archiviste clandestin"
        
        assert "Réponse au problème moral" in props
        assert len(props["Réponse au problème moral"]["rich_text"][0]["text"]["content"]) > 0
    
    def test_payload_has_number(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        
        assert "Âge" in props
        assert props["Âge"]["number"] == 42
    
    def test_payload_has_multiselects(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        
        # Archétype
        assert "Archétype littéraire" in props
        archetypes = props["Archétype littéraire"]["multi_select"]
        assert len(archetypes) == 2
        archetype_names = [a["name"] for a in archetypes]
        assert "Mentor / Gourou" in archetype_names
        assert "Magicien / Sorcier" in archetype_names
        
        # Qualités
        assert "Qualités" in props
        qualites = props["Qualités"]["multi_select"]
        assert len(qualites) == 3
        qualite_names = [q["name"] for q in qualites]
        assert "Lucide" in qualite_names
        
        # Défauts
        assert "Défauts" in props
        defauts = props["Défauts"]["multi_select"]
        assert len(defauts) == 3
        defaut_names = [d["name"] for d in defauts]
        assert "Cynique" in defaut_names
    
    def test_payload_has_default_status(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        
        assert "État" in props
        assert props["État"]["status"]["name"] == "Brouillon IA"


# ============================================================================
# TESTS - Payload Lieu
# ============================================================================

@pytest.mark.unit
class TestPayloadLieu:
    """Tests de construction du payload Notion pour lieux"""
    
    def test_payload_has_title(self, sample_lieu_content):
        props = build_notion_properties_lieu(sample_lieu_content)
        assert "Nom" in props
        assert props["Nom"]["title"][0]["text"]["content"] == "Marché des Placides Respirants"
    
    def test_payload_has_selects(self, sample_lieu_content):
        props = build_notion_properties_lieu(sample_lieu_content)
        
        assert "Catégorie" in props
        assert props["Catégorie"]["select"]["name"] == "Lieu"
        
        assert "Taille" in props
        assert props["Taille"]["select"]["name"] == "Site"
        
        assert "Rôle" in props
        assert props["Rôle"]["select"]["name"] == "Lieu commercial"
        
        assert "Sprint" in props
        assert props["Sprint"]["select"]["name"] == "Sprint 1"
    
    def test_payload_has_default_status(self, sample_lieu_content):
        props = build_notion_properties_lieu(sample_lieu_content)
        
        assert "État" in props
        assert props["État"]["status"]["name"] == "Brouillon IA"


# ============================================================================
# TESTS - Validation structure
# ============================================================================

@pytest.mark.unit
class TestPayloadStructure:
    """Tests de validation de la structure du payload"""
    
    def test_title_property_structure(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        title = props["Nom"]
        
        assert "title" in title
        assert isinstance(title["title"], list)
        assert len(title["title"]) > 0
        assert "text" in title["title"][0]
        assert "content" in title["title"][0]["text"]
    
    def test_select_property_structure(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        select = props["Type"]
        
        assert "select" in select
        assert "name" in select["select"]
        assert isinstance(select["select"]["name"], str)
    
    def test_multiselect_property_structure(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        multiselect = props["Qualités"]
        
        assert "multi_select" in multiselect
        assert isinstance(multiselect["multi_select"], list)
        assert len(multiselect["multi_select"]) > 0
        for item in multiselect["multi_select"]:
            assert "name" in item
            assert isinstance(item["name"], str)
    
    def test_number_property_structure(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        number = props["Âge"]
        
        assert "number" in number
        assert isinstance(number["number"], (int, float))
    
    def test_rich_text_property_structure(self, sample_personnage_content):
        props = build_notion_properties_personnage(sample_personnage_content)
        rich_text = props["Alias"]
        
        assert "rich_text" in rich_text
        assert isinstance(rich_text["rich_text"], list)
        assert len(rich_text["rich_text"]) > 0
        assert "text" in rich_text["rich_text"][0]
        assert "content" in rich_text["rich_text"][0]["text"]


# ============================================================================
# TESTS - Champs critiques présents
# ============================================================================

@pytest.mark.unit
class TestChampsEssentiels:
    """Vérifie que tous les champs essentiels sont présents"""
    
    def test_personnage_champs_obligatoires(self, sample_personnage_content):
        """Vérifie les champs demandés par l'utilisateur"""
        props = build_notion_properties_personnage(sample_personnage_content)
        
        # Champs essentiels selon user query
        champs_obligatoires = [
            "Nom", "Type", "Genre", "Axe idéologique",
            "Archétype littéraire", "Qualités", "Défauts",
            "Réponse au problème moral", "État"
        ]
        
        for champ in champs_obligatoires:
            assert champ in props, f"Champ manquant: {champ}"
    
    def test_lieu_champs_obligatoires(self, sample_lieu_content):
        """Vérifie les champs essentiels pour lieux"""
        props = build_notion_properties_lieu(sample_lieu_content)
        
        champs_obligatoires = [
            "Nom", "Catégorie", "Taille", "Rôle", "État"
        ]
        
        for champ in champs_obligatoires:
            assert champ in props, f"Champ manquant: {champ}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

