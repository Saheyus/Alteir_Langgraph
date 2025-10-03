# Instructions Configuration

## Structure
- `notion_config.py` : IDs bases Notion, version API
- `domain_configs/` : Configs par domaine (personnages, lieux)

## Domain Config Pattern
Chaque domaine a sa config complète :
```python
from agents.base.domain_config import DomainConfig

PERSONNAGES_CONFIG = DomainConfig(
    domain_name="personnages",
    notion_database_id="...",
    narrative_template="...",
    validation_rules={...},
    specific_params={...}
)
```

## Notion Config
**API Version** : `2025-09-03` (support multi-source databases)

**Bases Sandbox (ÉCRITURE)** :
- Personnages (1) : `2806e4d21b458012a744d8d6723c8be1`
- Lieux (1) : `2806e4d21b4580969f1cd7463a4c889c`

**Bases Principales (LECTURE)** :
- Personnages : `1886e4d21b4581a29340f77f5f2e5885`
- Lieux : `1886e4d21b4581eda022ea4e0f1aba5f`
- Communautés : `1886e4d21b4581dea4f4d01beb5e1be2`
- Espèces : `1886e4d21b4581e9a768df06185c1aea`
- Objets : `1886e4d21b4581098024c61acd801f52`

## Ajouter Nouveau Domaine
1. Créer `domain_configs/nouveau_config.py`
2. Définir `NOUVEAU_CONFIG = DomainConfig(...)`
3. Exporter dans `domain_configs/__init__.py`
4. Adapter UI dans `app_streamlit.py`

## Validation Rules
Définir par domaine :
```python
validation_rules = {
    "required_fields": ["Nom", "Type"],
    "min_length": 500,
    "max_length": 3000
}
```

