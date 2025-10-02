#!/usr/bin/env python3
"""
Module de visualisation interactive du graphe de relations
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional
import plotly.graph_objects as go
import networkx as nx

sys.path.append(str(Path(__file__).parent.parent))

from agents.relation_graph import RelationGraph, EntityType, RelationType

# Couleurs par type d'entité
ENTITY_COLORS = {
    EntityType.PERSONNAGE: '#667eea',  # Violet
    EntityType.LIEU: '#f59e0b',  # Orange
    EntityType.COMMUNAUTE: '#10b981',  # Vert
    EntityType.ESPECE: '#8b5cf6',  # Pourpre
    EntityType.OBJET: '#ef4444',  # Rouge
    EntityType.EVENEMENT: '#06b6d4',  # Cyan
}

# Icônes par type d'entité
ENTITY_ICONS = {
    EntityType.PERSONNAGE: '●',
    EntityType.LIEU: '■',
    EntityType.COMMUNAUTE: '▲',
    EntityType.ESPECE: '◆',
    EntityType.OBJET: '★',
    EntityType.EVENEMENT: '⬢',
}

def create_interactive_graph(
    graph: RelationGraph,
    layout: str = 'spring',
    width: int = 1200,
    height: int = 800,
    show_labels: bool = True,
    filter_types: Optional[List[EntityType]] = None
) -> go.Figure:
    """
    Crée une visualisation interactive du graphe avec Plotly
    
    Args:
        graph: Le graphe de relations
        layout: Type de layout ('spring', 'circular', 'kamada_kawai', 'random')
        width: Largeur de la figure
        height: Hauteur de la figure
        show_labels: Afficher les labels des nœuds
        filter_types: Types d'entités à afficher (None = tous)
    
    Returns:
        Figure Plotly interactive
    """
    # Convertir en NetworkX
    G = graph.to_networkx()
    
    # Filtrer par type si nécessaire
    if filter_types:
        nodes_to_keep = [
            n for n in G.nodes()
            if EntityType(G.nodes[n]['type']) in filter_types
        ]
        G = G.subgraph(nodes_to_keep)
    
    # Calculer le layout
    if layout == 'spring':
        pos = nx.spring_layout(G, k=2, iterations=50)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    elif layout == 'random':
        pos = nx.random_layout(G)
    else:
        pos = nx.spring_layout(G)
    
    # Créer les traces pour les arêtes
    edge_traces = []
    
    # Grouper les arêtes par type pour avoir des couleurs différentes
    edges_by_type = {}
    for edge in G.edges(data=True):
        relation_type = edge[2].get('type', 'unknown')
        if relation_type not in edges_by_type:
            edges_by_type[relation_type] = []
        edges_by_type[relation_type].append(edge)
    
    # Créer une trace par type de relation
    relation_colors = {
        RelationType.CONNAIT.value: '#9ca3af',
        RelationType.AMI.value: '#10b981',
        RelationType.ENNEMI.value: '#ef4444',
        RelationType.FAMILLE.value: '#f59e0b',
        RelationType.HABITE.value: '#8b5cf6',
        RelationType.MEMBRE_DE.value: '#06b6d4',
        RelationType.POSSEDE.value: '#f97316',
        RelationType.CONTIENT.value: '#14b8a6',
    }
    
    for relation_type, edges in edges_by_type.items():
        edge_x = []
        edge_y = []
        
        for edge in edges:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(
                width=1,
                color=relation_colors.get(relation_type, '#9ca3af')
            ),
            hoverinfo='none',
            mode='lines',
            name=relation_type,
            showlegend=True
        )
        edge_traces.append(edge_trace)
    
    # Créer les traces pour les nœuds (une par type d'entité)
    node_traces = []
    
    # Grouper les nœuds par type
    nodes_by_type = {}
    for node in G.nodes(data=True):
        node_type = EntityType(node[1]['type'])
        if node_type not in nodes_by_type:
            nodes_by_type[node_type] = []
        nodes_by_type[node_type].append(node)
    
    # Créer une trace par type d'entité
    for entity_type, nodes in nodes_by_type.items():
        node_x = []
        node_y = []
        node_text = []
        node_hover = []
        
        for node in nodes:
            x, y = pos[node[0]]
            node_x.append(x)
            node_y.append(y)
            
            name = node[1]['name']
            node_text.append(name if show_labels else '')
            
            # Créer le texte de hover
            hover_text = f"<b>{name}</b><br>"
            hover_text += f"Type: {node[1]['type']}<br>"
            hover_text += f"Connexions: {G.degree(node[0])}"
            node_hover.append(hover_text)
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text' if show_labels else 'markers',
            text=node_text,
            textposition="top center",
            hovertext=node_hover,
            hoverinfo='text',
            marker=dict(
                size=15,
                color=ENTITY_COLORS[entity_type],
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            name=entity_type.value,
            showlegend=True
        )
        node_traces.append(node_trace)
    
    # Créer la figure
    fig = go.Figure(
        data=edge_traces + node_traces,
        layout=go.Layout(
            title=dict(
                text='Graphe de Relations - GDD Alteir',
                font=dict(size=20)
            ),
            showlegend=True,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            width=width,
            height=height,
            plot_bgcolor='#0e1117',
            paper_bgcolor='#0e1117',
            font=dict(color='white'),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0,0,0,0.5)'
            )
        )
    )
    
    return fig


def create_ego_graph(
    graph: RelationGraph,
    entity_id: str,
    depth: int = 2,
    **kwargs
) -> go.Figure:
    """
    Crée un graphe ego-centré sur une entité
    
    Args:
        graph: Le graphe complet
        entity_id: ID de l'entité centrale
        depth: Profondeur du sous-graphe
        **kwargs: Arguments additionnels pour create_interactive_graph
    
    Returns:
        Figure Plotly du graphe ego
    """
    subgraph = graph.get_subgraph([entity_id], depth=depth)
    
    # Titre personnalisé
    entity = graph.get_entity(entity_id)
    if entity and 'title' not in kwargs:
        kwargs['title'] = f"Relations de {entity.name}"
    
    return create_interactive_graph(subgraph, **kwargs)


def create_stats_chart(graph: RelationGraph) -> go.Figure:
    """
    Crée un graphique de statistiques sur le graphe
    
    Args:
        graph: Le graphe de relations
    
    Returns:
        Figure Plotly avec statistiques
    """
    stats = graph.stats()
    
    # Créer un subplot avec 2 graphiques
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Entités par type', 'Relations par type'),
        specs=[[{"type": "pie"}, {"type": "bar"}]]
    )
    
    # Graphique camembert des entités
    entity_types = list(stats['entity_types'].keys())
    entity_counts = list(stats['entity_types'].values())
    
    fig.add_trace(
        go.Pie(
            labels=entity_types,
            values=entity_counts,
            marker=dict(colors=[ENTITY_COLORS.get(EntityType(t), '#9ca3af') for t in entity_types])
        ),
        row=1, col=1
    )
    
    # Graphique en barres des relations
    relation_types = [k for k, v in stats['relation_types'].items() if v > 0]
    relation_counts = [v for k, v in stats['relation_types'].items() if v > 0]
    
    fig.add_trace(
        go.Bar(
            x=relation_types,
            y=relation_counts,
            marker=dict(color='#667eea')
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text="Statistiques du Graphe de Relations",
        showlegend=False,
        height=500,
        plot_bgcolor='#0e1117',
        paper_bgcolor='#0e1117',
        font=dict(color='white')
    )
    
    return fig

