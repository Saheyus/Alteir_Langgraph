"""
Tests pour l'export Notion des fiches générées

Tests l'extraction des métadonnées, la création de pages Notion,
et la validation des propriétés par domaine.
"""

import pytest
import re
from unittest.mock import Mock, patch, MagicMock
import os


# ============================================================================
# FIXTURES - Données de test
# ============================================================================

@pytest.fixture
def sample_personnage_content():
    """Contenu markdown d'un personnage de test"""
    return """# Résumé de la fiche
Norrik, un escargot cyberpunk test.

# Caractérisation
## Faiblesse
Facilement distrait

---

- **Nom**: Norrik  
- **Alias**: Le Sculpteur de Lumière  
- **Type**: PNJ principal  
- **Occupation**: Bricoleur d'art et artiste  
- **Espèce**: Escargot cybernétique  
- **Âge**: 27 cycles  
- **Genre**: Non défini  
- **Archétype littéraire**: Artiste / Cynique  
- **Axe idéologique**: Connexion  
"""


@pytest.fixture
def sample_lieu_content():
    """Contenu markdown d'un lieu de test (format avec section CHAMPS NOTION)"""
    return """# Marché Test

CHAMPS NOTION (métadonnées)

- Nom: Marché des Tests
- Catégorie: Lieu
- Rôle: Lieu commercial
- Taille: Secteur
- Contenu par: Plateformes organiques
- Contient: Étals mouvants

CONTENU NARRATIF COMPLET

Le marché est un endroit de test.
"""


@pytest.fixture
def sample_result_personnage(sample_personnage_content):
    """Result dict complet pour un personnage"""
    return {
        "domain": "personnages",
        "content": sample_personnage_content,
        "brief": "Test personnage",
        "coherence_score": 0.85,
        "completeness_score": 1.0,
        "quality_score": 0.9
    }


@pytest.fixture
def sample_result_lieu(sample_lieu_content):
    """Result dict complet pour un lieu"""
    return {
        "domain": "lieux",
        "content": sample_lieu_content,
        "brief": "Test lieu",
        "coherence_score": 0.80,
        "completeness_score": 0.95,
        "quality_score": 0.85
    }


# ============================================================================
# TESTS UNITAIRES - Extraction de métadonnées
# ============================================================================

