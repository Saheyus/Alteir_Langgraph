"""Constants used by the Streamlit application."""

MODELS = {
    "GPT-5": {
        "name": "gpt-5",
        "provider": "OpenAI",
        "description": "Modèle le plus puissant, raisonnement approfondi",
        "max_tokens": 4000,
        "icon": "🚀",
        "uses_reasoning": True,
        "default_reasoning": "medium",
    },
    "GPT-5-mini": {
        "name": "gpt-5-mini",
        "provider": "OpenAI",
        "description": "Équilibré entre performance et coût",
        "max_tokens": 3000,
        "icon": "⚡",
        "uses_reasoning": True,
        "default_reasoning": "low",
    },
    "GPT-5-nano": {
        "name": "gpt-5-nano",
        "provider": "OpenAI",
        "description": "Rapide et économique, idéal pour itérations",
        "max_tokens": 2000,
        "icon": "✨",
        "uses_reasoning": True,
        "default_reasoning": "minimal",
    },
    "GPT-4o-mini": {
        "name": "gpt-4o-mini",
        "provider": "OpenAI",
        "description": "Modèle de fallback stable",
        "max_tokens": 2000,
        "icon": "🔄",
        "uses_reasoning": False,
    },
}

DOMAIN_HEADERS = {
    "Personnages": "Créer un Personnage",
    "Lieux": "Créer un Lieu",
}

DOMAIN_ICONS = {
    "Personnages": "👤",
    "Lieux": "🏛️",
}

BRIEF_PLACEHOLDERS = {
    "Personnages": "Ex: Un alchimiste qui transforme les émotions en substances physiques...",
    "Lieux": "Ex: Une bibliothèque souterraine dont les livres murmurent...",
}

BRIEF_EXAMPLES = {
    "Personnages": [
        "Un alchimiste qui transforme les émotions en substances physiques. Genre: Non défini. Espèce: Humain modifié. Âge: 38 cycles. Membre d'une guilde secrète, cache une dépendance à ses propres créations.",
        "Un cartographe solitaire membre d'un culte cherchant des ossements divins. Genre: Féminin. Espèce: Humaine. Âge: 45 cycles. Porte un compas en os qui vibre près des reliques.",
        "Un marchand d'ombres qui vend des souvenirs oubliés. Genre: Non binaire. Espèce: Gedroth. Âge: 102 cycles. Ancien bibliothécaire devenu contrebandier de mémoires interdites.",
        "Une chasseuse de primes cybernétique traquant son propre créateur. Genre: Féminin. Espèce: Hybride mécanique. Âge: 28 cycles. Recherche la vérité sur ses origines.",
        "Un barde aveugle qui voit les émotions comme des couleurs. Genre: Masculin. Espèce: Humain. Âge: 34 cycles. Autrefois peintre célèbre, maintenant musicien errant.",
        "Une archéologue obsédée par une civilisation disparue dont elle rêve chaque nuit. Genre: Féminin. Espèce: Humaine modifiée. Âge: 41 cycles. Collectionne des artefacts qui lui causent des visions.",
        "Un escargot cyberpunk touche-à-tout géotrouvetout et amateur d'art. Genre: Non défini. Espèce: Escargot modifié. Âge: 27 cycles. Rêve de créer une galerie underground.",
        "Un ancien soldat reconverti en chef cuisinier utilisant des ingrédients interdits. Genre: Masculin. Espèce: Humain. Âge: 52 cycles. Ses plats réveillent des souvenirs enfouis.",
    ],
    "Lieux": [
        "Une bibliothèque souterraine abandonnée dont les livres murmurent. Taille: Site. Rôle: Lieu de culte. Autrefois lieu de savoir, maintenant repaire de cultistes.",
        "Un marché flottant sur des plateformes organiques qui respirent. Taille: Secteur. Rôle: Lieu commercial. Construit sur le dos d'une créature endormie.",
        "Les ruines d'une station de purification d'eau devenue sanctuaire. Taille: Point d'intérêt. Rôle: Zone magique. L'eau y coule encore, mais transforme ce qu'elle touche.",
        "Un quartier vertical dans les entrailles d'un Léviathan pétrifié. Taille: District. Rôle: Ville. Sept niveaux de habitations creusées dans l'os ancien.",
        "Une forge maudite où les armes forgées pleurent. Taille: Site. Rôle: Lieu artisanal. Les artisans y travaillent avec des masques pour ne pas entendre.",
        "Un jardin suspendu où poussent des souvenirs cristallisés. Taille: Site. Rôle: Zone naturelle. Entretenu par des jardiniers aveugles qui récoltent les rêves.",
        "Une gare abandonnée devenue labyrinthe de rails fantômes. Taille: Secteur. Rôle: Lieu unique. Des trains spectraux y passent encore certaines nuits.",
    ],
}

