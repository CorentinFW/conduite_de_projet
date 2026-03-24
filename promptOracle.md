## RÔLE
Tu es un ingénieur logiciel senior et expert en NLP. Tu dois produire un code Python robuste, maintenable et testable.

## CONTEXTE
On construit un « oracle » qui transforme un texte utilisateur quelconque en une combinaison structurée : émotion(s) + confiance.
L’oracle doit rester généraliste (pas de logique câblée sur un domaine spécifique) et doit être modulable : la liste des émotions disponibles ainsi que les paramètres de confiance doivent être fournis par un fichier JSON externe.

## OBJECTIF
Écrire un module Python qui :
1) lit un fichier de configuration JSON décrivant les émotions disponibles et la manière d’exprimer la confiance,
2) prend en entrée un texte utilisateur (chaîne arbitraire),
3) renvoie une sortie structurée « émotion(s) + confiance » exploitable par un autre algorithme.

## CONTRAINTES (IMPÉRATIF)
- Ne code pas en dur la liste des émotions ni l’échelle de confiance : tout doit venir du JSON.
- La sortie DOIT être strictement conforme au schéma demandé ci-dessous (noms de champs, types, présence des champs).
- Le code DOIT gérer les cas ambigus : texte vide, texte hors-sujet, émotions multiples, absence d’émotion claire.
- Le code DOIT être modulaire (fonctions/classes séparées), lisible (noms explicites), et facilement extensible.
- Le code DOIT être déterministe si un paramètre `seed` est fourni (si tu utilises une part non déterministe, ce qui est déconseillé).
- Le code DOIT inclure une interface CLI simple.
- Le code NE DOIT PAS nécessiter d’accès réseau.
- Utilise uniquement la bibliothèque standard Python (sauf instruction contraire explicite dans la config).

## HYPOTHÈSES
- Le fichier JSON est fourni localement.
- L’algorithme de décision peut être heuristique (lexique, règles, pondérations), mais il doit être encapsulé et paramétrable via la config.

## ENTRÉES
1) Texte utilisateur (string) :
- peut contenir ponctuation, emojis, fautes, plusieurs phrases.
- peut être en français ou autre (le système doit être tolérant, sans garantir une couverture parfaite).

2) Chemin vers la config JSON (string).

## CONFIG JSON (À SUPPORTER)
Ton code doit accepter une config au moins équivalente à ce schéma (tu peux permettre des champs additionnels, mais ceux-ci doivent être ignorés proprement) :

```json
{
	"schema_version": "1.0",
	"emotions": [
		{
			"id": "joy",
			"label": "joie",
			"aliases": ["content", "heureux", "ravis"],
			"keywords": ["super", "génial", "merci"],
			"negations": ["pas", "jamais", "aucun"],
			"weight": 1.0
		}
	],
	"confidence": {
		"scale": "0_1",
		"min": 0.0,
		"max": 1.0,
		"calibration": {
			"base": 0.2,
			"per_keyword_hit": 0.15,
			"per_alias_hit": 0.20,
			"ambiguity_penalty": 0.25,
			"negation_penalty": 0.30,
			"max_emotions": 3
		}
	},
	"behavior": {
		"allow_multiple_emotions": true,
		"unknown_emotion_id": "unknown",
		"language_hint": "auto"
	}
}
```

## SORTIE (FORMAT STRICT)
Le résultat doit être un objet JSON sérialisable (dict) ayant EXACTEMENT ces champs racine (aucune clé racine additionnelle) :

```json
{
	"input": {
		"text": "...",
		"normalized_text": "..."
	},
	"result": {
		"emotions": [
			{
				"id": "...",
				"label": "...",
				"confidence": 0.0,
				"evidence": {
					"matched_keywords": ["..."],
					"matched_aliases": ["..."],
					"negation_detected": true
				}
			}
		],
		"primary_emotion_id": "...",
		"overall_confidence": 0.0,
		"notes": ["..."]
	},
	"meta": {
		"schema_version": "1.0",
		"config_path": "...",
		"timestamp_utc": "ISO-8601",
		"engine": "heuristic_v1"
	}
}
```

