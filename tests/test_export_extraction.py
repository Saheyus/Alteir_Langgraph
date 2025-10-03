"""
Tests unitaires pour l'extraction de champs depuis le markdown
"""

import pytest
import re


def extract_field(field_name: str, content: str) -> str:
    """
    Extrait un champ du contenu markdown (formats variés)
    
    Copie de la fonction dans app_streamlit.py pour tests isolés
    """
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


# ============================================================================
# FIXTURES - Données de test
# ============================================================================

@pytest.fixture
def sample_personnage_content():
    """Contenu markdown d'un personnage type"""
    return """
# Drarus Lumenflex

## Métadonnées

- **Nom**: Drarus Lumenflex
- **Type**: PNJ
- **Genre**: Masculin
- **Alias**: Le Tisseur d'Ombres
- **Occupation**: Archiviste clandestin
- **Âge**: 42 ans
- **Espèce**: Humain modifié
- **Axe idéologique**: Subversion
- **Archétype littéraire**: Mentor / Gourou, Magicien / Sorcier
- **Qualités**: Lucide, Ingénieuse, Diplomate
- **Défauts**: Cynique, Méfiante, Obstinée
- **Communautés**: Les Murmurateurs, Réseau Abyssal
- **Lieux de vie**: Le Léviathan Pétrifié, La Vieille Ville
- **Réponse au problème moral**: La résistance ne peut exister que dans les interstices du système, là où le contrôle s'effrite.

## Contenu narratif

Drarus incarne la figure du mentor désabusé...
"""

@pytest.fixture
def sample_lieu_content():
    """Contenu markdown d'un lieu type"""
    return """
# Marché des Placides Respirants

## CHAMPS NOTION (métadonnées)

- Nom: Marché des Placides Respirants
- Catégorie: Lieu
- Taille: Site
- Rôle: Lieu commercial
- Sprint: Sprint 1
- Zones limitrophes: Strate I - La Périphérie Caudale, Bassin Médullaire
- Communautés présentes: Les Murmurateurs
- Personnages présents: Drarus Lumenflex

## CONTENU NARRATIF

Le Marché des Placides Respirants est un hub commercial...
"""


# ============================================================================
# TESTS - Extraction basique
# ============================================================================

class TestExtractionBasique:
    """Tests d'extraction de champs simples"""
    
    def test_extract_nom_personnage(self, sample_personnage_content):
        nom = extract_field("Nom", sample_personnage_content)
        assert nom == "Drarus Lumenflex"
    
    def test_extract_type(self, sample_personnage_content):
        type_val = extract_field("Type", sample_personnage_content)
        assert type_val == "PNJ"
    
    def test_extract_genre(self, sample_personnage_content):
        genre = extract_field("Genre", sample_personnage_content)
        assert genre == "Masculin"
    
    def test_extract_alias(self, sample_personnage_content):
        alias = extract_field("Alias", sample_personnage_content)
        assert alias == "Le Tisseur d'Ombres"
    
    def test_extract_age(self, sample_personnage_content):
        age = extract_field("Âge", sample_personnage_content)
        assert age == "42 ans"
    
    def test_extract_field_missing(self, sample_personnage_content):
        missing = extract_field("ChampInexistant", sample_personnage_content)
        assert missing is None


# ============================================================================
# TESTS - Champs critiques pour relations
# ============================================================================

class TestExtractionRelations:
    """Tests d'extraction des champs de relations"""
    
    def test_extract_espece(self, sample_personnage_content):
        espece = extract_field("Espèce", sample_personnage_content)
        assert espece == "Humain modifié"
    
    def test_extract_communautes(self, sample_personnage_content):
        comms = extract_field("Communautés", sample_personnage_content)
        assert comms == "Les Murmurateurs, Réseau Abyssal"
    
    def test_extract_lieux_de_vie(self, sample_personnage_content):
        lieux = extract_field("Lieux de vie", sample_personnage_content)
        assert lieux == "Le Léviathan Pétrifié, La Vieille Ville"


# ============================================================================
# TESTS - Champs multi-valeurs
# ============================================================================

class TestExtractionMultiValeurs:
    """Tests d'extraction des champs multi-select"""
    
    def test_extract_axe_ideologique(self, sample_personnage_content):
        axe = extract_field("Axe idéologique", sample_personnage_content)
        assert axe == "Subversion"
    
    def test_extract_archetype(self, sample_personnage_content):
        archetype = extract_field("Archétype littéraire", sample_personnage_content)
        assert archetype == "Mentor / Gourou, Magicien / Sorcier"
    
    def test_extract_qualites(self, sample_personnage_content):
        qualites = extract_field("Qualités", sample_personnage_content)
        assert qualites == "Lucide, Ingénieuse, Diplomate"
    
    def test_extract_defauts(self, sample_personnage_content):
        defauts = extract_field("Défauts", sample_personnage_content)
        assert defauts == "Cynique, Méfiante, Obstinée"


# ============================================================================
# TESTS - Rich text long
# ============================================================================

class TestExtractionRichText:
    """Tests d'extraction de champs rich text longs"""
    
    def test_extract_reponse_morale(self, sample_personnage_content):
        reponse = extract_field("Réponse au problème moral", sample_personnage_content)
        assert "La résistance ne peut exister" in reponse
        assert len(reponse) > 0


# ============================================================================
# TESTS - Lieux (format différent)
# ============================================================================

class TestExtractionLieux:
    """Tests d'extraction spécifiques aux lieux"""
    
    def test_extract_nom_lieu(self, sample_lieu_content):
        nom = extract_field("Nom", sample_lieu_content)
        assert nom == "Marché des Placides Respirants"
    
    def test_extract_categorie(self, sample_lieu_content):
        cat = extract_field("Catégorie", sample_lieu_content)
        assert cat == "Lieu"
    
    def test_extract_taille(self, sample_lieu_content):
        taille = extract_field("Taille", sample_lieu_content)
        assert taille == "Site"
    
    def test_extract_role(self, sample_lieu_content):
        role = extract_field("Rôle", sample_lieu_content)
        assert role == "Lieu commercial"
    
    def test_extract_zones_limitrophes(self, sample_lieu_content):
        zones = extract_field("Zones limitrophes", sample_lieu_content)
        assert "Strate I" in zones
        assert "Bassin Médullaire" in zones


# ============================================================================
# TESTS - Parsing multi-valeurs
# ============================================================================

class TestParsingSplit:
    """Tests du parsing des valeurs multiples"""
    
    def test_split_communautes(self, sample_personnage_content):
        comms_raw = extract_field("Communautés", sample_personnage_content)
        comms = [c.strip() for c in re.split(r'[,;]\s*', comms_raw)]
        assert len(comms) == 2
        assert "Les Murmurateurs" in comms
        assert "Réseau Abyssal" in comms
    
    def test_split_qualites(self, sample_personnage_content):
        qual_raw = extract_field("Qualités", sample_personnage_content)
        qualites = [q.strip() for q in re.split(r'[,;]\s*', qual_raw)]
        assert len(qualites) == 3
        assert "Lucide" in qualites
        assert "Ingénieuse" in qualites
        assert "Diplomate" in qualites
    
    def test_split_archetype(self, sample_personnage_content):
        arch_raw = extract_field("Archétype littéraire", sample_personnage_content)
        archetypes = [a.strip() for a in re.split(r'[,;]\s*', arch_raw)]
        assert len(archetypes) == 2
        assert "Mentor / Gourou" in archetypes
        assert "Magicien / Sorcier" in archetypes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