INTENT_OPTIONS = {
    "Personnages": ["orthogonal_depth", "vocation_pure", "archetype_assume", "mystere_non_resolu"],
    "Lieux": ["hub_central", "passage_obligé", "zone_exploration", "lieu_secret"],
}

LEVEL_OPTIONS = {
    "Personnages": ["cameo", "standard", "major"],
    "Lieux": ["point_interet", "site", "secteur", "district"],
}

DIALOGUE_OPTIONS = {
    "Personnages": ["parle", "gestuel", "telepathique", "ecrit_only"],
}

ATMOSPHERE_OPTIONS = {
    "Lieux": ["oppressante", "vivante", "sacrée", "hostile", "accueillante", "neutre"],
}

PROFILE_CONFIGS = {
    "Lieux": {
        "Hub central": {
            "intent": "hub_central",
            "level": "district",
            "atmosphere": "vivante",
            "creativity": 0.75,
            "description": "Lieu de convergence, plein de vie et d'activités",
        },
        "Zone d'exploration": {
            "intent": "zone_exploration",
            "level": "secteur",
            "atmosphere": "neutre",
            "creativity": 0.70,
            "description": "Zone à découvrir, secrets et opportunités",
        },
        "Passage obligé": {
            "intent": "passage_obligé",
            "level": "site",
            "atmosphere": "hostile",
            "creativity": 0.65,
            "description": "Lieu de transit, dangers potentiels",
        },
        "Lieu secret": {
            "intent": "lieu_secret",
            "level": "point_interet",
            "atmosphere": "oppressante",
            "creativity": 0.80,
            "description": "Caché, découverte importante",
        },
        "Sanctuaire": {
            "intent": "lieu_secret",
            "level": "site",
            "atmosphere": "sacrée",
            "creativity": 0.85,
            "description": "Lieu de culte ou protection, ambiance spirituelle",
        },
    },
    "Personnages": {
        "Personnage principal": {
            "intent": "orthogonal_depth",
            "level": "major",
            "dialogue_mode": "parle",
            "creativity": 0.75,
            "description": "Profondeur maximale, 10-12 répliques, 2-4 relations",
        },
        "PNJ secondaire": {
            "intent": "orthogonal_depth",
            "level": "standard",
            "dialogue_mode": "parle",
            "creativity": 0.70,
            "description": "Profondeur moyenne, 8-10 répliques, 1-3 relations",
        },
        "Cameo/Figurant": {
            "intent": "mystere_non_resolu",
            "level": "cameo",
            "dialogue_mode": "parle",
            "creativity": 0.65,
            "description": "Présence minimale, 4-6 répliques, 0-1 relation",
        },
        "Boss/Antagoniste": {
            "intent": "archetype_assume",
            "level": "major",
            "dialogue_mode": "parle",
            "creativity": 0.80,
            "description": "Archétype assumé, profondeur maximale",
        },
        "Personnage mystérieux": {
            "intent": "mystere_non_resolu",
            "level": "standard",
            "dialogue_mode": "gestuel",
            "creativity": 0.85,
            "description": "Zones d'ombre, communication non-verbale",
        },
    },
}
