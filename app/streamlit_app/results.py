"""Result visualisation and export helpers."""

from __future__ import annotations

import base64
import csv
import io
import os
import re
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import requests
import streamlit as st

from .cache import list_output_files, load_result_file


def _ensure_results_styles() -> None:
    if st.session_state.get("_results_styles_loaded"):
        return

    st.markdown(
        """
        <style>
        .results-table {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            overflow: hidden;
            background: #ffffff;
            margin-bottom: 1rem;
        }
        .results-table__header,
        .results-table__row {
            display: grid;
            grid-template-columns: 1.3fr 1fr 1.4fr 1fr 0.6fr;
            align-items: center;
            padding: 0.6rem 0.85rem;
            column-gap: 0.75rem;
        }
        .results-table__header {
            background: #f3f4f6;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
            font-weight: 600;
        }
        .results-table__row {
            border-top: 1px solid #e5e7eb;
            font-size: 0.9rem;
            color: #111827;
        }
        .results-table__row:hover {
            background: #f9fafb;
        }
        .results-table__row--active {
            background: #e0f2fe;
            border-color: #bae6fd;
        }
        .results-table__row--active:hover {
            background: #dbeafe;
        }
        .results-status {
            display: inline-flex;
            align-items: center;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .results-status--ok {
            background: #dcfce7;
            color: #166534;
        }
        .results-status--warn {
            background: #fef3c7;
            color: #92400e;
        }
        .results-download-link {
            text-decoration: none;
            font-size: 1.1rem;
        }
        .issue-card {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 0.75rem;
            margin: 0.5rem 0;
            background: #ffffff;
        }
        .issue-card--critical {
            border-left: 4px solid #dc2626;
            background: #fee2e2;
        }
        .issue-card--major {
            border-left: 4px solid #f97316;
            background: #fff7ed;
        }
        .issue-card--minor {
            border-left: 4px solid #facc15;
            background: #fefce8;
        }
        .issue-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 0.4rem;
        }
        .issue-badge--critical {
            background: #dc2626;
            color: #ffffff;
        }
        .issue-badge--major {
            background: #f97316;
            color: #ffffff;
        }
        .issue-badge--minor {
            background: #facc15;
            color: #1f2937;
        }
        .issue-card__body {
            color: #1f2937;
            font-size: 0.9rem;
        }
        .issue-card__suggestion {
            margin-top: 0.4rem;
            font-size: 0.85rem;
            color: #374151;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_results_styles_loaded"] = True


def _build_results_overview(file_names: list[str]) -> list[dict[str, Any]]:
    outputs_dir = Path("outputs")
    records: list[dict[str, Any]] = []

    for stem in file_names:
        json_path = outputs_dir / f"{stem}.json"
        if not json_path.exists():
            continue

        data = load_result_file(stem)
        if not data:
            continue

        timestamp = datetime.fromtimestamp(json_path.stat().st_mtime)
        formatted_date = timestamp.strftime("%d/%m/%Y %H:%M")
        domain = str(data.get("domain", "personnages")).capitalize()
        model_name = data.get("model_used")
        model_config = data.get("model_config", {})
        model_icon = model_config.get("icon", "🤖")
        ready = bool(data.get("ready_for_publication"))
        status_label = "✅ Prêt" if ready else "⚠️ À revoir"

        download_href = (
            "data:application/json;base64," + base64.b64encode(json_path.read_bytes()).decode("utf-8")
        )

        records.append(
            {
                "stem": stem,
                "date": formatted_date,
                "domain": domain,
                "model": f"{model_icon} {model_name}" if model_name else model_icon,
                "status": status_label,
                "ready": ready,
                "download_href": download_href,
            }
        )

    return records


def _render_results_overview(records: list[dict[str, Any]], selected_file: str | None) -> None:
    if not records:
        return

    _ensure_results_styles()

    header_html = """
        <div class="results-table__header">
            <div>Date</div>
            <div>Domaine</div>
            <div>Modèle</div>
            <div>État</div>
            <div>Télécharger</div>
        </div>
    """

    rows_html = []
    for record in records:
        row_class = "results-table__row"
        if selected_file and record["stem"] == selected_file:
            row_class += " results-table__row--active"

        status_class = "results-status results-status--ok" if record["ready"] else "results-status results-status--warn"

        rows_html.append(
            """
            <div class="{row_class}">
                <div>{date}</div>
                <div>{domain}</div>
                <div>{model}</div>
                <div><span class="{status_class}">{status}</span></div>
                <div><a class="results-download-link" href="{href}" download="{stem}.json" title="Télécharger {stem}.json">⬇️</a></div>
            </div>
            """.format(
                row_class=row_class,
                date=escape(record["date"]),
                domain=escape(record["domain"]),
                model=escape(record["model"]),
                status_class=status_class,
                status=escape(record["status"]),
                href=record["download_href"],
                stem=escape(record["stem"]),
            )
        )

    st.markdown(
        """
        <div class="results-table">
            {header}
            {rows}
        </div>
        """.format(header=header_html, rows="".join(rows_html)),
        unsafe_allow_html=True,
    )


def export_to_notion(result):
    """Exporte le résultat vers Notion (BAC À SABLE)."""
    try:
        with st.spinner("📤 Export vers Notion en cours..."):
            domain = result.get("domain", "personnages").lower()
            content = result.get("content", "")

            if domain == "lieux":
                database_id = "2806e4d21b4580969f1cd7463a4c889c"
                domain_label = "Lieu"
                nom_property = "Nom"
            else:
                database_id = "2806e4d21b458012a744d8d6723c8be1"
                domain_label = "Personnage"
                nom_property = "Nom"

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

            headers = {
                "Authorization": f"Bearer {os.environ.get('NOTION_API_KEY', '')}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            }

            payload = {
                "parent": {"database_id": database_id},
                "properties": notion_properties,
            }

            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            page_id = response.json()["id"]
            page_url = response.json().get("url", "https://www.notion.so")

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

            if blocks:
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

            st.markdown(
                f"""
            <div style="background-color: #f0f9ff; border-left: 5px solid #0ea5e9; padding: 1.25rem; margin: 1rem 0; border-radius: 0.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="color: #0c4a6e; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.75rem;">
                    ✅ {domain_label} exporté vers Notion (BAC À SABLE) !
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

    except Exception as exc:  # pragma: no cover - network path
        st.error(f"❌ Erreur lors de l'export : {exc}")
        st.exception(exc)


def show_results():
    """Affiche les résultats générés."""

    file_names = list_output_files()

    if not file_names:
        st.info("Aucun résultat généré pour le moment.")
        return

    st.write(f"**{len(file_names)} résultat(s) généré(s)**")

    overview_records = _build_results_overview(file_names)
    current_selected = st.session_state.get("_results_selected_file")
    if not current_selected or current_selected not in file_names:
        current_selected = file_names[0]

    if overview_records:
        st.markdown("### 📚 Historique des générations")
        _render_results_overview(overview_records, current_selected)
        label_map = {
            record["stem"]: f"{record['date']} · {record['domain']} · {record['model']} ({record['status']})"
            for record in overview_records
        }
    else:
        label_map = {stem: stem for stem in file_names}

    selected_file = st.selectbox(
        "Sélectionner un résultat",
        file_names,
        index=file_names.index(current_selected),
        format_func=lambda stem: label_map.get(stem, stem),
    )

    st.session_state["_results_selected_file"] = selected_file

    data = load_result_file(selected_file)

    if not data:
        st.error("Erreur lors du chargement du fichier")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Cohérence", f"{data['coherence_score']:.2f}")
    with col2:
        st.metric("Complétude", f"{data['completeness_score']:.2f}")
    with col3:
        st.metric("Qualité", f"{data['quality_score']:.2f}")

    if data.get("model_used"):
        model_config = data.get("model_config", {})
        icon = model_config.get("icon", "🤖")
        st.info(f"{icon} **Modèle utilisé :** {data['model_used']}")

    if data["ready_for_publication"]:
        st.success("✅ Prêt pour publication")
    else:
        st.warning("⚠️ Nécessite révision")

    col_export, col_download = st.columns(2)

    with col_export:
        if st.button(
            "📤 Exporter vers Notion",
            help="Créer une page dans Notion",
            key=f"export_{selected_file}",
        ):
            export_to_notion(data)

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

    st.divider()

    with st.expander("📄 Contenu", expanded=True):
        st.markdown(data["content"])

    if data.get("review_issues"):
        severity_order = {"critical": 0, "major": 1, "minor": 2}
        sorted_issues = sorted(
            data["review_issues"],
            key=lambda issue: severity_order.get(issue.get("severity", "minor"), 3),
        )

        with st.expander(f"⚠️ Problèmes identifiés ({len(sorted_issues)})"):
            _ensure_results_styles()
            for issue in sorted_issues:
                severity = issue.get("severity", "minor")
                category = issue.get("category", "General").capitalize()
                description = issue.get("description", "N/A")
                suggestion = issue.get("suggestion")

                if severity == "critical":
                    badge_class = "issue-badge issue-badge--critical"
                    card_class = "issue-card issue-card--critical"
                    icon = "🔴"
                elif severity == "major":
                    badge_class = "issue-badge issue-badge--major"
                    card_class = "issue-card issue-card--major"
                    icon = "🟠"
                else:
                    badge_class = "issue-badge issue-badge--minor"
                    card_class = "issue-card issue-card--minor"
                    icon = "🟡"

                st.markdown(
                    """
                    <div class="{card_class}">
                        <div class="{badge_class}">{icon} {category}</div>
                        <div class="issue-card__body">{description}</div>
                        {suggestion_block}
                    </div>
                    """.format(
                        card_class=card_class,
                        badge_class=badge_class,
                        icon=icon,
                        category=escape(category),
                        description=escape(description),
                        suggestion_block=(
                            f"<div class='issue-card__suggestion'>💡 {escape(suggestion)}</div>"
                            if suggestion
                            else ""
                        ),
                    ),
                    unsafe_allow_html=True,
                )

    if data.get("corrections"):
        with st.expander(f"✏️ Corrections ({len(data['corrections'])})"):
            corrections = data["corrections"]

            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)
            csv_writer.writerow(["Type", "Original", "Correction", "Explication"])
            markdown_lines = ["| Type | Original | Correction | Explication |", "| --- | --- | --- | --- |"]

            def _escape_markdown(value: str) -> str:
                return value.replace("|", "\\|").replace("\n", "<br>")

            for corr in corrections:
                corr_type = corr.get("type", "N/A")
                original = corr.get("original", "")
                corrected = corr.get("corrected", "")
                explanation = corr.get("explanation", "")
                csv_writer.writerow([corr_type, original, corrected, explanation])
                markdown_lines.append(
                    f"| {_escape_markdown(corr_type)} | {_escape_markdown(original)} | {_escape_markdown(corrected)} | {_escape_markdown(explanation)} |"
                )

            csv_content = csv_buffer.getvalue()
            markdown_content = "\n".join(markdown_lines)

            col_csv, col_md = st.columns(2)
            with col_csv:
                st.download_button(
                    "⬇️ Export CSV",
                    data=csv_content,
                    file_name=f"{selected_file}_corrections.csv",
                    mime="text/csv",
                )
            with col_md:
                st.download_button(
                    "⬇️ Export Markdown",
                    data=markdown_content,
                    file_name=f"{selected_file}_corrections.md",
                    mime="text/markdown",
                )

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
        st.json(data["writer_metadata"])
