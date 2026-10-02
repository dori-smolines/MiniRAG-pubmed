from Bio import Entrez
import json

Entrez.email = "enter-your-email-here"

def rechercher_pubmed(mot_cle, nombre_max=100):
    handle = Entrez.esearch(db="pubmed", term=mot_cle, retmax=nombre_max)
    resultats = Entrez.read(handle)
    handle.close()
    return resultats["IdList"]

def recuperer_articles(liste_ids):
    handle = Entrez.efetch(db="pubmed", id=liste_ids, retmode="xml")
    donnees = Entrez.read(handle)
    handle.close()
    return donnees["PubmedArticle"]

def extraire_fiche(article):
    citation = article["MedlineCitation"]
    infos = citation["Article"]

    pmid = str(citation["PMID"])
    titre = str(infos["ArticleTitle"])

    auteurs = []
    for auteur in infos.get("AuthorList", []):
        nom = f"{auteur.get('ForeName', '')} {auteur.get('LastName', '')}".strip()
        if nom:
            auteurs.append(nom)

    if "Abstract" in infos:
        resume = " ".join(str(p) for p in infos["Abstract"]["AbstractText"])
    else:
        resume = ""

    revue = str(infos["Journal"]["Title"])
    date = infos["Journal"]["JournalIssue"]["PubDate"]
    annee = str(date.get("Year", date.get("MedlineDate", "")))

    reference = f"{', '.join(auteurs[:3])} ({annee}). {titre}. {revue}."

    return {
        "reference": reference,
        "titre": titre,
        "auteurs": auteurs,
        "resume": resume,
        "pmid": pmid,
    }

ids = rechercher_pubmed("Child, Gifted AND hasabstract[text]", nombre_max=1000)
print(f"{len(ids)} identifiants trouvés")

articles = recuperer_articles(ids)
fiches = [extraire_fiche(a) for a in articles]

with open("corpus.json", "w", encoding="utf-8") as f:
    json.dump(fiches, f, ensure_ascii=False, indent=2)

print(f"{len(fiches)} fiches sauvegardées dans corpus.json")


