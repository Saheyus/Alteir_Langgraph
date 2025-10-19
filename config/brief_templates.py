#!/usr/bin/env python3
"""Brief templates per domain and complexity mode.

Placeholders map to categories in TAGS_REGISTRY.
"""

BRIEF_TEMPLATES = {
    "Personnages": {
        "simple": (
            "Rédige un personnage de type [TYPE], de l'espèce [ESPÈCE], vivant à [LIEU]. "
            "Il ou elle occupe la fonction de [OCCUPATION] au sein de [FACTION]. "
            "Sa personnalité se caractérise par [QUALITÉS], mais souffre aussi de [DÉFAUTS]. Genre: [GENRE]."
        ),
        "complexe": (
            "Rédige un personnage de type [TYPE], de genre [GENRE], faisant partie de l'espèce [ESPÈCE], [CATÉGORIE_ÂGE]. "
            "Il ou elle est originaire de [ORIGINE] et vit actuellement à [LIEU]. Son apparence est [APPARENCE]. "
            "Il ou elle occupe la fonction de [OCCUPATION] au sein de [FACTION]. Son état de santé  est qualifié de [ÉTAT_SANTÉ]. "
            "Il ou elle fait partie de la classe sociale [CLASSE_SOCIALE] et son niveau d'éducation est [ÉDUCATION]. Son statut social  au sein de sa classe est [STATUT_SOCIAL]. "
            "Sa personnalité se caractérise par [QUALITÉS], mais souffre aussi de [DÉFAUTS]. Sa faiblesse psychologiqu est liée à [FAIBLESSE]. "
            "Ce qu'il ou elle désire par-dessus tout : [DÉSIR], alors qu'en réalité il ou elle a besoin de [BESOIN]. "
            "Son axe idéologique : [AXE_IDÉOLOGIQUE]. Il/Elle incarne l'archétype littéraire de John Truby : [ARCHÉTYPE]. "
            "Il ou elle s'exprime principalement en [REGISTRE_LANGUE]. Face à la question \"Comment résister à un système d'oppression "
            "quand ce système définit les termes mêmes de la résistance ?\", il ou elle [POSTURE_MORALE]."
        ),
    },
    "Lieux": {
        "simple": (
            "Rédige un lieu de type [RÔLE], de taille [TAILLE], situé dans [LIEU]. "
            "L'atmosphère générale est [ATMOSPHÈRE]. Les communautés présentes : [FACTION]. "
            "Particularité physique ou magique notable : [PARTICULARITÉ]."
        ),
        "complexe": (
            "Rédige un lieu de type [RÔLE], de taille [TAILLE], situé dans [LIEU]. Son apparence générale est [APPARENCE_LIEU]. "
            "L'atmosphère générale est [ATMOSPHÈRE]. Les communautés présentes : [FACTION]. Les espèces dominantes : [ESPÈCE]. "
            "Son accessibilité : [ACCESSIBILITÉ]. Son niveau de danger : [DANGER]. Sa particularité physique ou magique : [PARTICULARITÉ]. "
            "Les lois physiques locales : [LOIS_PHYSIQUES]. Sa fonction principale dans l'histoire : [FONCTION_NARRATIVE]."
        ),
    },
    "Espèces": {
        "simple": (
            "Rédige une espèce de type [TYPE], vivant principalement en [HABITAT]. "
            "Morphologie dominante : [MORPHOLOGIE]. Comportement : [COMPORTEMENT]. "
            "Mode de communication : [COMMUNICATION]. Faiblesse : [FAIBLESSE]."
        ),
        "complexe": (
            "Rédige une espèce de type [TYPE], intelligence [INTELLIGENCE], adaptée à l'habitat [HABITAT]. "
            "Morphologie : [MORPHOLOGIE]. Comportements typiques : [COMPORTEMENT]. "
            "Communication : [COMMUNICATION]. Ressource clé : [RESSOURCE_CLÉ]. Rang trophique : [RANG_TROPHIQUE]. "
            "Indique 1-2 lieux de présence : [LIEU]. Décris un rituel observable : [RITUEL]."
        ),
    },
    "Communautés": {
        "simple": (
            "Rédige une communauté de type [TYPE], de taille [TAILLE], opérant à [LIEU]. "
            "Objectif principal : [OBJECTIF]. Méthodes : [MÉTHODES]. Tabou : [TABOU]."
        ),
        "complexe": (
            "Rédige une communauté de type [TYPE], taille [TAILLE], structurée de façon [STRUCTURE]. "
            "Objectif : [OBJECTIF]. Méthodes : [MÉTHODES]. Ressource clé : [RESSOURCE_CLÉ]. Tabou : [TABOU]. "
            "Lieux d'influence : [LIEU]. Alliances/rivalités : [FACTION]. Décris un rite : [RITUEL]."
        ),
    },
}



