"""Result visualisation and export helpers."""

from __future__ import annotations

import os
import re
from pathlib import Path

import requests
import streamlit as st

from .cache import list_output_files, load_result_file
from config.notion_config import NotionConfig


def export_to_notion(result, container: st.delta_generator.DeltaGenerator | None = None):
    """Exporte le résultat vers Notion (BAC À SABLE) et affiche un feedback.

    Args:
        result: Dictionnaire de résultat à exporter.
        container: Optionnel, un conteneur Streamlit (st.empty(), st.container(), colonne) pour afficher le feedback à l'endroit du bouton. Si None, utilise st (position globale).
    Returns:
        dict: Informations d'export (success, page_url, page_id, domain, nom, dry_run, error)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    container = container or st
    logger.info("🚀 Début export vers Notion")
    logger.info(f"  - Domain: {result.get('domain', 'N/A')}")
    logger.info(f"  - DRY_RUN: {NotionConfig.DRY_RUN}")
    try:
        logger.info(f"  - Feedback container provided: {bool(container)}")
    except Exception:
        pass
    
    try:
        # Affiche un indicateur visuel immédiat dans la zone fournie
        status_area = (container or st).empty()
        try:
            status_area.info("📤 Export vers Notion en cours…")
        except Exception:
            pass

        with st.spinner("📤 Export vers Notion en cours..."):
            # If domain missing, try to recover from persisted state
            domain = (result.get("domain") or st.session_state.get("_last_generation_result", {}).get("domain") or "personnages").lower()
            logger.info(f"  - Domain normalisé: {domain}")
            content = result.get("content") or (st.session_state.get("_last_generation_result") or {}).get("content") or ""

            # Recovery path: reload last saved JSON if content is empty
            if (not isinstance(content, str)) or (not content.strip()):
                try:
                    import json as _json
                    from pathlib import Path as _Path
                    last_json_path = st.session_state.get("_last_saved_json")
                    if last_json_path:
                        p = _Path(last_json_path)
                        if p.exists():
                            data = _json.loads(p.read_text(encoding="utf-8"))
                            if isinstance(data, dict):
                                # Prefer file content/domain if present
                                file_content = data.get("content")
                                file_domain = data.get("domain")
                                if isinstance(file_content, str) and file_content.strip():
                                    content = file_content
                                if file_domain and not result.get("domain"):
                                    domain = (file_domain or domain or "personnages").lower()
                                # Merge into result for downstream use
                                try:
                                    merged = dict(data)
                                    merged.update({k: v for k, v in (result or {}).items() if v is not None})
                                    result = merged
                                except Exception:
                                    pass
                except Exception:
                    # Non bloquant
                    pass
            if not isinstance(content, str) or not content.strip():
                logger.warning("  - Contenu vide ou invalide; annulation export")
                (container or st).warning("⚠️ Contenu vide: export Notion annulé")
                try:
                    st.session_state._last_export_event = {
                        "success": False,
                        "error": "empty_content",
                        "source": "results",
                    }
                except Exception:
                    pass
                return {"success": False, "error": "empty_content"}

            if domain == "lieux":
                database_id = NotionConfig.get_sandbox_database_id("lieux")
                domain_label = "Lieu"
                nom_property = "Nom"
            elif domain == "especes":
                database_id = NotionConfig.get_sandbox_database_id("especes")
                domain_label = "Espèce"
                nom_property = "Nom"
            elif domain == "communautes":
                database_id = NotionConfig.get_sandbox_database_id("communautes")
                domain_label = "Communauté"
                nom_property = "Nom"
            else:
                database_id = NotionConfig.get_sandbox_database_id("personnages")
                domain_label = "Personnage"
                nom_property = "Nom"

            # Guardrails: sandbox only
            logger.info(f"  - Database ID: {database_id}")
            NotionConfig.assert_sandbox_database_id(database_id)
            logger.info("  ✓ Database sandbox validée")

            def extract_field(field_name: str, raw_content: str):
                pattern_bold = rf'^-?\s*\*\*{re.escape(field_name)}\*\*:\s*(.+)$'
                match = re.search(pattern_bold, raw_content, re.MULTILINE | re.IGNORECASE)
                if match:
                    return match.group(1).strip()

                pattern_plain = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
                match = re.search(pattern_plain, raw_content, re.MULTILINE | re.IGNORECASE)
                if match:
                    return match.group(1).strip()

                section_match = re.search(
                    r"CHAMPS NOTION.*?\n(.*?)(?:\n\n|CONTENU NARRATIF|\Z)",
                    raw_content,
                    re.DOTALL | re.IGNORECASE,
                )
                if section_match:
                    section_content = section_match.group(1)
                    pattern_in_section = rf'^-?\s*{re.escape(field_name)}:\s*(.+)$'
                    match = re.search(pattern_in_section, section_content, re.MULTILINE | re.IGNORECASE)
                    if match:
                        return match.group(1).strip()

                return None

            nom = extract_field("Nom", content) or "Sans nom"
            logger.info(f"  - Nom extrait: {nom}")

            notion_properties = {
                nom_property: {"title": [{"text": {"content": nom}}]},
                "État": {"status": {"name": "Brouillon IA"}},
            }

            if domain == "personnages":
                if type_val := extract_field("Type", content):
                    notion_properties["Type"] = {"select": {"name": type_val}}
                if genre := extract_field("Genre", content):
                    notion_properties["Genre"] = {"select": {"name": genre}}
                if alias := extract_field("Alias", content):
                    notion_properties["Alias"] = {"rich_text": [{"text": {"content": alias}}]}
                if occupation := extract_field("Occupation", content):
                    notion_properties["Occupation"] = {"rich_text": [{"text": {"content": occupation}}]}
                if age_str := extract_field("Âge", content):
                    try:
                        age = int(re.search(r"\d+", age_str).group())
                        notion_properties["Âge"] = {"number": age}
                    except Exception:  # pragma: no cover - best effort parsing
                        pass

                if axe := extract_field("Axe idéologique", content):
                    axe_clean = axe.split(",")[0].split(";")[0].strip()
                    notion_properties["Axe idéologique"] = {"select": {"name": axe_clean}}

                if archetype_raw := extract_field("Archétype littéraire", content):
                    archetypes = [a.strip() for a in re.split(r"[,;]\s*", archetype_raw) if a.strip()]
                    if archetypes:
                        notion_properties["Archétype littéraire"] = {
                            "multi_select": [{"name": arch} for arch in archetypes]
                        }

                if qualites_raw := extract_field("Qualités", content):
                    qualites = [q.strip() for q in re.split(r"[,;]\s*", qualites_raw) if q.strip()]
                    if qualites:
                        notion_properties["Qualités"] = {
                            "multi_select": [{"name": qual} for qual in qualites]
                        }

                if defauts_raw := extract_field("Défauts", content):
                    defauts = [d.strip() for d in re.split(r"[,;]\s*", defauts_raw) if d.strip()]
                    if defauts:
                        notion_properties["Défauts"] = {
                            "multi_select": [{"name": def_} for def_ in defauts]
                        }

                if reponse := extract_field("Réponse au problème moral", content):
                    notion_properties["Réponse au problème moral"] = {
                        "rich_text": [{"text": {"content": reponse[:2000]}}]
                    }

            elif domain == "lieux":
                for field_name in ["Catégorie", "Taille", "Rôle", "Sprint"]:
                    if value := extract_field(field_name, content):
                        value_clean = value.split(",")[0].split(";")[0].strip()[:100]
                        notion_properties[field_name] = {"select": {"name": value_clean}}
            elif domain == "especes":
                for field_name in [
                    "Type",
                    "Morphologie",
                    "Habitat",
                    "Comportement",
                    "Intelligence",
                    "Communication",
                    "Rang trophique",
                ]:
                    if value := extract_field(field_name, content):
                        value_clean = value.split(",")[0].split(";")[0].strip()[:100]
                        notion_properties[field_name] = {"select": {"name": value_clean}}
                if faib_raw := extract_field("Faiblesses", content):
                    vals = [v.strip() for v in re.split(r"[,;]\s*", faib_raw) if v.strip()]
                    if vals:
                        notion_properties["Faiblesses"] = {"multi_select": [{"name": v} for v in vals]}
            elif domain == "communautes":
                for field_name in [
                    "Type",
                    "Taille",
                    "Objectif",
                    "Ressource clé",
                    "Tabou",
                    "Structure",
                ]:
                    if value := extract_field(field_name, content):
                        value_clean = value.split(",")[0].split(";")[0].strip()[:100]
                        notion_properties[field_name] = {"select": {"name": value_clean}}
                if meth_raw := extract_field("Méthodes", content):
                    vals = [v.strip() for v in re.split(r"[,;]\s*", meth_raw) if v.strip()]
                    if vals:
                        notion_properties["Méthodes"] = {"multi_select": [{"name": v} for v in vals]}

            from agents.notion_relation_resolver import NotionRelationResolver

            resolver = NotionRelationResolver(fuzzy_threshold=0.80)
            relation_stats = {"resolved": 0, "unresolved": 0, "details": []}

            if domain == "personnages":
                if espece_raw := extract_field("Espèce", content):
                    espece_name = espece_raw.split(",")[0].split(";")[0].strip()

                    match = resolver.find_match(espece_name, "especes")
                    if match:
                        notion_properties["Espèce"] = {
                            "relation": [{"id": match.notion_id.replace("-", "")}]
                        }
                        relation_stats["resolved"] += 1
                        relation_stats["details"].append(
                            {
                                "field": "Espèce",
                                "resolved": [
                                    {
                                        "id": match.notion_id,
                                        "original": espece_name,
                                        "matched": match.matched_name,
                                        "confidence": match.confidence,
                                    }
                                ],
                                "unresolved": [],
                            }
                        )
                    else:
                        relation_stats["unresolved"] += 1
                        relation_stats["details"].append(
                            {
                                "field": "Espèce",
                                "resolved": [],
                                "unresolved": [espece_name],
                            }
                        )

                if communautes_raw := extract_field("Communautés", content):
                    communautes_names = re.split(r"[,;]\s*", communautes_raw)
                    communautes_names = [n.strip() for n in communautes_names if n.strip()]

                    communautes_resolved = []
                    communautes_unresolved = []

                    for comm_name in communautes_names:
                        match = resolver.find_match(comm_name, "communautes")
                        if match:
                            communautes_resolved.append(
                                {
                                    "id": match.notion_id,
                                    "original": comm_name,
                                    "matched": match.matched_name,
                                    "confidence": match.confidence,
                                }
                            )
                        else:
                            communautes_unresolved.append(comm_name)

                    if communautes_resolved:
                        notion_properties["Communautés"] = {
                            "relation": [
                                {"id": cr["id"].replace("-", "")} for cr in communautes_resolved
                            ]
                        }
                        relation_stats["resolved"] += len(communautes_resolved)

                    relation_stats["unresolved"] += len(communautes_unresolved)
                    if communautes_resolved or communautes_unresolved:
                        relation_stats["details"].append(
                            {
                                "field": "Communautés",
                                "resolved": communautes_resolved,
                                "unresolved": communautes_unresolved,
                            }
                        )

                if allies_raw := extract_field("Alliés", content):
                    allies_names = re.split(r"[,;]\s*", allies_raw)
                    allies_names = [n.strip() for n in allies_names if n.strip()]

                    allies_resolved = []
                    allies_unresolved = []

                    for ally_name in allies_names:
                        match = resolver.find_match(ally_name, "personnages")
                        if match:
                            allies_resolved.append(
                                {
                                    "id": match.notion_id,
                                    "original": ally_name,
                                    "matched": match.matched_name,
                                    "confidence": match.confidence,
                                }
                            )
                        else:
                            allies_unresolved.append(ally_name)

                    if allies_resolved:
                        notion_properties["Alliés"] = {
                            "relation": [
                                {"id": ar["id"].replace("-", "")} for ar in allies_resolved
                            ]
                        }
                        relation_stats["resolved"] += len(allies_resolved)

                    relation_stats["unresolved"] += len(allies_unresolved)
                    if allies_resolved or allies_unresolved:
                        relation_stats["details"].append(
                            {
                                "field": "Alliés",
                                "resolved": allies_resolved,
                                "unresolved": allies_unresolved,
                            }
                        )

                if ennemis_raw := extract_field("Ennemis", content):
                    ennemis_names = re.split(r"[,;]\s*", ennemis_raw)
                    ennemis_names = [n.strip() for n in ennemis_names if n.strip()]

                    ennemis_resolved = []
                    ennemis_unresolved = []

                    for ennemi_name in ennemis_names:
                        match = resolver.find_match(ennemi_name, "personnages")
                        if match:
                            ennemis_resolved.append(
                                {
                                    "id": match.notion_id,
                                    "original": ennemi_name,
                                    "matched": match.matched_name,
                                    "confidence": match.confidence,
                                }
                            )
                        else:
                            ennemis_unresolved.append(ennemi_name)

                    if ennemis_resolved:
                        notion_properties["Ennemis"] = {
                            "relation": [
                                {"id": er["id"].replace("-", "")} for er in ennemis_resolved
                            ]
                        }
                        relation_stats["resolved"] += len(ennemis_resolved)

                    relation_stats["unresolved"] += len(ennemis_unresolved)
                    if ennemis_resolved or ennemis_unresolved:
                        relation_stats["details"].append(
                            {
                                "field": "Ennemis",
                                "resolved": ennemis_resolved,
                                "unresolved": ennemis_unresolved,
                            }
                        )

            elif domain == "lieux":
                if secteurs_raw := extract_field("Secteurs reliés", content):
                    secteurs_names = re.split(r"[,;]\s*", secteurs_raw)
                    secteurs_names = [n.strip() for n in secteurs_names if n.strip()]

                    from agents.notion_relation_resolver import NotionRelationResolver
                    resolver = NotionRelationResolver(fuzzy_threshold=0.80)
                    secteurs_resolved = []
                    secteurs_unresolved = []

                    for secteur_name in secteurs_names:
                        match = resolver.find_match(secteur_name, "lieux")
                        if match:
                            secteurs_resolved.append(
                                {
                                    "id": match.notion_id,
                                    "original": secteur_name,
                                    "matched": match.matched_name,
                                    "confidence": match.confidence,
                                }
                            )
                        else:
                            secteurs_unresolved.append(secteur_name)

                    if secteurs_resolved:
                        notion_properties["Secteurs reliés"] = {
                            "relation": [
                                {"id": sr["id"].replace("-", "")} for sr in secteurs_resolved
                            ]
                        }
                        relation_stats["resolved"] += len(secteurs_resolved)

                    relation_stats["unresolved"] += len(secteurs_unresolved)
                    if secteurs_resolved or secteurs_unresolved:
                        relation_stats["details"].append(
                            {
                                "field": "Secteurs reliés",
                                "resolved": secteurs_resolved,
                                "unresolved": secteurs_unresolved,
                            }
                        )

                if figures_raw := extract_field("Figures associées", content):
                    figures_names = re.split(r"[,;]\s*", figures_raw)
                    figures_names = [n.strip() for n in figures_names if n.strip()]

                    from agents.notion_relation_resolver import NotionRelationResolver
                    resolver = NotionRelationResolver(fuzzy_threshold=0.80)
                    figures_resolved = []
                    figures_unresolved = []

                    for figure_name in figures_names:
                        match = resolver.find_match(figure_name, "personnages")
                        if match:
                            figures_resolved.append(
                                {
                                    "id": match.notion_id,
                                    "original": figure_name,
                                    "matched": match.matched_name,
                                    "confidence": match.confidence,
                                }
                            )
                        else:
                            figures_unresolved.append(figure_name)

                    if figures_resolved:
                        notion_properties["Figures associées"] = {
                            "relation": [
                                {"id": fr["id"].replace("-", "")} for fr in figures_resolved
                            ]
                        }
                        relation_stats["resolved"] += len(figures_resolved)

                    relation_stats["unresolved"] += len(figures_unresolved)
                    if figures_resolved or figures_unresolved:
                        relation_stats["details"].append(
                            {
                                "field": "Figures associées",
                                "resolved": figures_resolved,
                                "unresolved": figures_unresolved,
                            }
                        )

                if organisations_raw := extract_field("Organisations impliquées", content):
                    organisations_names = re.split(r"[,;]\s*", organisations_raw)
                    organisations_names = [n.strip() for n in organisations_names if n.strip()]

                    from agents.notion_relation_resolver import NotionRelationResolver
                    resolver = NotionRelationResolver(fuzzy_threshold=0.80)
                    organisations_resolved = []
                    organisations_unresolved = []

                    for organisation_name in organisations_names:
                        match = resolver.find_match(organisation_name, "communautes")
                        if match:
                            organisations_resolved.append(
                                {
                                    "id": match.notion_id,
                                    "original": organisation_name,
                                    "matched": match.matched_name,
                                    "confidence": match.confidence,
                                }
                            )
                        else:
                            organisations_unresolved.append(organisation_name)

                    if organisations_resolved:
                        notion_properties["Organisations impliquées"] = {
                            "relation": [
                                {"id": or_["id"].replace("-", "")} for or_ in organisations_resolved
                            ]
                        }
                        relation_stats["resolved"] += len(organisations_resolved)

                    relation_stats["unresolved"] += len(organisations_unresolved)
                    if organisations_resolved or organisations_unresolved:
                        relation_stats["details"].append(
                            {
                                "field": "Organisations impliquées",
                                "resolved": organisations_resolved,
                                "unresolved": organisations_unresolved,
                            }
                        )

            elif domain == "especes":
                # Relations (facultatives MVP)
                if lieux_raw := extract_field("Aire de répartition", content):
                    names = [n.strip() for n in re.split(r"[,;]\s*", lieux_raw) if n.strip()]
                    if names:
                        from agents.notion_relation_resolver import NotionRelationResolver
                        resolver = NotionRelationResolver(fuzzy_threshold=0.80)
                        resolved = []
                        unresolved = []
                        for nm in names:
                            match = resolver.find_match(nm, "lieux")
                            if match:
                                resolved.append({"id": match.notion_id, "original": nm, "matched": match.matched_name, "confidence": match.confidence})
                            else:
                                unresolved.append(nm)
                        if resolved:
                            notion_properties["Aire de répartition"] = {"relation": [{"id": r["id"].replace("-", "")} for r in resolved]}
                        if resolved or unresolved:
                            relation_stats["details"].append({"field": "Aire de répartition", "resolved": resolved, "unresolved": unresolved})
            elif domain == "communautes":
                # Relations (facultatives MVP)
                if lieux_raw := extract_field("Lieux d'influence", content):
                    names = [n.strip() for n in re.split(r"[,;]\s*", lieux_raw) if n.strip()]
                    if names:
                        from agents.notion_relation_resolver import NotionRelationResolver
                        resolver = NotionRelationResolver(fuzzy_threshold=0.80)
                        resolved = []
                        unresolved = []
                        for nm in names:
                            match = resolver.find_match(nm, "lieux")
                            if match:
                                resolved.append({"id": match.notion_id, "original": nm, "matched": match.matched_name, "confidence": match.confidence})
                            else:
                                unresolved.append(nm)
                        if resolved:
                            notion_properties["Lieux d'influence"] = {"relation": [{"id": r["id"].replace("-", "")} for r in resolved]}
                        if resolved or unresolved:
                            relation_stats["details"].append({"field": "Lieux d'influence", "resolved": resolved, "unresolved": unresolved})

            # Headers depuis la configuration centralisée
            headers = NotionConfig.get_headers()
            # Hard safety: if token missing, stop with clear UI feedback
            if not headers.get("Authorization") or headers["Authorization"].endswith(" ") or headers["Authorization"] == "Bearer ":
                logger.error("❌ NOTION_TOKEN manquant: export impossible")
                (container or st).error("❌ NOTION_TOKEN manquant. Ajoute le token dans `.env` et relance l'app.")
                try:
                    st.session_state._last_export_event = {
                        "success": False,
                        "error": "missing_token",
                        "source": "results",
                    }
                except Exception:
                    pass
                return {"success": False, "error": "missing_token"}

            payload = {
                "parent": {"database_id": database_id},
                "properties": notion_properties,
            }

            # Dry-run: ne pas écrire en mode DRY_RUN
            if NotionConfig.DRY_RUN:
                logger.warning("⚠️ MODE DRY-RUN : aucune page créée")
                page_id = "DRY-RUN"
                page_url = "https://www.notion.so"
            else:
                logger.info("  📡 Envoi requête POST à Notion API...")
                logger.info(f"  - Payload properties: {list(notion_properties.keys())}")
                response = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                logger.info(f"  - Status code: {response.status_code}")
                response.raise_for_status()
                page_id = response.json()["id"]
                page_url = response.json().get("url", "https://www.notion.so")
                logger.info(f"  ✓ Page créée: {page_id}")
                logger.info(f"  ✓ URL: {page_url}")

            blocks = []
            for line in content.split("\n"):
                if line.startswith("# "):
                    blocks.append(
                        {
                            "heading_1": {
                                "rich_text": [{"text": {"content": line[2:].strip()[:2000]}}]
                            }
                        }
                    )
                elif line.startswith("## "):
                    blocks.append(
                        {
                            "heading_2": {
                                "rich_text": [{"text": {"content": line[3:].strip()[:2000]}}]
                            }
                        }
                    )
                elif line.startswith("### "):
                    blocks.append(
                        {
                            "heading_3": {
                                "rich_text": [{"text": {"content": line[4:].strip()[:2000]}}]
                            }
                        }
                    )
                elif line.startswith("- "):
                    blocks.append(
                        {
                            "bulleted_list_item": {
                                "rich_text": [{"text": {"content": line[2:].strip()[:2000]}}]
                            }
                        }
                    )
                else:
                    blocks.append(
                        {
                            "paragraph": {
                                "rich_text": [{"text": {"content": line[:2000]}}]
                            }
                        }
                    )

            if blocks and not NotionConfig.DRY_RUN:
                requests.patch(
                    f"https://api.notion.com/v1/blocks/{page_id}/children",
                    headers=headers,
                    json={"children": blocks[:100]},
                    timeout=30,
                )

            relations_summary = ""
            if relation_stats["resolved"] > 0 or relation_stats["unresolved"] > 0:
                relations_summary = (
                    f"""<br>🔗 <b>Relations :</b> {relation_stats['resolved']} résolues"""
                )
                if relation_stats["unresolved"] > 0:
                    relations_summary += (
                        f""", {relation_stats['unresolved']} non trouvées"""
                    )

            # Nettoie l'indicateur et rend une confirmation persistante
            try:
                status_area.empty()
            except Exception:
                pass

            (container or st).markdown(
                f"""
            <div style="background-color: #f0f9ff; border-left: 5px solid #0ea5e9; padding: 1.25rem; margin: 1rem 0; border-radius: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="color: #0c4a6e; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.75rem;">
                    ✅ {domain_label} exporté vers Notion (BAC À SABLE){' — DRY-RUN' if NotionConfig.DRY_RUN else ''} !
                </div>
                <div style="color: #164e63; line-height: 1.8;">
                    📄 <b>Lien :</b> <a href="{page_url}" target="_blank" style="color: #0284c7; text-decoration: underline; font-weight: 600;">{nom}</a><br>
                    📊 <b>Base :</b> {domain_label}s (1) - Bac à sable<br>
                    🆔 <b>ID :</b> <code style="background-color: #e0f2fe; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-size: 0.85rem;">{page_id}</code>{relations_summary}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Toast rapide + persistance de l'état pour ré-affichage inline
            try:
                st.toast("✅ Export Notion terminé", icon="✅")
            except Exception:
                pass

            # Global banner state for top-level display (survives reruns and tab changes)
            try:
                st.session_state._last_export_event = {
                    "success": True,
                    "page_url": page_url,
                    "page_id": page_id,
                    "domain": domain,
                    "nom": nom,
                    "source": "results",
                }
                # Mirror to creation flow confirmation slot
                st.session_state._export_creation = {
                    "success": True,
                    "page_url": page_url,
                    "page_id": page_id,
                    "domain": domain,
                }
            except Exception:
                pass

            if relation_stats["details"]:
                with st.expander("🔍 Détails résolution relations"):
                    for detail in relation_stats["details"]:
                        field_name = detail["field"]
                        st.markdown(f"**{field_name}:**")

                        if "resolved" in detail:
                            if detail["resolved"]:
                                st.success(
                                    f"✅ {len(detail['resolved'])} correspondance(s) trouvée(s)"
                                )
                                for resolved in detail["resolved"]:
                                    confidence_pct = int(resolved["confidence"] * 100)
                                    match_icon = "🎯" if confidence_pct == 100 else "🔍"
                                    notion_url = (
                                        f"https://www.notion.so/{resolved['id'].replace('-', '')}"
                                    )
                                    st.markdown(
                                        f"  {match_icon} `{resolved['original']}` → "
                                        f"[**{resolved['matched']}**]({notion_url}) "
                                        f"({confidence_pct}%)"
                                    )

                            if detail["unresolved"]:
                                st.warning(
                                    f"⚠️ {len(detail['unresolved'])} non trouvé(s): "
                                    f"{', '.join(detail['unresolved'])}"
                                )

                        elif "status" in detail:
                            st.info(
                                f"ℹ️ {detail['status']}: {', '.join(detail['values'])}"
                            )

                        st.divider()

            with st.expander("📋 Prochaines étapes"):
                st.markdown(
                    """
                **À compléter manuellement dans Notion :**
                - 🔗 Relations (Communautés, Espèces, Lieux, etc.)
                - 📅 Dates et événements liés
                - 🗺️ Carte et zones limitrophes
                - ✅ Validation et changement d'état

                **Note :** Les relations ne peuvent pas être créées via API sans les IDs exacts des entités liées.
                """
                )

            return {
                "success": True,
                "page_url": page_url,
                "page_id": page_id,
                "domain": domain,
                "nom": nom,
                "dry_run": NotionConfig.DRY_RUN,
                "relations": relation_stats,
            }

    except Exception as exc:  # pragma: no cover - network path
        logger.error(f"❌ Erreur export: {exc}", exc_info=True)
        container.error(f"❌ Erreur lors de l'export : {exc}")
        container.exception(exc)
        return {
            "success": False,
            "error": str(exc),
        }