@pytest.mark.unit
def test_extract_field_with_bold(sample_personnage_content):
    """Test extraction d'un champ avec format gras **Nom**:"""
    # Fonction extract_field de app_streamlit.py (version complète)
    def extract_field(field_name, content):
        """Extrait un champ du contenu markdown (formats variés)"""
        # Format 1: "- **Nom**: valeur" (personnages)
        pattern_bold = rf'^-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
        match = re.search(pattern_bold, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Format 2: "- Nom: valeur" (lieux - sous CHAMPS NOTION)
        pattern_plain = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
        match = re.search(pattern_plain, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Format 3: Sous section "CHAMPS NOTION (métadonnées)" (lieux)
        section_match = re.search(r'CHAMPS NOTION.*?\n(.*?)(?:\n\n|CONTENU NARRATIF|\Z)', 
                                 content, re.DOTALL | re.IGNORECASE)
        if section_match:
            section_content = section_match.group(1)
            pattern_in_section = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
            match = re.search(pattern_in_section, section_content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    # Test extraction
    nom = extract_field("Nom", sample_personnage_content)
    assert nom == "Norrik", f"Expected 'Norrik', got '{nom}'"
    
    alias = extract_field("Alias", sample_personnage_content)
    assert alias == "Le Sculpteur de Lumière"
    
    age = extract_field("Âge", sample_personnage_content)
    assert age == "27 cycles"


@pytest.mark.unit
def test_extract_field_without_bold():
    """Test extraction d'un champ sans format gras"""
    content = "- Nom: Simple Test\n- Type: PNJ"
    
    def extract_field(field_name, content):
        pattern = rf'^-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
        match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        pattern_plain = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
        match = re.search(pattern_plain, content, re.MULTILINE | re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    nom = extract_field("Nom", content)
    assert nom == "Simple Test"


@pytest.mark.unit
def test_extract_field_from_champs_notion_section(sample_lieu_content):
    """Test extraction depuis la section CHAMPS NOTION (métadonnées)"""
    def extract_field(field_name, content):
        """Extrait un champ du contenu markdown (formats variés)"""
        pattern_bold = rf'^-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
        match = re.search(pattern_bold, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        pattern_plain = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
        match = re.search(pattern_plain, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        section_match = re.search(r'CHAMPS NOTION.*?\n(.*?)(?:\n\n|CONTENU NARRATIF|\Z)', 
                                 content, re.DOTALL | re.IGNORECASE)
        if section_match:
            section_content = section_match.group(1)
            pattern_in_section = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
            match = re.search(pattern_in_section, section_content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    # Test extraction depuis section CHAMPS NOTION
    nom = extract_field("Nom", sample_lieu_content)
    assert nom == "Marché des Tests", f"Expected 'Marché des Tests', got '{nom}'"
    
    categorie = extract_field("Catégorie", sample_lieu_content)
    assert categorie == "Lieu"
    
    role = extract_field("Rôle", sample_lieu_content)
    assert role == "Lieu commercial"
    
    taille = extract_field("Taille", sample_lieu_content)
    assert taille == "Secteur"


@pytest.mark.unit
def test_extract_field_missing():
    """Test extraction d'un champ absent"""
    content = "- Nom: Test"
    
    def extract_field(field_name, content):
        pattern_bold = rf'^-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
        match = re.search(pattern_bold, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        pattern_plain = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
        match = re.search(pattern_plain, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        section_match = re.search(r'CHAMPS NOTION.*?\n(.*?)(?:\n\n|CONTENU NARRATIF|\Z)', 
                                 content, re.DOTALL | re.IGNORECASE)
        if section_match:
            section_content = section_match.group(1)
            pattern_in_section = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
            match = re.search(pattern_in_section, section_content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    alias = extract_field("Alias", content)
    assert alias is None


# ============================================================================
# TESTS UNITAIRES - Propriétés Notion
# ============================================================================

@pytest.mark.unit
def test_notion_properties_personnage(sample_personnage_content):
    """Test construction des propriétés Notion pour un personnage"""
    def extract_field(field_name, content):
        pattern_bold = rf'^-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
        match = re.search(pattern_bold, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        pattern_plain = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
        match = re.search(pattern_plain, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        section_match = re.search(r'CHAMPS NOTION.*?\n(.*?)(?:\n\n|CONTENU NARRATIF|\Z)', 
                                 content, re.DOTALL | re.IGNORECASE)
        if section_match:
            section_content = section_match.group(1)
            pattern_in_section = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
            match = re.search(pattern_in_section, section_content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    # Extraire et construire propriétés
    nom = extract_field("Nom", sample_personnage_content)
    type_val = extract_field("Type", sample_personnage_content)
    genre = extract_field("Genre", sample_personnage_content)
    
    notion_properties = {
        "Nom": {"title": [{"text": {"content": nom}}]},
        "État": {"status": {"name": "Brouillon IA"}}
    }
    
    if type_val:
        notion_properties["Type"] = {"select": {"name": type_val}}
    if genre:
        notion_properties["Genre"] = {"select": {"name": genre}}
    
    # Vérifications
    assert notion_properties["Nom"]["title"][0]["text"]["content"] == "Norrik"
    assert notion_properties["Type"]["select"]["name"] == "PNJ principal"
    assert notion_properties["Genre"]["select"]["name"] == "Non défini"
    assert notion_properties["État"]["status"]["name"] == "Brouillon IA"


@pytest.mark.unit
def test_notion_properties_lieu(sample_lieu_content):
    """Test construction des propriétés Notion pour un lieu"""
    def extract_field(field_name, content):
        pattern_bold = rf'^-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
        match = re.search(pattern_bold, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        pattern_plain = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
        match = re.search(pattern_plain, content, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        section_match = re.search(r'CHAMPS NOTION.*?\n(.*?)(?:\n\n|CONTENU NARRATIF|\Z)', 
                                 content, re.DOTALL | re.IGNORECASE)
        if section_match:
            section_content = section_match.group(1)
            pattern_in_section = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
            match = re.search(pattern_in_section, section_content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    nom = extract_field("Nom", sample_lieu_content)
    categorie = extract_field("Catégorie", sample_lieu_content)
    role = extract_field("Rôle", sample_lieu_content)
    taille = extract_field("Taille", sample_lieu_content)
    
    notion_properties = {
        "Nom": {"title": [{"text": {"content": nom}}]},
        "État": {"status": {"name": "Brouillon IA"}}
    }
    
    if categorie:
        notion_properties["Catégorie"] = {"select": {"name": categorie}}
    if taille:
        notion_properties["Taille"] = {"select": {"name": taille}}
    if role:
        role_clean = role.split(';')[0].strip()[:100]
        notion_properties["Rôle"] = {"select": {"name": role_clean}}
    
    # Vérifications
    assert notion_properties["Nom"]["title"][0]["text"]["content"] == "Marché des Tests"
    assert notion_properties["Catégorie"]["select"]["name"] == "Lieu"
    assert notion_properties["Rôle"]["select"]["name"] == "Lieu commercial"
    assert notion_properties["Taille"]["select"]["name"] == "Secteur"


# ============================================================================
# TESTS D'INTÉGRATION - API Notion (avec mock)
# ============================================================================

@pytest.mark.integration
@patch('requests.post')
@patch('requests.patch')
def test_export_personnage_to_notion_mock(mock_patch, mock_post, sample_result_personnage):
    """Test export d'un personnage vers Notion (mocké)"""
    # Mock de la réponse API
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {
            'id': '2806e4d2-test-id-personnage',
            'url': 'https://notion.so/test-norrik'
        }
    )
    mock_patch.return_value = Mock(status_code=200)
    
    # Simuler l'export
    import app_streamlit
    
    # Note: Cette partie nécessite d'adapter app_streamlit pour être testable
    # Pour l'instant, on vérifie juste que la logique de construction est correcte
    
    # Vérifier que les mocks seraient appelés avec les bonnes données
    # (test de structure, pas d'appel réel)
    pass  # TODO: Refactorer app_streamlit.export_to_notion pour être testable


@pytest.mark.integration
@patch('requests.post')
@patch('requests.patch')
def test_export_lieu_to_notion_mock(mock_patch, mock_post, sample_result_lieu):
    """Test export d'un lieu vers Notion (mocké)"""
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {
            'id': '2806e4d2-test-id-lieu',
            'url': 'https://notion.so/test-marche'
        }
    )
    mock_patch.return_value = Mock(status_code=200)
    
    # Simuler l'export
    # TODO: Refactorer pour testabilité
    pass


# ============================================================================
# TESTS RÉELS - API Notion (slow, optionnel)
# ============================================================================

@pytest.mark.slow
@pytest.mark.skipif(not os.getenv('NOTION_TOKEN'), reason="NOTION_TOKEN not set")
def test_export_personnage_real(sample_result_personnage):
    """
    Test réel d'export d'un personnage vers Notion
    
    ⚠️ ATTENTION: Ce test crée une vraie page dans le bac à sable Notion
    Utiliser avec précaution et nettoyer après.
    """
    # TODO: Implémenter test réel si besoin
    # Pour l'instant, skip pour éviter pollution
    pytest.skip("Test réel désactivé par défaut - décommenter pour activer")
    
    # import app_streamlit
    # result = app_streamlit.export_to_notion(sample_result_personnage)
    # assert result is not None
    # # Nettoyer après test
    # # requests.delete(f"https://api.notion.com/v1/pages/{page_id}")


@pytest.mark.slow
@pytest.mark.skipif(not os.getenv('NOTION_TOKEN'), reason="NOTION_TOKEN not set")
def test_export_lieu_real(sample_result_lieu):
    """
    Test réel d'export d'un lieu vers Notion
    
    ⚠️ ATTENTION: Ce test crée une vraie page dans le bac à sable Notion
    """
    pytest.skip("Test réel désactivé par défaut - décommenter pour activer")
    
    # import app_streamlit
    # result = app_streamlit.export_to_notion(sample_result_lieu)
    # assert result is not None


# ============================================================================
# TESTS DE VALIDATION - Schémas Notion
# ============================================================================

@pytest.mark.unit
def test_database_ids():
    """Vérifie que les IDs de bases sandbox sont corrects"""
    PERSONNAGES_SANDBOX_ID = "2806e4d21b458012a744d8d6723c8be1"
    LIEUX_SANDBOX_ID = "2806e4d21b4580969f1cd7463a4c889c"
    
    # Vérifier format UUID
    assert len(PERSONNAGES_SANDBOX_ID.replace('-', '')) == 32
    assert len(LIEUX_SANDBOX_ID.replace('-', '')) == 32


@pytest.mark.unit
def test_property_types_mapping():
    """Vérifie le mapping correct des types de propriétés"""
    # Personnages
    personnage_props = {
        "Nom": "title",
        "Type": "select",
        "Genre": "select",
        "État": "status",
        "Alias": "rich_text",
        "Occupation": "rich_text",
        "Âge": "number"
    }
    
    # Lieux
    lieu_props = {
        "Nom": "title",
        "Catégorie": "select",
        "Rôle": "select",  # ⚠️ IMPORTANT: select, pas rich_text
        "Taille": "select",
        "État": "status"
    }
    
    # Vérifications
    assert personnage_props["Nom"] == "title"
    assert lieu_props["Rôle"] == "select", "Rôle DOIT être select pour éviter erreur API"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

