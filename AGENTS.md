# Instructions Projet - Système Multi-Agents GDD Alteir

## Contexte
Système multi-agents local pour génération de contenu narratif (personnages, lieux).
Stack : LangGraph + MCP Notion + OpenAI GPT-5/GPT-4.

## Règles Critiques

### Export Notion
**TOUJOURS utiliser le bac à sable, JAMAIS les bases principales.**
- Personnages (1) : `2806e4d21b458012a744d8d6723c8be1`
- Lieux (1) : `2806e4d21b4580969f1cd7463a4c889c`

### Tests
- Fichiers de test **TOUJOURS dans `tests/`**, JAMAIS à la racine
- Pas de fichiers temporaires, utiliser `python -c "..."` ou `if __name__ == "__main__"`
- Tests rapides : `python tests/run_export_tests.py quick`

### LLM
- GPT-5 : `use_responses_api=True`, `reasoning={"effort": "minimal"}`, **PAS de `temperature`**
- GPT-4 : `temperature=1.0`, pas de `reasoning`

### Guides et Documentation
- Guides pour l'IA → `.cursor/rules/*.mdc` (format MDC avec frontmatter)
- Guides pour utilisateur → Racine en `.md` (ex: `GUIDE_UTILISATEUR.md`)
- Doc technique tests → `tests/README_*.md` (OK dans dossier tests)
- **TOUJOURS créer `AGENTS.md` dans répertoires importants**

## Architecture
- `agents/` : Agents génériques (Writer, Reviewer, Corrector, Validator)
- `config/domain_configs/` : Configs par domaine (personnages, lieux)
- `workflows/` : Workflows LangGraph
- `app_streamlit.py` : Interface utilisateur principale
- `tests/` : Tests modulaires (extraction, payload, intégration)

## Références
- Rules détaillées : `.cursor/rules/`
- Guide utilisateur : `GUIDE_UTILISATEUR.md`
- Tests export : `tests/README_EXPORT_TESTS.md`

