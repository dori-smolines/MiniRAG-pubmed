# RAG PubMed — Recherche sémantique dans la littérature scientifique

Système de recherche par le sens (RAG — *Retrieval-Augmented Generation*, volet *Retrieval*) sur des articles PubMed. On interroge le corpus en langage naturel et on retrouve les passages les plus proches en sens, chacun rattaché à son article d'origine par son PMID.

Projet personnel réalisé en parallèle de ma formation à l'École 42.

## Pipeline

```
step1_pubmed_extract.py   →  corpus.json
step2_verify_corpus.py    →  contrôle qualité (lecture seule)
step3_chunk.py             →  chunks.json
step4_embeddings.py        →  embeddings.npy
step5_recherche.py         →  recherche interactive
```

## Prérequis

```bash
pip install biopython fastembed numpy
```

`fastembed` a été choisi pour calculer les embeddings

---

## step1_pubmed_extract.py

**Ce qu'il fait**
Interroge l'API PubMed/NCBI, récupère les articles correspondant à une
recherche, et en extrait une fiche structurée par article : référence,
titre, auteurs, résumé, PMID. Sauvegarde le tout dans `corpus.json`.

**Comment l'utiliser**
```bash
python3 step1_pubmed_extract.py
```
Modifier au besoin, en haut du fichier :
- `Entrez.email` : adresse à renseigner (exigée par NCBI pour vous contacter en cas de problème)
- le terme de recherche et `nombre_max`, dans l'appel `rechercher_pubmed(...)`

Produit `corpus.json` dans le dossier courant. Affiche le nombre
d'identifiants trouvés puis le nombre de fiches sauvegardées.

**Choix techniques**
- **XML plutôt que texte brut** (`retmode="xml"`) : PubMed peut renvoyer les
  résumés en texte brut ou en XML structuré. Le XML fournit des champs déjà
  identifiés (titre, auteurs, résumé...), donc pas besoin de deviner où
  commence et où finit chaque information — contrairement au texte brut, où
  cette limite est ambiguë.
- **Extraction plutôt que nettoyage** : le script construit une fiche
  complète pour chaque article plutôt que de simplement nettoyer un texte,
  afin de préserver les métadonnées bibliographiques (auteurs, revue,
  année), indispensables pour citer une source.
- **Gestion des champs manquants** : certains articles n'ont pas de résumé
  ou pas d'auteur renseigné dans PubMed. Le script vérifie leur présence
  (`if "Abstract" in infos`, `infos.get("AuthorList", [])`) plutôt que de
  supposer qu'ils existent toujours, ce qui évite un plantage sur un article
  incomplet.
- **Année de publication à deux emplacements possibles** : PubMed la range
  tantôt sous `Year`, tantôt sous `MedlineDate`, selon l'article. Le script
  essaie les deux (`date.get("Year", date.get("MedlineDate", ""))`).

---

## step2_verify_corpus.py

**Ce qu'il fait**
Relit `corpus.json` et produit un bilan de qualité : nombre de fiches sans
résumé, sans auteur, longueur des résumés (min / max / moyenne), et nombre
de doublons (même PMID). Ne modifie aucun fichier.

**Comment l'utiliser**
```bash
python3 step2_verify_corpus.py
```
À exécuter après `step1_pubmed_extract.py`, dans le même dossier que
`corpus.json`.

**Choix techniques**
- **Contrôle avant transformation** : un RAG ne vaut que ce que vaut son
  corpus. Ce contrôle qualité est fait avant le chunking pour identifier tôt
  les fiches inexploitables (sans résumé) plutôt que de les découvrir après
  coup, une fois mélangées aux morceaux valides.
- **Les fiches incomplètes ne sont pas supprimées** de `corpus.json` : le
  script ne fait que les recenser. La décision de les garder ou de les
  écarter revient à l'étape suivante (chunking).
- **Détection des doublons par ensemble** (`set(...)`) : convertir la liste
  des PMID en ensemble supprime les répétitions ; comparer les deux
  longueurs donne le nombre de doublons en une ligne.

---

## step3_chunk.py

**Ce qu'il fait**
Découpe chaque résumé de `corpus.json` en un ou plusieurs morceaux
(*chunks*), chacun gardant le PMID, le titre et la référence de son article
d'origine. Sauvegarde le résultat dans `chunks.json` et affiche un bilan
(fiches ignorées, articles coupés, nombre total de morceaux, taille du plus
long).

