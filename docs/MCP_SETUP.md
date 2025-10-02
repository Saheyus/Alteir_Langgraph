# Configuration MCP Notion - Guide Complet (API 2025-09-03)

## 🎯 Objectif
Configurer l'accès sécurisé à Notion pour le système multi-agents, avec lecture globale et écriture restreinte, en utilisant la nouvelle API Notion 2025-09-03 avec support des bases de données multisources.

## 📋 Étapes de Configuration

### 1. Créer l'Intégration Notion

1. **Aller sur** : [developers.notion.com](https://developers.notion.com)
2. **Se connecter** avec votre compte Notion
3. **Créer une nouvelle intégration** :
   - Cliquer sur "New integration"
   - **Nom** : `GDD Multi-Agents Alteir`
   - **Description** : `Système multi-agents pour écriture/relecture du Game Design Document`
   - **Logo** : Optionnel (peut être ajouté plus tard)
   - **⚠️ IMPORTANT** : Utiliser la version API `2025-09-03` pour le support des bases multisources

### 2. Configurer les Permissions

Dans les paramètres de l'intégration :

#### **Capacités (Capabilities)**
```
✅ Read content
✅ Update content  
✅ Insert content
✅ Read user information
```

#### **Bases de Données (Databases)**
Ajouter chaque base avec les permissions appropriées :

| Base | ID | Permission | Usage |
|------|----|-----------|--------|
| Lieux | `1886e4d21b4581eda022ea4e0f1aba5f` | **Read** | Lecture des lieux existants |
| Personnages | `1886e4d21b4581a29340f77f5f2e5885` | **Read** | Lecture des personnages |
| Communautés | `1886e4d21b4581dea4f4d01beb5e1be2` | **Read** | Lecture des organisations |
| Espèces | `1886e4d21b4581e9a768df06185c1aea` | **Read** | Lecture des races |
| Objets | `1886e4d21b4581098024c61acd801f52` | **Read** | Lecture des objets |
| Chronologie | `22c6e4d21b458066b17cc2af998de0b8` | **Read** | Lecture des événements |

### 3. Gérer les Bases Multisources (API 2025-09-03)

**Nouveauté** : Les bases de données peuvent maintenant avoir plusieurs sources de données.

1. **Identifier les sources** : Chaque base peut avoir plusieurs sources
2. **Récupérer les data_source_url** : Utiliser `mcp_notionMCP_notion-fetch` pour obtenir les sources
3. **Configurer les permissions** : Par source de données si nécessaire

### 4. Créer une Base de Test

**Important** : Créer une base dédiée pour les tests d'écriture.

1. **Dans Notion** : Créer une nouvelle base
2. **Nom** : `GDD - Tests Multi-Agents`
3. **Structure** : Copier la structure d'une base existante (ex: Personnages)
4. **Permissions** : Donner "Full access" à l'intégration
5. **Noter l'ID** : Copier l'ID de la base (visible dans l'URL)
6. **Récupérer les sources** : Noter les `data_source_url` pour la configuration

### 5. Récupérer le Token

1. **Dans l'intégration** : Aller dans "Secrets"
2. **Copier le token** : `secret_...`
3. **⚠️ Important** : Garder ce token secret !

### 6. Configuration Locale

1. **Copier le fichier d'exemple** :
   ```bash
   cp env.example .env
   ```

2. **Éditer `.env`** :
   ```bash
   NOTION_TOKEN=secret_votre_token_ici
   OPENAI_API_KEY=votre_cle_openai
   ```

3. **Mettre à jour la config** :
   - Éditer `config/notion_config.py`
   - Remplacer l'ID de la base "tests" par l'ID réel
   - Ajouter les `data_source_url` pour les bases multisources

## 🔒 Sécurité

### Bonnes Pratiques
- ✅ **Jamais** commiter le fichier `.env`
- ✅ **Rotation** régulière des tokens
- ✅ **Permissions minimales** nécessaires
- ✅ **Base de test** séparée pour l'écriture

### Vérification
```python
from config.notion_config import NotionConfig

# Vérifier la configuration
if NotionConfig.validate_token():
    print("✅ Token Notion configuré")
    print(NotionConfig.get_config_summary())
else:
    print("❌ Token Notion manquant")
```

## 🧪 Test de Connexion

### Script de Test
```python
# test_notion_connection.py
import os
from dotenv import load_dotenv
from config.notion_config import NotionConfig

load_dotenv()

def test_connection():
    if not NotionConfig.validate_token():
        print("❌ Token Notion manquant")
        return False
    
    # Test de lecture sur une base
    # (À implémenter avec les outils MCP)
    print("✅ Configuration Notion OK")
    return True

if __name__ == "__main__":
    test_connection()
```

## 🚀 Prochaines Étapes

1. **Configurer l'intégration** Notion (étapes 1-4)
2. **Tester la connexion** avec le script de test
3. **Créer les agents** avec accès MCP
4. **Implémenter les workflows** de lecture/écriture

## 📞 Support

En cas de problème :
1. Vérifier les permissions de l'intégration
2. Vérifier que les bases sont bien partagées avec l'intégration
3. Tester avec une base simple d'abord
4. Consulter les logs d'erreur MCP

---

*Guide créé le : Janvier 2025*
*Version : 1.0*
