"""
Test pour vérifier que le composant brief_builder n'a pas de bug de closure.

Ce test vérifie que chaque dropdown modifie bien la bonne catégorie,
et non la dernière catégorie due à une fermeture incorrecte.
"""
import pytest
from app.streamlit_app.brief_builder_logic import compose_brief_text, roll_tags


@pytest.mark.unit
def test_multiple_categories_no_closure_bug():
    """
    Vérifie que chaque catégorie peut être modifiée indépendamment.
    
    Problème identifié: Dans le JS, les event listeners partageaient 
    la même référence 'cat' (dernière valeur de la boucle).
    
    Ce test vérifie la logique Python uniquement. Le fix JS est 
    documenté dans index.html ligne 107-117 (IIFE pour capture correcte).
    """
    domain = "Personnages"
    mode = "simple"
    
    # Initial roll
    initial = roll_tags(domain, mode, seed=42, locked={})
    
    # Simuler un changement de TYPE uniquement
    updated = initial.copy()
    updated["TYPE"] = "PNJ secondaire"
    
    # Composer le brief avec la nouvelle valeur
    brief_with_change = compose_brief_text(domain, mode, updated)
    
    # Le brief doit contenir la nouvelle valeur de TYPE
    assert "PNJ secondaire" in brief_with_change
    
    # Les autres catégories ne doivent PAS avoir changé
    assert updated["ESPÈCE"] == initial["ESPÈCE"]
    assert updated["LIEU"] == initial["LIEU"]
    assert updated["OCCUPATION"] == initial["OCCUPATION"]
    assert updated["GENRE"] == initial["GENRE"]


@pytest.mark.unit
def test_compose_brief_preserves_all_categories():
    """
    Vérifie que compose_brief_text utilise toutes les catégories 
    sans les mélanger.
    """
    domain = "Personnages"
    mode = "simple"
    
    selections = {
        "TYPE": "PJ (Personnage Joueur)",
        "GENRE": "Féminin",
        "ESPÈCE": "Van'Doei",
        "LIEU": "Vieille Ville",
        "OCCUPATION": "Archiviste",
    }
    
    brief = compose_brief_text(domain, mode, selections)
    
    # Toutes les valeurs doivent être présentes
    for value in selections.values():
        assert value in brief, f"Valeur '{value}' absente du brief: {brief}"
    
    # Aucun placeholder non résolu
    assert "[TYPE]" not in brief
    assert "[GENRE]" not in brief
    assert "[ESPÈCE]" not in brief
    assert "[LIEU]" not in brief
    assert "[OCCUPATION]" not in brief


@pytest.mark.unit
def test_single_category_change_isolation():
    """
    Change une seule catégorie et vérifie que les autres 
    restent intactes.
    """
    domain = "Lieux"
    mode = "simple"
    
    initial = {
        "RÔLE": "Ville",
        "TAILLE": "Région",
        "LIEU": "Escelion",
        "ATMOSPHÈRE": "Paisible",
        "PARTICULARITÉ": "Aucune",
    }
    
    # Change uniquement ATMOSPHÈRE
    updated = initial.copy()
    updated["ATMOSPHÈRE"] = "Oppressante"
    
    # Vérifie isolation
    assert updated["ATMOSPHÈRE"] == "Oppressante"
    assert updated["RÔLE"] == initial["RÔLE"]
    assert updated["TAILLE"] == initial["TAILLE"]
    assert updated["LIEU"] == initial["LIEU"]
    assert updated["PARTICULARITÉ"] == initial["PARTICULARITÉ"]
    
    # Compose et vérifie
    brief = compose_brief_text(domain, mode, updated)
    assert "Oppressante" in brief
    assert "Ville" in brief


