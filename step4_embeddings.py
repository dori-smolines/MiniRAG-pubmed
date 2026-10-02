import json
import numpy as np
from fastembed import TextEmbedding

MODELE = "sentence-transformers/all-MiniLM-L6-v2"

# Charger les morceaux
with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"{len(chunks)} morceaux chargés")

# Préparer les textes : titre + texte du morceau
textes = []
for chunk in chunks:
    textes.append(chunk["titre"] + ". " + chunk["texte"])

# Charger le modèle 
modele = TextEmbedding(MODELE)

# Calculer les embeddings
embeddings = np.array(list(modele.embed(textes)))

# Normaliser (tous les vecteurs à la même longueur)
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

print(f"Forme du tableau : {embeddings.shape}")

# Sauvegarder
np.save("embeddings.npy", embeddings)
print("Embeddings sauvegardés dans embeddings.npy")