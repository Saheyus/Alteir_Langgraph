"""Result visualisation and export helpers."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from .cache import list_output_files, load_result_file


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

    outputs_dir = Path("outputs")
    previous_selection = st.session_state.get("results_selected_file", file_names[0])

    overview_rows = []
    for stem in file_names:
        json_path = outputs_dir / f"{stem}.json"
        data_preview = load_result_file(stem)
        if not data_preview:
            continue
        timestamp = datetime.fromtimestamp(json_path.stat().st_mtime)
        domain_label = data_preview.get("domain", "").capitalize() or "—"
        model_used = data_preview.get("model_used") or "—"
        ready = data_preview.get("ready_for_publication", False)
        context_count = len(data_preview.get("context", {}).get("pages", [])) if data_preview.get("context") else 0
        overview_rows.append(
            {
                "id": stem,
                "Ouvrir": stem == previous_selection,
                "Télécharger": False,
                "Date": timestamp.strftime("%Y-%m-%d %H:%M"),
                "Domaine": domain_label,
                "Modèle": model_used,
                "Publication": "✅ Prêt" if ready else "À revoir",
                "Contexte": context_count,
            }
        )

    if not overview_rows:
        st.error("Impossible de charger les métadonnées des résultats.")
        return

    overview_df = pd.DataFrame(overview_rows).set_index("id")

    domains_available = sorted(overview_df["Domaine"].unique())
    status_available = sorted(overview_df["Publication"].unique())

    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 2])
    with filter_col1:
        domain_filter = st.multiselect(
            "Domaine",
            options=domains_available,
            default=domains_available,
            key="results_domain_filter",
        )
    with filter_col2:
        status_filter = st.multiselect(
            "État",
            options=status_available,
            default=status_available,
            key="results_status_filter",
        )
    with filter_col3:
        search_query = st.text_input(
            "Recherche",
            key="results_search_query",
            placeholder="Nom, modèle ou date",
        )

    filtered_overview = overview_df[
        overview_df["Domaine"].isin(domain_filter)
        & overview_df["Publication"].isin(status_filter)
    ]

    if search_query:
        q = search_query.lower()

        def _match(row: pd.Series) -> bool:
            haystack = " ".join(
                [
                    row.name,
                    str(row.get("Date", "")),
                    str(row.get("Domaine", "")),
                    str(row.get("Modèle", "")),
                    str(row.get("Publication", "")),
                ]
            ).lower()
            return q in haystack

        filtered_overview = filtered_overview[filtered_overview.apply(_match, axis=1)]

    if filtered_overview.empty:
        st.info("Aucun résultat ne correspond aux filtres sélectionnés.")
        return

    edited_overview = st.data_editor(
        filtered_overview,
        hide_index=True,
        use_container_width=True,
        key="results_overview_editor",
        column_config={
            "Ouvrir": st.column_config.CheckboxColumn(
                "Ouvrir",
                help="Afficher les détails du résultat",
            ),
            "Télécharger": st.column_config.CheckboxColumn(
                "Téléchargement",
                help="Cocher pour activer le bouton de téléchargement ci-dessous",
            ),
            "Contexte": st.column_config.NumberColumn(
                "Contexte",
                help="Nombre de fiches utilisées",
                format="%d",
            ),
        },
    )

    open_candidates = [idx for idx, row in edited_overview.iterrows() if row.get("Ouvrir")]
    if open_candidates:
        selected_file = open_candidates[-1]
    else:
        selected_file = previous_selection if previous_selection in overview_df.index else overview_df.index[0]

    st.session_state.results_selected_file = selected_file

    download_candidates = [idx for idx, row in edited_overview.iterrows() if row.get("Télécharger")]
    if download_candidates:
        with st.expander("Téléchargements rapides", expanded=True):
            for stem in download_candidates:
                json_path = outputs_dir / f"{stem}.json"
                if not json_path.exists():
                    continue
                st.download_button(
                    label=f"💾 {stem}.json",
                    data=json_path.read_text(encoding="utf-8"),
                    file_name=f"{stem}.json",
                    mime="application/json",
                    key=f"download_inline_{stem}",
                )

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
        json_path = outputs_dir / f"{selected_file}.json"
        if json_path.exists():
            st.download_button(
                label="💾 Télécharger JSON",
                data=json_path.read_text(encoding="utf-8"),
                file_name=f"{selected_file}.json",
                mime="application/json",
            )

    st.divider()

    with st.expander("📄 Contenu", expanded=True):
        st.markdown(data["content"])

    if data.get("review_issues"):
        severity_order = {"critical": 0, "major": 1, "minor": 2}
        issues_sorted = sorted(
            data["review_issues"],
            key=lambda issue: severity_order.get(issue.get("severity", "minor"), 3),
        )
        issues_md = ["# Problèmes identifiés"]

        with st.expander(f"⚠️ Problèmes identifiés ({len(issues_sorted)})"):
            severity_styles = {
                "critical": ("🔴", "Critique", "#dc2626", "#fee2e2"),
                "major": ("🟠", "Majeur", "#d97706", "#fff7ed"),
                "minor": ("🟡", "Mineur", "#2563eb", "#eff6ff"),
            }

            for issue in issues_sorted:
                severity_key = issue.get("severity", "minor")
                icon, label, border_color, bg_color = severity_styles.get(
                    severity_key, ("🟡", "Mineur", "#2563eb", "#eff6ff")
                )
                category = issue.get("category", "Général").capitalize()
                description = issue.get("description", "N/A")
                suggestion = issue.get("suggestion")

                st.markdown(
                    f"""
                    <div style="background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 1rem; margin: 0.5rem 0; border-radius: 0.4rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong>{category}</strong>
                            <span class="badge-soft secondary">{icon} {label}</span>
                        </div>
                        <div style="margin-top:0.5rem;">{description}</div>
                        {f"<div style='margin-top:0.5rem; font-style:italic;'>💡 {suggestion}</div>" if suggestion else ""}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                issues_md.append(f"- **{label}** · {category}: {description}")
                if suggestion:
                    issues_md.append(f"  - 💡 {suggestion}")

            st.download_button(
                "⬇️ Export Markdown",
                data="\n".join(issues_md),
                file_name=f"{selected_file}_issues.md",
                mime="text/markdown",
                key=f"download_issues_{selected_file}",
            )

    if data.get("corrections"):
        with st.expander(f"✏️ Corrections ({len(data['corrections'])})"):
            corrections_df = pd.DataFrame(data["corrections"])
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

            if not corrections_df.empty:
                markdown_lines = ["# Corrections proposées"]
                for _, row in corrections_df.iterrows():
                    markdown_lines.append(
                        f"- **{row.get('type', 'N/A')}** : `{row.get('original', '')}` → `{row.get('corrected', '')}`"
                    )
                    if row.get("explanation"):
                        markdown_lines.append(f"  - 💡 {row['explanation']}")

                st.download_button(
                    "⬇️ Export Markdown",
                    data="\n".join(markdown_lines),
                    file_name=f"{selected_file}_corrections.md",
                    mime="text/markdown",
                    key=f"download_corrections_md_{selected_file}",
                )

                st.download_button(
                    "⬇️ Export CSV",
                    data=corrections_df.to_csv(index=False),
                    file_name=f"{selected_file}_corrections.csv",
                    mime="text/csv",
                    key=f"download_corrections_csv_{selected_file}",
                )

    with st.expander("📊 Métadonnées"):
        st.json(data["writer_metadata"])
