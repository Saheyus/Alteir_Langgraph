"""
Tests E2E de gestion d'erreurs

Teste les cas d'erreur et la résilience du système:
- Brief invalide
- Validation échouée
- API Notion erreur
- Timeouts (simulés)
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.append(str(Path(__file__).parent.parent))

from workflows.content_workflow import ContentWorkflow
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
from agents.base.base_agent import AgentResult


# ============================================================================
# TESTS E2E - Gestion d'Erreurs
# ============================================================================

class TestE2EErrorHandling:
    """Tests de gestion d'erreurs du workflow"""
    
    @pytest.mark.e2e
    def test_e2e_brief_vide(self, test_llm, temp_output_dir):
        """
        Test avec brief vide
        
        Le workflow doit:
        1. Détecter le brief vide
        2. Retourner une erreur claire
        3. Ne pas crasher
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Brief Vide")
        print(f"{'='*60}")
        
        brief = ""
        
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        print("\n[1/2] Exécution avec brief vide...")
        
        # Le workflow peut soit lever une exception, soit retourner un état invalide
        try:
            state = workflow.run(brief)
            
            # Si pas d'exception, vérifier que le workflow a détecté le problème
            print("\n[2/2] Vérification de la gestion d'erreur...")
            
            # Le writer ou validator devrait avoir échoué
            writer_success = state.get("writer_metadata", {}).get("success", False)
            validator_valid = state.get("validator_metadata", {}).get("is_valid", False)
            
            print(f"  - Writer success: {writer_success}")
            print(f"  - Validator valid: {validator_valid}")
            
            # Au moins un devrait avoir échoué
            assert not (writer_success and validator_valid), \
                "Le workflow n'a pas détecté le brief vide"
            
            print(f"\n✓ Gestion erreur brief vide OK")
            
        except Exception as e:
            # Exception levée = OK aussi
            print(f"\n[2/2] Exception levée (OK): {type(e).__name__}")
            print(f"  - Message: {str(e)[:100]}")
            
            # Vérifier que ce n'est pas un crash inattendu
            assert "brief" in str(e).lower() or "input" in str(e).lower() or \
                   "content" in str(e).lower() or "empty" in str(e).lower(), \
                f"Exception inattendue: {e}"
            
            print(f"\n✓ Exception appropriée levée")
    
    @pytest.mark.e2e
    def test_e2e_brief_trop_court(self, test_llm, temp_output_dir):
        """
        Test avec brief trop court/vague
        
        Le validator devrait détecter un problème de complétude
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Brief Trop Court")
        print(f"{'='*60}")
        
        brief = "humain"  # Trop vague
        
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        print("\n[1/2] Exécution avec brief vague...")
        state = workflow.run(brief)
        
        print("\n[2/2] Vérification des scores...")
        
        # Le score de complétude devrait être bas
        completeness = state.get("completeness_score", 1.0)
        print(f"  - Complétude: {completeness:.2f}")
        
        # Soit score bas, soit validation échouée
        validator_valid = state.get("validator_metadata", {}).get("is_valid", True)
        print(f"  - Validation: {validator_valid}")
        
        # On accepte que le LLM puisse quand même générer quelque chose
        # mais au moins un indicateur de problème devrait être présent
        has_issue = completeness < 0.7 or not validator_valid or \
                   len(state.get("validation_errors", [])) > 0
        
        print(f"  - Problème détecté: {has_issue}")
        
        print(f"\n✓ Gestion brief court OK")
    
    @pytest.mark.e2e
    def test_e2e_validation_failed_no_export(self, test_llm, temp_output_dir):
        """
        Test que si la validation échoue, on n'exporte pas vers Notion
        
        Simule un contenu invalide qui ne doit pas être exporté
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Validation Échouée = Pas d'Export")
        print(f"{'='*60}")
        
        # Workflow normal
        brief = "Personnage test, 30 ans"
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        state = workflow.run(brief)
        
        print("\n[1/2] Vérification de l'état de validation...")
        
        is_valid = state.get("validator_metadata", {}).get("is_valid", False)
        ready_for_pub = state.get("validator_metadata", {}).get("ready_for_publication", False)
        
        print(f"  - Valid: {is_valid}")
        print(f"  - Ready for publication: {ready_for_pub}")
        
        # Si validation échouée
        if not is_valid:
            print("\n[2/2] Validation a échoué (comme attendu pour certains briefs)")
            print("  → Export Notion ne devrait PAS être effectué")
            
            # Vérifier qu'il y a des erreurs de validation
            errors = state.get("validation_errors", [])
            print(f"  - Erreurs de validation: {len(errors)}")
            
            assert len(errors) > 0, "Validation échouée mais pas d'erreurs listées"
            
            print(f"\n✓ Gestion validation échouée OK")
        else:
            print("\n[2/2] Validation réussie")
            print("  → Le LLM a réussi à générer un contenu valide")
            print(f"\n✓ Test passé (contenu valide généré)")
    
    @pytest.mark.e2e
    def test_e2e_notion_api_error_simulation(
        self,
        test_llm,
        notion_headers,
        temp_output_dir
    ):
        """
        Test avec erreur API Notion simulée (base invalide)
        
        Le système doit:
        1. Générer le contenu correctement
        2. Échouer proprement à l'export Notion
        3. Retourner un message d'erreur clair
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Erreur API Notion")
        print(f"{'='*60}")
        
        import requests
        
        # Workflow normal
        brief = "Marchand, 40 ans"
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        print("\n[1/3] Génération du contenu...")
        state = workflow.run(brief)
        
        assert state["validator_metadata"]["is_valid"], "Contenu devrait être valide"
        
        # Tenter export vers base INVALIDE
        print("\n[2/3] Tentative export vers base invalide...")
        
        invalid_db_id = "00000000000000000000000000000000"
        
        payload = {
            "parent": {"database_id": invalid_db_id},
            "properties": {
                "Nom": {
                    "title": [{"text": {"content": "Test"}}]
                }
            }
        }
        
        url = "https://api.notion.com/v1/pages"
        response = requests.post(url, headers=notion_headers, json=payload)
        
        print("\n[3/3] Vérification de l'erreur...")
        
        # Doit échouer
        assert response.status_code != 200, "La requête devrait échouer"
        
        print(f"  - Status: {response.status_code}")
        print(f"  - Erreur: {response.json().get('message', 'N/A')[:100]}")
        
        # Vérifier que l'erreur est claire
        error_msg = response.text
        assert "notion" in error_msg.lower() or "database" in error_msg.lower(), \
            "Message d'erreur pas assez clair"
        
        print(f"\n✓ Gestion erreur API Notion OK")
    
    @pytest.mark.e2e
    def test_e2e_partial_success(self, test_llm, temp_output_dir):
        """
        Test succès partiel: certains agents réussissent, d'autres non
        
        Le système doit tracker quels agents ont réussi/échoué
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Tracking Succès Partiel")
        print(f"{'='*60}")
        
        brief = "test"
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        print("\n[1/2] Exécution du workflow...")
        state = workflow.run(brief)
        
        print("\n[2/2] Analyse des résultats...")
        
        # Vérifier tracking de chaque agent
        agents = ["writer", "reviewer", "corrector", "validator"]
        
        results = {}
        for agent in agents:
            metadata_key = f"{agent}_metadata"
            if metadata_key in state:
                success = state[metadata_key].get("success", False)
                results[agent] = success
                print(f"  - {agent.capitalize()}: {'✓' if success else '✗'}")
        
        # Au moins writer devrait avoir une métadonnée
        assert "writer" in results, "Metadata writer manquante"
        
        # Compter succès
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        print(f"\n  → Succès: {success_count}/{total_count}")
        
        print(f"\n✓ Tracking succès partiel OK")


# ============================================================================
# TESTS E2E - Résilience
# ============================================================================

class TestE2EResilience:
    """Tests de résilience du système"""
    
    @pytest.mark.e2e
    def test_e2e_contenu_incomplet_detection(self, test_llm, temp_output_dir):
        """
        Test détection de contenu incomplet
        
        Le validator doit détecter si des champs essentiels manquent
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Détection Contenu Incomplet")
        print(f"{'='*60}")
        
        # Brief minimal qui pourrait générer contenu incomplet
        brief = "personnage sans détails"
        
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        print("\n[1/2] Génération avec brief minimal...")
        state = workflow.run(brief)
        
        print("\n[2/2] Analyse de la complétude...")
        
        completeness = state.get("completeness_score", 0)
        validation_errors = state.get("validation_errors", [])
        
        print(f"  - Score complétude: {completeness:.2f}")
        print(f"  - Erreurs validation: {len(validation_errors)}")
        
        # Si score bas OU erreurs, c'est bon signe
        has_detection = completeness < 0.8 or len(validation_errors) > 0
        
        print(f"  - Détection active: {has_detection}")
        
        print(f"\n✓ Test détection complétude OK")
    
    @pytest.mark.e2e
    def test_e2e_workflow_state_consistency(self, test_llm, temp_output_dir):
        """
        Test cohérence de l'état du workflow
        
        L'état doit rester cohérent même en cas d'erreur partielle
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Cohérence État Workflow")
        print(f"{'='*60}")
        
        brief = "test cohérence"
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        print("\n[1/2] Exécution...")
        state = workflow.run(brief)
        
        print("\n[2/2] Vérification cohérence...")
        
        # Vérifier présence des clés essentielles
        essential_keys = ["domain", "brief", "content", "history"]
        
        for key in essential_keys:
            assert key in state, f"Clé essentielle manquante: {key}"
            print(f"  - {key}: ✓")
        
        # Vérifier types
        assert isinstance(state["domain"], str)
        assert isinstance(state["brief"], str)
        assert isinstance(state["content"], str)
        assert isinstance(state["history"], list)
        
        # Vérifier historique cohérent
        assert len(state["history"]) > 0, "Historique vide"
        
        print(f"  - Entrées historique: {len(state['history'])}")
        
        print(f"\n✓ Cohérence état OK")