def show_results():
    """Affiche les résultats générés."""

    file_names = list_output_files()

    if not file_names:
        st.info("Aucun résultat généré pour le moment.")
        return

    st.write(f"**{len(file_names)} résultat(s) généré(s)**")

    selected_file = st.selectbox("Sélectionner un résultat", file_names)

    if not selected_file:
        return

    data = load_result_file(selected_file)

    if not data:
        st.error("Erreur lors du chargement du fichier (fichier invalide ou corrompu). Sélectionnez un autre résultat.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Cohérence", f"{float(data.get('coherence_score', 0.0)):.2f}")
    with col2:
        st.metric("Complétude", f"{float(data.get('completeness_score', 0.0)):.2f}")
    with col3:
        st.metric("Qualité", f"{float(data.get('quality_score', 0.0)):.2f}")

    if data.get("model_used"):
        model_config = data.get("model_config", {})
        icon = model_config.get("icon", "🤖")
        st.info(f"{icon} **Modèle utilisé :** {data['model_used']}")

    if bool(data.get("ready_for_publication", False)):
        st.success("✅ Prêt pour publication")
    else:
        st.warning("⚠️ Nécessite révision")

    # État persistant des exports par fichier
    if "_export_results" not in st.session_state:
        st.session_state._export_results = {}

    col_export, col_download = st.columns(2)

    with col_export:
        export_feedback = st.empty()
        if st.button(
            "📤 Exporter vers Notion",
            help="Créer une page dans Notion",
            key=f"export_{selected_file}",
        ):
            result_export = export_to_notion(data, container=export_feedback)
            # Persist result so confirmation remains visible after rerun
            if isinstance(result_export, dict) and result_export.get("success"):
                st.session_state._export_results[selected_file] = result_export
            else:
                # Keep at least an error marker to avoid silent disappear
                st.session_state._export_results[selected_file] = {
                    "success": False,
                    "error": (result_export or {}).get("error") if isinstance(result_export, dict) else "unknown",
                }

    with col_download:
        json_path = Path("outputs") / f"{selected_file}.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as handle:
                st.download_button(
                    label="💾 Télécharger JSON",
                    data=handle.read(),
                    file_name=f"{selected_file}.json",
                    mime="application/json",
                )

    # Affichage persistant du dernier export pour ce fichier (après reruns)
    persisted = st.session_state._export_results.get(selected_file)
    if persisted and isinstance(persisted, dict) and persisted.get("success"):
        link = persisted.get("page_url") or "https://www.notion.so"
        title = persisted.get("nom") or "Fiche Notion"
        st.markdown(
            f"""
        <div style="background-color: #ecfdf5; border-left: 5px solid #10b981; padding: 1rem; margin: 1rem 0; border-radius: 0.5rem;">
            ✅ Export confirmé — <a href="{link}" target="_blank" style="color:#047857; text-decoration: underline; font-weight:600;">ouvrir la fiche</a>
        </div>
        """,
            unsafe_allow_html=True,
        )
    elif persisted and isinstance(persisted, dict) and not persisted.get("success"):
        st.error(f"❌ Échec export: {persisted.get('error','inconnu')}")

    # Extra safety: when a selection is present but no visible message, render a lightweight hint
    if selected_file and persisted is None:
        st.caption("ℹ️ Tip: Utilise le bouton Exporter pour créer la fiche Notion du résultat sélectionné.")

    st.divider()

    with st.expander("📄 Contenu", expanded=True):
        st.markdown(data.get("content", ""))

    if data.get("review_issues"):
        with st.expander(f"⚠️ Problèmes identifiés ({len(data['review_issues'])})"):
            for issue in data["review_issues"]:
                severity = issue.get("severity", "minor")
                if severity == "critical":
                    severity_icon = "🔴"
                    box_color = "#f8d7da"
                    border_color = "#dc3545"
                elif severity == "major":
                    severity_icon = "🟠"
                    box_color = "#fff3cd"
                    border_color = "#ffc107"
                else:
                    severity_icon = "🟡"
                    box_color = "#d1ecf1"
                    border_color = "#17a2b8"

                st.markdown(
                    f"""
                <div style="background-color: {box_color}; border-left: 4px solid {border_color}; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem;">
                    {severity_icon} <b>{issue.get('category', 'General').capitalize()}</b><br>
                    {issue.get('description', 'N/A')}
                    {f"<br><i>💡 Suggestion: {issue['suggestion']}</i>" if issue.get('suggestion') else ""}
                </div>
                """,
                    unsafe_allow_html=True,
                )

    if data.get("corrections"):
        with st.expander(f"✏️ Corrections ({len(data['corrections'])})"):
            for corr in data["corrections"]:
                st.markdown(
                    f"""
                <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem;">
                    <b>{corr.get('type', 'N/A')}</b>: <code>{corr.get('original', '')}</code> → <code>{corr.get('corrected', '')}</code>
                    {f"<br><i>{corr['explanation']}</i>" if corr.get('explanation') else ""}
                </div>
                """,
                    unsafe_allow_html=True,
                )

    with st.expander("📊 Métadonnées"):
        st.json(data.get("writer_metadata") or data.get("metadata") or {})
