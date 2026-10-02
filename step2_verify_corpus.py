import json

# 1. Charger le corpus
with open("corpus.json", "r", encoding="utf-8") as f:
    fiches = json.load(f)

print(f"Nombre de fiches : {len(fiches)}")
print()

# 2. Repérer les fiches incomplètes
sans_resume = []
sans_auteur = []
longueurs = []

for fiche in fiches:
    if fiche["resume"].strip() == "":
        sans_resume.append(fiche["pmid"])
    else:
        longueurs.append(len(fiche["resume"]))

    if len(fiche["auteurs"]) == 0:
        sans_auteur.append(fiche["pmid"])

print(f"Fiches sans résumé : {len(sans_resume)}")
if sans_resume:
    print(f"  PMID concernés : {', '.join(sans_resume)}")

print(f"Fiches sans auteur : {len(sans_auteur)}")
if sans_auteur:
    print(f"  PMID concernés : {', '.join(sans_auteur)}")
print()

# 3. Calculer les longueurs des résumés
if longueurs:
    moyenne = sum(longueurs) / len(longueurs)
    print("Longueur des résumés (en caractères) :")
    print(f"  plus court : {min(longueurs)}")
    print(f"  plus long  : {max(longueurs)}")
    print(f"  moyenne    : {moyenne:.0f}")
print()

# 4. Repérer les doublons : fiches aux PMID identiques
tous_les_pmid = [fiche["pmid"] for fiche in fiches]
nb_doublons = len(tous_les_pmid) - len(set(tous_les_pmid))
print(f"Doublons (même PMID) : {nb_doublons}")