**Comment l'utiliser**
```bash
python3 step3_chunk.py
```
À exécuter après `step2_verify_corpus.py` (ou directement après l'étape 1),
dans le même dossier que `corpus.json`.

**Choix techniques**
- **Un résumé court reste un seul morceau** : la limite `TAILLE_MAX = 1500`
  caractères correspond à la longueur moyenne observée des résumés PubMed du
  corpus. La plupart des résumés tiennent donc en un seul morceau, évitant un
  découpage inutile qui fragmenterait des idées cohérentes.
- **Découpage phrase par phrase, jamais au milieu d'une phrase**
  (`resume.split(". ")`) : les morceaux longs sont coupés sur des frontières
  de phrases, pour préserver le sens de chaque fragment. Limite connue : une
  abréviation comme « et al. » peut provoquer une coupure au mauvais endroit,
  ce cas n'étant pas géré spécifiquement.
- **Accumulation progressive** (`courant` + `candidat`) : chaque phrase est
  ajoutée au morceau en cours tant que la limite de taille n'est pas
  dépassée ; dès qu'elle le serait, le morceau en cours est clos et un
  nouveau commence. Ça garantit qu'aucun morceau ne dépasse `TAILLE_MAX`.
- **Fiches sans résumé ignorées** (`if resume == "": continue`) : cohérent
  avec le contrôle qualité de l'étape 2, ces fiches ne peuvent produire aucun
  morceau exploitable et sont exclues de `chunks.json`, sans pour autant être
  supprimées de `corpus.json`.
- **Identifiant composite** (`f"{pmid}_{numero}"`) : chaque morceau garde une
  trace explicite de sa position dans l'article d'origine (par exemple
  `12345678_2` pour le deuxième morceau de l'article 12345678), utile pour
  retrouver l'ordre des morceaux d'un même article si besoin.

---

## step4_embeddings.py

**Ce qu'il fait**
Charge `chunks.json`, calcule un embedding (une représentation numérique du
sens) pour chaque morceau de texte, et sauvegarde l'ensemble dans
`embeddings.npy`.

**Comment l'utiliser**
```bash
python3 step4_embeddings.py
```
À exécuter après `step3_chunk.py`, une fois `chunks.json` disponible.
Le modèle est téléchargé automatiquement au premier lancement (~90 Mo).

**Choix techniques**
- **Modèle local (`all-MiniLM-L6-v2`) plutôt qu'une API payante** : les
  embeddings sont calculés sur la machine, sans clé d'API ni coût, avec un
  modèle compact (384 dimensions) suffisant pour un corpus de cette taille.
- **`fastembed` plutôt que `sentence-transformers`** : même modèle, mais
  sans la dépendance à PyTorch, pour rester léger en espace disque.
- **Titre concaténé au texte du morceau** (`titre + ". " + texte`) : le
  titre apporte du contexte utile, en particulier pour les morceaux courts
  ou ambigus pris isolément.
- **Normalisation des vecteurs** (`embeddings / np.linalg.norm(...)`) :
  ramène tous les embeddings à la même longueur, condition nécessaire pour
  que la comparaison par produit scalaire (étape suivante) reflète
  uniquement une proximité de sens, pas une différence de longueur de texte.
- **L'ordre des morceaux dans `chunks.json` doit correspondre à l'ordre des
  lignes dans `embeddings.npy`** : le fichier n'associe pas explicitement
  chaque embedding à son PMID, cette correspondance se fait uniquement par
  position. Ne pas modifier l'un sans régénérer l'autre.

---

## step5_recherche.py

**Ce qu'il fait**
Pose une question en langage naturel (en anglais) et affiche les morceaux
de `chunks.json` les plus proches en sens, avec leur score de similarité et
leur PMID.

**Comment l'utiliser**
```bash
python3 step5_recherche.py
```
À exécuter après `step4_embeddings.py`, une fois `embeddings.npy`
disponible. Le script demande une question au clavier et affiche les 20
meilleurs résultats.

**Choix techniques**
- **Similarité cosinus via produit scalaire** (`embeddings @ vecteur_question`) :
  comme tous les vecteurs sont déjà normalisés (étape 4), un simple produit
  matriciel donne directement un score de proximité entre -1 et 1 pour
  chacun des morceaux, en une seule opération plutôt qu'en boucle.
- **Tri par score décroissant** (`np.argsort(scores)[::-1]`) : `argsort`
  trie du plus petit au plus grand score ; `[::-1]` inverse l'ordre pour
  faire remonter les morceaux les plus pertinents en premier.
- **Même modèle qu'à l'étape 4, obligatoirement** : deux modèles différents
  ne produisent pas des nombres comparables entre eux. Le nom du modèle est
  dupliqué en haut du fichier pour rester cohérent avec `step4_embeddings.py`.
- **Nombre de résultats réglable** (`nombre=20` par défaut, dans
  `chercher(question, nombre=...)`) : utile pour évaluer la position du bon
  article dans le classement plutôt que de ne voir que les tout premiers
  résultats.

---

## Limites connues et pistes d'évolution

- **Pas d'étape de génération** : le pipeline retrouve des extraits
  pertinents, mais ne rédige pas encore de réponse. Une prochaine étape
  consisterait à transmettre les meilleurs morceaux à un LLM (SDK Anthropic)
  avec une consigne de citation stricte des PMID.
- **Pas d'évaluation automatisée** : la pertinence des résultats est vérifiée
  manuellement. Un jeu de questions à réponse connue permettrait de mesurer
  objectivement la qualité de la recherche.
- **Découpage des phrases naïf** : `step3_chunk.py` coupe sur `". "`, ce qui
  peut mal gérer certaines abréviations (`et al.`).
