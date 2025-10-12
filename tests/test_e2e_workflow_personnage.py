"""
Tests End-to-End du workflow complet pour personnages

Teste le workflow complet:
Brief → Writer → Reviewer → Corrector → Validator → Export Notion

⚠️ Ces tests utilisent:
- API LLM réelle (GPT-4o-mini) → coût ~$0.005 par test
- API Notion réelle (sandbox) → crée et archive des pages
- Temps d'exécution: ~30-60 secondes par test
"""
import pytest
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from workflows.content_workflow import ContentWorkflow
from agents.writer_agent import WriterConfig
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
from config.domain_configs.lieux_config import LIEUX_CONFIG


# ============================================================================
# TESTS E2E - Personnage Basique
# ============================================================================

class TestE2EWorkflowPersonnageBasic:
    """Tests E2E basiques pour le workflow personnage"""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    def test_e2e_personnage_minimal(
        self,
        test_llm,
        temp_output_dir,
        sample_brief_personnage
    ):
        """
        Test E2E complet avec brief minimal
        
        Étapes:
        1. Brief → WriterAgent
        2. Content → ReviewerAgent
        3. Reviewed → CorrectorAgent
        4. Corrected → ValidatorAgent
        5. Sauvegarder outputs JSON + MD
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Workflow Personnage Minimal")
        print(f"{'='*60}")
        print(f"Brief: {sample_brief_personnage}")
        
        # Créer le workflow
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        # Exécuter le workflow
        print("\n[1/4] Exécution du workflow...")
        state = workflow.run(sample_brief_personnage)
        
        # Vérifier état final
        print("\n[2/4] Vérification de l'état...")
        assert state is not None
        assert "content" in state
        assert len(state["content"]) > 100, "Contenu généré trop court"
        
        # Vérifier succès des agents
        assert state.get("writer_metadata", {}).get("success") is True, "Writer a échoué"
        assert state.get("reviewer_metadata", {}).get("success") is True, "Reviewer a échoué"
        assert state.get("corrector_metadata", {}).get("success") is True, "Corrector a échoué"
        assert state.get("validator_metadata", {}).get("success") is True, "Validator a échoué"
        
        # Vérifier scores
        print("\n[3/4] Vérification des scores...")
        coherence = state.get("coherence_score", 0)
        completeness = state.get("completeness_score", 0)
        quality = state.get("quality_score", 0)
        
        print(f"  - Cohérence: {coherence:.2f}")
        print(f"  - Complétude: {completeness:.2f}")
        print(f"  - Qualité: {quality:.2f}")
        
        assert coherence > 0.5, f"Score de cohérence trop bas: {coherence}"
        assert completeness > 0.5, f"Score de complétude trop bas: {completeness}"
        assert quality > 0.5, f"Score de qualité trop bas: {quality}"
        
        # Sauvegarder résultats
        print("\n[4/4] Sauvegarde des résultats...")
        json_file, md_file = workflow.save_results(state, output_dir=str(temp_output_dir))
        
        assert json_file.exists(), "Fichier JSON non créé"
        assert md_file.exists(), "Fichier Markdown non créé"
        
        # Vérifier contenu JSON
        with open(json_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        
        assert "domain" in json_data
        assert "content" in json_data
        assert "scores" in json_data
        
        print(f"\n✓ Test E2E réussi !")
        print(f"  - JSON: {json_file.name}")
        print(f"  - Markdown: {md_file.name}")
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    @pytest.mark.notion_api
    def test_e2e_personnage_with_notion_export(
        self,
        test_llm,
        notion_headers,
        sandbox_databases,
        notion_page_tracker,
        temp_output_dir
    ):
        """
        Test E2E complet avec export Notion
        
        Étapes:
        1-4. Workflow complet
        5. Export vers Notion sandbox
        6. Vérifier page créée
        7. Cleanup automatique
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Workflow Personnage + Export Notion")
        print(f"{'='*60}")
        
        brief = "PNJ forgeron nain, 60 ans, bourru mais généreux"
        
        # Workflow complet
        print("\n[1/5] Exécution du workflow...")
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        state = workflow.run(brief)
        
        assert state["validator_metadata"]["is_valid"], "Validation a échoué"
        
        # Sauvegarder pour extraction
        print("\n[2/5] Sauvegarde des résultats...")
        json_file, md_file = workflow.save_results(state, output_dir=str(temp_output_dir))
        
        # Lire le markdown pour extraction
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extraire métadonnées (fonction simplifiée)
        print("\n[3/5] Extraction des métadonnées...")
        import re
        
        def extract_field(field_name, content):
            pattern = rf'^\-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            return match.group(1).strip() if match else None
        
        nom = extract_field("Nom", content) or "TEST_E2E_Personnage"
        type_perso = extract_field("Type", content) or "PNJ"
        genre = extract_field("Genre", content) or "Non défini"
        
        # Créer payload Notion
        print("\n[4/5] Export vers Notion...")
        db_id = sandbox_databases["personnages"]
        
        payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Nom": {
                    "title": [{"text": {"content": nom}}]
                },
                "Type": {
                    "select": {"name": type_perso}
                },
                "Genre": {
                    "select": {"name": genre}
                },
                "État": {
                    "status": {"name": "Brouillon IA"}
                }
            }
        }
        
        # Créer la page
        url = "https://api.notion.com/v1/pages"
        response = requests.post(url, headers=notion_headers, json=payload)
        
        assert response.status_code == 200, f"Échec création page: {response.text}"
        
        page_data = response.json()
        page_id = page_data["id"]
        
        # Ajouter au tracker pour cleanup
        notion_page_tracker.append(page_id)
        
        # Vérifier page créée
        print("\n[5/5] Vérification de la page créée...")
        get_url = f"https://api.notion.com/v1/pages/{page_id}"
        response = requests.get(get_url, headers=notion_headers)
        
        assert response.status_code == 200
        
        page = response.json()
        assert page["properties"]["Nom"]["title"][0]["text"]["content"] == nom
        
        print(f"\n✓ Test E2E + Export Notion réussi !")
        print(f"  - Page créée: {page_id}")
        print(f"  - URL: {page_data.get('url', 'N/A')}")
        print(f"  - Cleanup automatique activé")


