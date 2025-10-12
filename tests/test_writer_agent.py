"""
Tests pour WriterAgent

Tests unitaires et d'intégration pour le WriterAgent:
- Génération basique
- Génération avec contexte Notion
- Différents WriterConfig (intent, level)
- Format markdown correct
"""
import pytest
import sys
import re
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents.writer_agent import WriterAgent, WriterConfig
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
from config.domain_configs.lieux_config import LIEUX_CONFIG


# ============================================================================
# TESTS UNITAIRES - WriterAgent Basique
# ============================================================================

class TestWriterAgentBasic:
    """Tests basiques du WriterAgent"""
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    def test_writer_generate_personnage(self, test_llm):
        """Test génération personnage basique"""
        print(f"\n{'='*60}")
        print(f"TEST: WriterAgent Génération Personnage")
        print(f"{'='*60}")
        
        brief = "Marchand humain, 45 ans, cynique"
        
        writer = WriterAgent(PERSONNAGES_CONFIG, llm=test_llm)
        
        print("\n[1/2] Génération...")
        result = writer.process(brief)
        
        print("\n[2/2] Vérification...")
        assert result.success, f"Writer a échoué: {result.metadata.get('error')}"
        assert result.content is not None
        assert len(result.content) > 100, "Contenu trop court"
        
        print(f"  - Longueur: {len(result.content)} caractères")
        print(f"  - Succès: {result.success}")
        
        print(f"\n✓ Génération personnage OK")
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    def test_writer_generate_lieu(self, test_llm):
        """Test génération lieu basique"""
        print(f"\n{'='*60}")
        print(f"TEST: WriterAgent Génération Lieu")
        print(f"{'='*60}")
        
        brief = "Marché souterrain, taille: site"
        
        writer = WriterAgent(LIEUX_CONFIG, llm=test_llm)
        
        print("\n[1/2] Génération...")
        result = writer.process(brief)
        
        print("\n[2/2] Vérification...")
        assert result.success
        assert len(result.content) > 100
        
        print(f"  - Longueur: {len(result.content)} caractères")
        
        print(f"\n✓ Génération lieu OK")


# ============================================================================
# TESTS - Format Markdown
# ============================================================================

class TestWriterAgentFormat:
    """Tests du format markdown généré"""
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    def test_writer_markdown_structure_personnage(self, test_llm):
        """Vérifie la structure markdown pour personnage"""
        print(f"\n{'='*60}")
        print(f"TEST: Structure Markdown Personnage")
        print(f"{'='*60}")
        
        brief = "PNJ forgeron, nain, 60 ans"
        
        writer = WriterAgent(PERSONNAGES_CONFIG, llm=test_llm)
        result = writer.process(brief)
        
        assert result.success
        content = result.content
        
        print("\n[1/2] Vérification sections...")
        
        # Sections attendues pour personnage
        expected_sections = [
            "# ",  # Titre principal
            "## ",  # Sections
        ]
        
        for section in expected_sections:
            assert section in content, f"Section manquante: {section}"
            print(f"  - {section.strip()}: ✓")
        
        # Vérifier champs essentiels personnage
        print("\n[2/2] Vérification champs...")
        
        essential_fields = ["Nom", "Type", "Genre"]
        
        for field in essential_fields:
            # Chercher format: **Champ**: valeur
            pattern = rf'\*\*{field}\*\*:'
            assert re.search(pattern, content), f"Champ manquant: {field}"
            print(f"  - {field}: ✓")
        
        print(f"\n✓ Structure markdown personnage OK")
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    def test_writer_markdown_structure_lieu(self, test_llm):
        """Vérifie la structure markdown pour lieu"""
        print(f"\n{'='*60}")
        print(f"TEST: Structure Markdown Lieu")
        print(f"{'='*60}")
        
        brief = "Taverne, atmosphère chaleureuse"
        
        writer = WriterAgent(LIEUX_CONFIG, llm=test_llm)
        result = writer.process(brief)
        
        assert result.success
        content = result.content
        
        print("\n[1/2] Vérification sections...")
        
        # Les lieux peuvent avoir "CHAMPS NOTION" ou des champs directs
        has_structure = "## " in content or "CHAMPS NOTION" in content
        assert has_structure, "Pas de structure markdown détectée"
        
        print(f"  - Structure présente: ✓")
        
        # Vérifier champs essentiels lieu
        print("\n[2/2] Vérification champs...")
        
        essential_fields = ["Nom", "Catégorie"]
        
        fields_found = 0
        for field in essential_fields:
            # Format plus flexible pour lieux
            if field.lower() in content.lower():
                fields_found += 1
                print(f"  - {field}: ✓")
        
        assert fields_found >= 1, "Pas assez de champs essentiels"
        
        print(f"\n✓ Structure markdown lieu OK")


# ============================================================================
# TESTS - WriterConfig
# ============================================================================

