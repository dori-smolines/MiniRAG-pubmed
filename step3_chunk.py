import json

# définir la taille max de chaque morceau
TAILLE_MAX = 1500  


def decouper_resume(resume, taille_max=TAILLE_MAX):
    # Conserver les résumés courts
    if len(resume) <= taille_max:
        return [resume]

    # Couper phrase par phrase les résumés longs
    phrases = resume.split(". ")
    morceaux = []
    courant = ""

    for phrase in phrases:
        if courant:
            candidat = courant + ". " + phrase
        else:
            candidat = phrase

        if len(candidat) > taille_max and courant:
            morceaux.append(courant + ".")
            courant = phrase
        else:
            courant = candidat

    if courant:
        morceaux.append(courant)

    return morceaux


# Charger le corpus
with open("corpus.json", "r", encoding="utf-8") as f:
    fiches = json.load(f)

# Fabriquer les morceaux
chunks = []
ignorees = 0
articles_coupes = 0

for fiche in fiches:
    resume = fiche["resume"].strip()

    if resume == "":
        ignorees += 1
        continue

    morceaux = decouper_resume(resume)
    if len(morceaux) > 1:
        articles_coupes += 1

    for numero, texte in enumerate(morceaux, start=1):
        chunks.append({
            "id": f"{fiche['pmid']}_{numero}",
            "pmid": fiche["pmid"],
            "titre": fiche["titre"],
            "reference": fiche["reference"],
            "texte": texte,
        })

# Sauvegarder
with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

# Creer un bilan chiffré
print(f"Fiches sans résumé (ignorées) : {ignorees}")
print(f"Articles coupés en plusieurs morceaux : {articles_coupes}")
print(f"Nombre total de morceaux : {len(chunks)}")
print(f"Plus long morceau : {max(len(c['texte']) for c in chunks)} caractères")