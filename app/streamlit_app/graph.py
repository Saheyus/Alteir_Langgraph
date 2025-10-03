"""Graph visualisation tab."""

import streamlit as st


def render_graph_tab():
    """Affiche l'onglet graphe de relations."""

    st.header("🕸️ Graphe de Relations")

    st.info(
        """
        📊 **Visualisation des relations entre entités générées**

        Explore les connexions entre personnages, lieux, communautés et objets extraites depuis vos fiches.
        """
    )

    from agents.relation_extractor import RelationExtractor
    from agents.graph_visualizer import create_interactive_graph, create_stats_chart
    from agents.relation_graph import EntityType

    with st.spinner("Extraction des relations depuis les fiches..."):
        extractor = RelationExtractor()
        graph = extractor.extract_from_outputs()

    stats = graph.stats()

    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Entités", stats["total_entities"])
    with col_stat2:
        st.metric("Relations", stats["total_relations"])
    with col_stat3:
        st.metric("Connexions moy.", f"{stats['avg_connections_per_entity']:.1f}")
    with col_stat4:
        if graph.entities:
            most_connected = max(
                graph.entities.keys(),
                key=lambda eid: len(graph.get_all_relations(eid)),
            )
            entity = graph.get_entity(most_connected)
            st.metric("Hub principal", entity.name if entity else "N/A")

    st.divider()

    st.subheader("Filtres")
    col_filter1, col_filter2 = st.columns(2)

    filter_types = []
    with col_filter1:
        if st.checkbox("Personnages", value=True):
            filter_types.append(EntityType.CHARACTER)
        if st.checkbox("Communautés", value=True):
            filter_types.append(EntityType.COMMUNITY)
        if st.checkbox("Espèces", value=False):
            filter_types.append(EntityType.SPECIES)
    with col_filter2:
        if st.checkbox("Lieux", value=True):
            filter_types.append(EntityType.LOCATION)
        if st.checkbox("Objets", value=False):
            filter_types.append(EntityType.ITEM)
        if st.checkbox("Événements", value=False):
            filter_types.append(EntityType.EVENT)

    layout_option = st.selectbox(
        "Type de disposition",
        ["spring", "circular", "kamada_kawai"],
        index=0,
        help="Algorithme de disposition des nœuds",
    )

    show_labels = st.checkbox("Afficher les labels", value=True)

    st.divider()

    if stats["total_entities"] == 0:
        st.warning("⚠️ Aucune entité trouvée. Générez d'abord quelques fiches dans l'onglet 'Créer'.")
    else:
        try:
            fig = create_interactive_graph(
                graph,
                layout=layout_option,
                width=1200,
                height=700,
                show_labels=show_labels,
                filter_types=filter_types if filter_types else None,
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:  # pragma: no cover - rendering fallback
            st.error(f"Erreur lors de la génération du graphe : {exc}")
            import traceback

            st.code(traceback.format_exc())

    with st.expander("📊 Statistiques détaillées"):
        if stats["total_entities"] > 0:
            try:
                stats_fig = create_stats_chart(graph)
                st.plotly_chart(stats_fig, use_container_width=True)
            except Exception as exc:  # pragma: no cover - chart fallback
                st.error(f"Erreur stats : {exc}")

        st.subheader("Entités par type")
        entity_type_data = [
            {"Type": key, "Nombre": value}
            for key, value in stats["entity_types"].items()
            if value > 0
        ]
        if entity_type_data:
            st.table(entity_type_data)

        st.subheader("Relations par type")
        relation_type_data = [
            {"Type": key, "Nombre": value}
            for key, value in stats["relation_types"].items()
            if value > 0
        ]
        if relation_type_data:
            st.table(relation_type_data)
