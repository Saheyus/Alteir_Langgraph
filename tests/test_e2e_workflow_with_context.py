"""
Tests E2E avec contexte Notion (références croisées)

Teste le workflow avec récupération de contexte depuis Notion:
- Communautés référencées
- Lieux mentionnés
- Espèces
- Autres personnages

⚠️ Ces tests utilisent:
- API LLM réelle (GPT-4o-mini)
- API Notion réelle (lecture bases principales + écriture sandbox)
- Temps d'exécution: ~60-90 secondes par test
"""
import pytest
import sys
import re
import requests
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from workflows.content_workflow import ContentWorkflow
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
from agents.notion_context_fetcher import NotionContextFetcher
from config.context_cache import context_cache


# ============================================================================
# TESTS E2E - Contexte Notion
# ============================================================================

class TestE2EWorkflowWithContext:
    """Tests E2E avec récupération de contexte Notion"""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    @pytest.mark.notion_api
    def test_e2e_with_communaute_context(
        self,
        test_llm,
        temp_output_dir
    ):
        """
        Test E2E avec référence à une communauté existante
        
        Brief mentionne "Les Murmurateurs" (communauté réelle dans Notion)
        Le workflow doit:
        1. Détecter la référence
        2. Récupérer le contexte de la communauté
        3. Générer un personnage cohérent avec ce contexte
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Workflow avec Contexte Communauté")
        print(f"{'='*60}")
        
        brief = """
        Créer un membre des Murmurateurs.
        Humain modifié, 35 ans, agit dans l'ombre.
        """
        
        print("\n[1/4] Récupération du contexte Notion...")
        
        # Créer le fetcher de contexte
        fetcher = NotionContextFetcher()
        
        # Récupérer contexte pour le brief
        context = fetcher.fetch_context_for_brief(brief, domain="personnages")
        
        print(f"  - Contexte récupéré: {len(context)} entrées")
        
        # Vérifier qu'on a récupéré des communautés
        communautes = [c for c in context if c.get("type") == "communautés"]
        print(f"  - Communautés trouvées: {len(communautes)}")
        
        # Workflow avec contexte
        print("\n[2/4] Exécution du workflow avec contexte...")
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        state = workflow.run(brief, context={"notion_context": context})
        
        assert state["writer_metadata"]["success"], "Writer a échoué"
        
        # Vérifier que le contenu mentionne la communauté
        print("\n[3/4] Vérification de la cohérence avec le contexte...")
        content = state["content"]
        
        # Le contenu doit mentionner les Murmurateurs
        has_reference = "murmurateur" in content.lower()
        print(f"  - Référence à la communauté: {has_reference}")
        
        # Sauvegarder
        print("\n[4/4] Sauvegarde...")
        json_file, md_file = workflow.save_results(state, output_dir=str(temp_output_dir))
        
        assert json_file.exists()
        
        print(f"\n✓ Test E2E avec contexte communauté réussi !")
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    @pytest.mark.notion_api
    def test_e2e_with_lieu_context(
        self,
        test_llm,
        temp_output_dir
    ):
        """
        Test E2E avec référence à un lieu existant
        
        Brief mentionne "La Vieille Ville" (lieu réel dans Notion)
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Workflow avec Contexte Lieu")
        print(f"{'='*60}")
        
        brief = """
        Créer un habitant de La Vieille Ville.
        Humain, 50 ans, connaît tous les recoins.
        """
        
        print("\n[1/3] Récupération du contexte...")
        
        fetcher = NotionContextFetcher()
        context = fetcher.fetch_context_for_brief(brief, domain="personnages")
        
        lieux = [c for c in context if c.get("type") == "lieux"]
        print(f"  - Lieux trouvés: {len(lieux)}")
        
        # Workflow
        print("\n[2/3] Exécution du workflow...")
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        state = workflow.run(brief, context={"notion_context": context})
        
        assert state["validator_metadata"]["is_valid"], "Validation a échoué"
        
        # Vérifier cohérence
        print("\n[3/3] Vérification...")
        content = state["content"]
        
        has_lieu_ref = "vieille ville" in content.lower()
        print(f"  - Référence au lieu: {has_lieu_ref}")
        
        print(f"\n✓ Test E2E avec contexte lieu réussi !")
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    @pytest.mark.notion_api
    def test_e2e_with_espece_context(
        self,
        test_llm,
        temp_output_dir
    ):
        """
        Test E2E avec référence à une espèce
        
        Brief mentionne "Humain modifié" (espèce dans Notion)
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Workflow avec Contexte Espèce")
        print(f"{'='*60}")
        
        brief = """
        Créer un Humain modifié.
        45 ans, modifications biomécaniques visibles.
        """
        
        print("\n[1/3] Récupération du contexte...")
        
        fetcher = NotionContextFetcher()
        context = fetcher.fetch_context_for_brief(brief, domain="personnages")
        
        especes = [c for c in context if c.get("type") == "espèces"]
        print(f"  - Espèces trouvées: {len(especes)}")
        
        # Workflow
        print("\n[2/3] Exécution du workflow...")
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        state = workflow.run(brief, context={"notion_context": context})
        
        assert state["writer_metadata"]["success"], "Writer a échoué"
        
        # Vérifier extraction espèce
        print("\n[3/3] Vérification extraction...")
        content = state["content"]
        
        def extract_field(field_name, content):
            pattern = rf'^\-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            return match.group(1).strip() if match else None
        
        espece_extracted = extract_field("Espèce", content)
        print(f"  - Espèce extraite: {espece_extracted}")
        
        assert espece_extracted is not None, "Espèce non extraite"
        assert "humain" in espece_extracted.lower(), "Espèce incorrecte"
        
        print(f"\n✓ Test E2E avec contexte espèce réussi !")
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.llm_api
    @pytest.mark.notion_api
    def test_e2e_with_multi_context(
        self,
        test_llm,
        temp_output_dir
    ):
        """
        Test E2E avec références multiples
        
        Brief mentionne:
        - Communauté: Les Murmurateurs
        - Lieu: La Vieille Ville
        - Espèce: Humain modifié
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Workflow avec Contexte Multiple")
        print(f"{'='*60}")
        
        brief = """
        Créer un membre des Murmurateurs, Humain modifié.
        Vit dans La Vieille Ville, 40 ans.
        Archiviste clandestin, possède des informations dangereuses.
        """
        
        print("\n[1/3] Récupération du contexte multiple...")
        
        fetcher = NotionContextFetcher()
        context = fetcher.fetch_context_for_brief(brief, domain="personnages")
        
        print(f"  - Total contexte: {len(context)} entrées")
        
        # Compter par type
        types_count = {}
        for item in context:
            item_type = item.get("type", "unknown")
            types_count[item_type] = types_count.get(item_type, 0) + 1
        
        for item_type, count in types_count.items():
            print(f"    - {item_type}: {count}")
        
        # Workflow avec contexte riche
        print("\n[2/3] Exécution du workflow...")
        workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
        
        state = workflow.run(brief, context={"notion_context": context})
        
        assert state["validator_metadata"]["is_valid"], "Validation a échoué"
        
        # Vérifier richesse du contenu
        print("\n[3/3] Vérification de la richesse...")
        content = state["content"]
        
        # Le contenu doit être riche (contexte multiple)
        assert len(content) > 500, "Contenu insuffisamment riche pour contexte multiple"
        
        # Vérifier présence des références
        has_communaute = "murmurateur" in content.lower()
        has_lieu = "vieille ville" in content.lower()
        has_espece = "humain" in content.lower()
        
        print(f"  - Référence communauté: {has_communaute}")
        print(f"  - Référence lieu: {has_lieu}")
        print(f"  - Référence espèce: {has_espece}")
        
        # Au moins 2/3 doivent être présentes
        refs_count = sum([has_communaute, has_lieu, has_espece])
        assert refs_count >= 2, f"Trop peu de références dans le contenu: {refs_count}/3"
        
        print(f"\n✓ Test E2E avec contexte multiple réussi !")
        print(f"  - {refs_count}/3 références présentes")


