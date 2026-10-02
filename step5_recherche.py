import json
import numpy as np
from fastembed import TextEmbedding


MODELE = "sentence-transformers/all-MiniLM-L6-v2"  
# reprendre le modele de l'étape 3

# Charger les morceaux et leurs embeddings
with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

embeddings = np.load("embeddings.npy")
modele = TextEmbedding(MODELE)


def chercher(question, nombre=20):
    # Transformer la question en nombres, comme les morceaux
    vecteur_question = np.array(list(modele.embed([question])))[0]
    vecteur_question = vecteur_question / np.linalg.norm(vecteur_question)

    # Mesurer la proximité avec chaque morceau
    scores = embeddings @ vecteur_question

    # Garder les meilleurs
    meilleurs = np.argsort(scores)[::-1][:nombre]

    resultats = []
    for i in meilleurs:
        resultats.append((chunks[i], float(scores[i])))
    return resultats


question = input("Question (en anglais) : ")

for chunk, score in chercher(question):
    print()
    print(f"[score {score:.2f}] PMID {chunk['pmid']}")
    print(chunk["titre"])
    print(chunk["texte"][:300] + "...")