# ============================================================================
# TESTS E2E - Lieu
# ============================================================================

class TestE2EWorkflowLieu:
    """Tests E2E pour le workflow lieu"""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    def test_e2e_lieu_minimal(
        self,
        test_llm,
        temp_output_dir,
        sample_brief_lieu
    ):
        """Test E2E complet pour un lieu"""
        print(f"\n{'='*60}")
        print(f"TEST E2E: Workflow Lieu Minimal")
        print(f"{'='*60}")
        print(f"Brief: {sample_brief_lieu}")
        
        # Créer le workflow pour lieux
        workflow = ContentWorkflow(LIEUX_CONFIG, llm=test_llm)
        
        # Exécuter
        print("\n[1/3] Exécution du workflow...")
        state = workflow.run(sample_brief_lieu)
        
        # Vérifier
        print("\n[2/3] Vérification...")
        assert state is not None
        assert len(state["content"]) > 100
        
        assert state["validator_metadata"]["is_valid"], "Validation lieu a échoué"
        
        # Sauvegarder
        print("\n[3/3] Sauvegarde...")
        json_file, md_file = workflow.save_results(state, output_dir=str(temp_output_dir))
        
        assert json_file.exists()
        assert md_file.exists()
        
        # Vérifier structure spécifique lieux
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Un lieu doit avoir ces sections
        assert "CHAMPS NOTION" in content or "Catégorie" in content, "Structure lieu invalide"
        
        print(f"\n✓ Test E2E Lieu réussi !")


# ============================================================================
# TESTS E2E - Writer Profiles
# ============================================================================

class TestE2EWriterProfiles:
    """Tests E2E avec différents profils WriterConfig"""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    def test_e2e_orthogonal_depth(
        self,
        test_llm,
        temp_output_dir
    ):
        """Test avec profil orthogonal_depth"""
        brief = "Médecin humain, 40 ans, cache un secret"
        
        writer_config = WriterConfig(
            intent="orthogonal_depth",
            level="major"
        )
        
        # Créer workflow avec config personnalisée
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        workflow.writer.config = writer_config
        
        state = workflow.run(brief)
        
        assert state["writer_metadata"]["success"]
        assert state["writer_metadata"]["intent"] == "orthogonal_depth"
        
        # Vérifier que le contenu a de la profondeur
        content = state["content"]
        assert len(content) > 200, "Contenu trop court pour orthogonal_depth"
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    def test_e2e_vocation_pure(
        self,
        test_llm,
        temp_output_dir
    ):
        """Test avec profil vocation_pure"""
        brief = "Garde de l'ordre humain, dévoué, 35 ans"
        
        writer_config = WriterConfig(
            intent="vocation_pure",
            level="supporting"
        )
        
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        workflow.writer.config = writer_config
        
        state = workflow.run(brief)
        
        assert state["writer_metadata"]["success"]
        assert state["writer_metadata"]["intent"] == "vocation_pure"
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    def test_e2e_mystere_non_resolu(
        self,
        test_llm,
        temp_output_dir
    ):
        """Test avec profil mystere_non_resolu"""
        brief = "Étranger mystérieux, parle peu"
        
        writer_config = WriterConfig(
            intent="mystere_non_resolu",
            level="minor"
        )
        
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        workflow.writer.config = writer_config
        
        state = workflow.run(brief)
        
        assert state["writer_metadata"]["success"]
        assert state["writer_metadata"]["intent"] == "mystere_non_resolu"
        
        # Le mystère doit laisser des zones d'ombre
        content = state["content"]
        # Vérifier présence de formulations évoquant le mystère
        mystery_indicators = ["mystère", "énigme", "inconnu", "ombre", "secret"]
        has_mystery = any(indicator in content.lower() for indicator in mystery_indicators)
        
        # Note: on ne force pas, mais c'est un bon indicateur
        print(f"  - Indicateurs de mystère présents: {has_mystery}")