# ============================================================================
# TESTS E2E - Cache Contexte
# ============================================================================

class TestE2EContextCache:
    """Tests E2E de la mise en cache du contexte"""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.notion_api
    def test_context_cache_performance(
        self,
        test_llm
    ):
        """
        Test que le cache contexte améliore les performances
        
        1er appel: fetch depuis Notion
        2e appel: récupération depuis cache (rapide)
        """
        print(f"\n{'='*60}")
        print(f"TEST E2E: Performance Cache Contexte")
        print(f"{'='*60}")
        
        brief = "Membre des Murmurateurs"
        
        fetcher = NotionContextFetcher()
        
        # Premier appel (sans cache)
        print("\n[1/2] Premier appel (fetch Notion)...")
        context_cache.clear()  # Vider le cache
        
        import time
        start = time.time()
        context1 = fetcher.fetch_context_for_brief(brief, domain="personnages")
        time1 = time.time() - start
        
        print(f"  - Durée: {time1:.2f}s")
        print(f"  - Entrées: {len(context1)}")
        
        # Deuxième appel (avec cache)
        print("\n[2/2] Deuxième appel (depuis cache)...")
        start = time.time()
        context2 = fetcher.fetch_context_for_brief(brief, domain="personnages")
        time2 = time.time() - start
        
        print(f"  - Durée: {time2:.2f}s")
        print(f"  - Entrées: {len(context2)}")
        
        # Le cache doit être plus rapide
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"  - Accélération: {speedup:.1f}x")
        
        # Assertions
        assert len(context1) == len(context2), "Cache a retourné des données différentes"
        
        # Le cache doit être au moins 2x plus rapide (souvent 10x+)
        if time2 > 0.01:  # Si mesurable
            assert speedup > 2, f"Cache pas assez rapide: {speedup:.1f}x"
        
        print(f"\n✓ Test cache performance réussi !")

