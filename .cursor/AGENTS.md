# Instructions Cursor - Meta

## Format Rules
- **Fichiers `.mdc`** : Format MDC avec frontmatter YAML
- **Fichiers `AGENTS.md`** : Markdown simple, sans métadonnées
- **Max 500 lignes** par rule (bonnes pratiques Cursor)

## Types de Rules (MDC)
```yaml
---
description: "Description pour l'IA"
globs: ["**/*.py"]  # Auto-attach si fichiers matchent
alwaysApply: true   # Toujours inclure
---
```

Types :
- **Always** : Toujours dans contexte
- **Auto Attached** : Si fichiers matchent globs
- **Agent Requested** : L'IA décide (description requise)
- **Manual** : Seulement si `@ruleName`

## Rules Disponibles
- `meta-rules.mdc` : Comment créer des rules
- `export-notion.mdc` : Export Notion (sandbox vs principal)
- `tests-export.mdc` : Tests d'export
- `tests.mdc` : Organisation tests généraux
- `debug-practices.mdc` : Pas de fichiers temporaires
- `multi-agents.mdc` : Architecture agents
- `narrative-design.mdc` : Principes narratifs
- `notion-mcp.mdc` : Outils MCP Notion

## Où Documenter
- **Pour l'IA** → `.cursor/rules/*.mdc`

## Création Rule
1. Identifier besoin (règle critique répétée)
2. Créer `.cursor/rules/nom-descriptif.mdc`
3. Ajouter frontmatter YAML
4. Supprimer vieux guides mal placés
5. Commit : `git commit -m "rules: ..."`

## Principe
**L'IA n'a pas de mémoire. Les AGENTS.md et rules sont sa mémoire externe.**

