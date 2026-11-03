"""
Schémas Pydantic : le "contrat" de l'API.

- Les schémas d'entrée (…Create, …Update, …Input) valident ce que le client
  envoie : types, longueurs, valeurs autorisées. Une donnée invalide est
  rejetée en 422 avant même d'atteindre la logique métier.
- Les schémas de sortie (…View) choisissent les champs renvoyés : par
  exemple, password_hash n'est jamais exposé.
"""