## RÈGLES DE SORTIE (IMPÉRATIF)
- `result.emotions` :
	- doit être triée par `confidence` décroissante.
	- taille <= `confidence.calibration.max_emotions` si ce champ existe.
	- si aucune émotion n’est détectée, retourne une émotion unique dont `id` vaut `behavior.unknown_emotion_id` (ou "unknown" par défaut) et une confiance faible.
- `primary_emotion_id` :
	- doit correspondre au premier élément de `result.emotions`.
- `overall_confidence` :
	- doit être un agrégat cohérent (ex. max ou moyenne pondérée) des confiances, et doit respecter les bornes de la config.
- Les champs `confidence` et `overall_confidence` doivent être des floats dans l’intervalle [`confidence.min`, `confidence.max`].
- `normalized_text` :
	- doit être une normalisation simple (minuscule, trim, espaces compressés). Ne supprime pas toute information.
- `timestamp_utc` :
	- format ISO-8601 en UTC (ex. "2026-03-24T12:34:56Z").

## EXIGENCES LOGICIELLES
- Architecture attendue (minimum) :
	- `ConfigLoader` : validation légère, valeurs par défaut, erreurs claires.
	- `TextNormalizer` : normalisation, détection naïve de négation.
	- `EmotionScorer` : scoring paramétrable à partir de la config.
	- `Oracle` : orchestration (input -> normalize -> score -> output).
	- `cli.py` ou `__main__` : exécution en ligne de commande.
- Gestion d’erreurs :
	- erreurs de config (fichier manquant, JSON invalide, champs manquants) => message explicite + code de retour non nul en CLI.
- Typage :
	- ajoute des annotations de types (typing) et, si utile, des `dataclasses`.
- Tests (si tu ajoutes des tests, reste minimal) :
	- au moins 3 cas : texte vide, émotion évidente, ambiguïté (deux émotions proches).

## ÉTAPES À SUIVRE
1) Définis le schéma interne (dataclasses) pour config et résultat.
2) Implémente le chargement et la validation légère de la config JSON.
3) Implémente la normalisation du texte et la détection simple de négation.
4) Implémente le scoring :
	 - compte les correspondances `keywords` et `aliases` (insensible à la casse),
	 - applique les pondérations et pénalités (ambiguïté, négation),
	 - borne la confiance selon `confidence.min/max`.
5) Sélectionne les top émotions selon `allow_multiple_emotions` et `max_emotions`.
6) Produis la sortie JSON strictement conforme.
7) Ajoute une CLI :
	 - `--config path/to/config.json`
	 - `--text "..."` (optionnel)
	 - si `--text` absent : lire depuis stdin.
	 - imprime la sortie JSON sur stdout (UTF-8), par exemple avec `json.dumps(..., ensure_ascii=False, indent=2)`.

## EXEMPLES (À RESPECTER)
Exemple A
Entrée texte: "Merci beaucoup, c’est génial !"
Sortie: émotions inclut `joy` (ou l’id correspondant), confiance > base, evidence montre les mots déclencheurs.

Exemple B
Entrée texte: "Je ne suis pas content."
Sortie: l’émotion positive doit être pénalisée si détectée, et une émotion négative (si présente en config) doit dominer.

Exemple C
Entrée texte: ""
Sortie: unknown + faible confiance, notes explique "empty_input".

## FORMAT DE SORTIE ATTENDU (IMPÉRATIF)
Retourne UNIQUEMENT :
1) l’arborescence de fichiers proposée (liste),
2) puis le contenu complet de chaque fichier (code),
sans texte supplémentaire.

Si tu produis un seul fichier, nomme-le `oracle.py` et inclue la CLI dedans.