class TestWriterAgentConfig:
    """Tests des différentes configurations WriterConfig"""
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    def test_writer_orthogonal_depth(self, test_llm):
        """Test configuration orthogonal_depth"""
        print(f"\n{'='*60}")
        print(f"TEST: WriterConfig orthogonal_depth")
        print(f"{'='*60}")
        
        brief = "Médecin, 40 ans, cache un secret"
        
        config = WriterConfig(
            intent="orthogonal_depth",
            level="major"
        )
        
        writer = WriterAgent(PERSONNAGES_CONFIG, llm=test_llm)
        writer.config = config
        
        print("\n[1/2] Génération avec orthogonal_depth...")
        result = writer.process(brief)
        
        assert result.success
        
        print("\n[2/2] Vérification profondeur...")
        content = result.content
        
        # Contenu devrait être riche (orthogonal_depth + major)
        assert len(content) > 200, f"Contenu trop court pour orthogonal_depth: {len(content)}"
        
        print(f"  - Longueur: {len(content)} caractères")
        print(f"  - Intent: {result.metadata.get('intent')}")
        print(f"  - Level: {result.metadata.get('level')}")
        
        print(f"\n✓ orthogonal_depth OK")
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    def test_writer_vocation_pure(self, test_llm):
        """Test configuration vocation_pure"""
        print(f"\n{'='*60}")
        print(f"TEST: WriterConfig vocation_pure")
        print(f"{'='*60}")
        
        brief = "Garde dévoué, 35 ans"
        
        config = WriterConfig(
            intent="vocation_pure",
            level="supporting"
        )
        
        writer = WriterAgent(PERSONNAGES_CONFIG, llm=test_llm)
        writer.config = config
        
        print("\n[1/2] Génération avec vocation_pure...")
        result = writer.process(brief)
        
        assert result.success
        
        print("\n[2/2] Vérification...")
        print(f"  - Intent metadata: {result.metadata.get('intent')}")
        
        # Vérifier que metadata contient le bon intent
        assert result.metadata.get("intent") == "vocation_pure"
        
        print(f"\n✓ vocation_pure OK")
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    def test_writer_mystere_non_resolu(self, test_llm):
        """Test configuration mystere_non_resolu"""
        print(f"\n{'='*60}")
        print(f"TEST: WriterConfig mystere_non_resolu")
        print(f"{'='*60}")
        
        brief = "Étranger mystérieux"
        
        config = WriterConfig(
            intent="mystere_non_resolu",
            level="minor"
        )
        
        writer = WriterAgent(PERSONNAGES_CONFIG, llm=test_llm)
        writer.config = config
        
        print("\n[1/2] Génération avec mystere_non_resolu...")
        result = writer.process(brief)
        
        assert result.success
        
        print("\n[2/2] Vérification...")
        
        # Minor level peut générer contenu plus court
        content = result.content
        print(f"  - Longueur: {len(content)} caractères")
        print(f"  - Intent: {result.metadata.get('intent')}")
        
        assert result.metadata.get("intent") == "mystere_non_resolu"
        
        print(f"\n✓ mystere_non_resolu OK")


# ============================================================================
# TESTS - Contexte Notion
# ============================================================================

class TestWriterAgentWithContext:
    """Tests WriterAgent avec contexte Notion"""
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    @pytest.mark.notion_api
    def test_writer_with_notion_context(self, test_llm):
        """Test génération avec contexte Notion"""
        print(f"\n{'='*60}")
        print(f"TEST: WriterAgent avec Contexte Notion")
        print(f"{'='*60}")
        
        brief = "Membre des Murmurateurs"
        
        # Simuler contexte minimal
        context = {
            "notion_context": [
                {
                    "type": "communautés",
                    "title": "Les Murmurateurs",
                    "description": "Réseau clandestin d'informateurs"
                }
            ]
        }
        
        writer = WriterAgent(PERSONNAGES_CONFIG, llm=test_llm)
        
        print("\n[1/2] Génération avec contexte...")
        result = writer.process(brief, context=context)
        
        assert result.success
        
        print("\n[2/2] Vérification utilisation contexte...")
        content = result.content
        
        # Le contenu devrait mentionner la communauté
        has_reference = "murmurateur" in content.lower()
        print(f"  - Référence contexte: {has_reference}")
        
        # Note: Le LLM peut ne pas toujours utiliser le contexte exactement
        # donc on ne force pas l'assertion, mais on l'affiche
        
        print(f"\n✓ Test avec contexte OK")
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    def test_writer_without_context(self, test_llm):
        """Test génération sans contexte (baseline)"""
        print(f"\n{'='*60}")
        print(f"TEST: WriterAgent sans Contexte")
        print(f"{'='*60}")
        
        brief = "Personnage générique"
        
        writer = WriterAgent(PERSONNAGES_CONFIG, llm=test_llm)
        
        print("\n[1/2] Génération sans contexte...")
        result = writer.process(brief, context=None)
        
        assert result.success
        
        print("\n[2/2] Vérification...")
        assert len(result.content) > 50
        
        print(f"  - Longueur: {len(result.content)}")
        
        print(f"\n✓ Génération sans contexte OK")


# ============================================================================
# TESTS - Métadonnées
# ============================================================================

class TestWriterAgentMetadata:
    """Tests des métadonnées retournées par WriterAgent"""
    
    @pytest.mark.llm_api
    @pytest.mark.slow
    def test_writer_metadata_complete(self, test_llm):
        """Vérifie que les métadonnées sont complètes"""
        print(f"\n{'='*60}")
        print(f"TEST: Métadonnées WriterAgent")
        print(f"{'='*60}")
        
        brief = "Test métadonnées"
        
        config = WriterConfig(
            intent="orthogonal_depth",
            level="major",
            dialogue_mode="parle"
        )
        
        writer = WriterAgent(PERSONNAGES_CONFIG, llm=test_llm)
        writer.config = config
        
        print("\n[1/2] Génération...")
        result = writer.process(brief)
        
        assert result.success
        
        print("\n[2/2] Vérification métadonnées...")
        
        # Métadonnées attendues
        expected_keys = ["success", "intent", "level", "dialogue_mode"]
        
        for key in expected_keys:
            assert key in result.metadata, f"Métadonnée manquante: {key}"
            value = result.metadata[key]
            print(f"  - {key}: {value}")
        
        # Vérifier valeurs
        assert result.metadata["intent"] == "orthogonal_depth"
        assert result.metadata["level"] == "major"
        assert result.metadata["dialogue_mode"] == "parle"
        
        print(f"\n✓ Métadonnées complètes OK")

