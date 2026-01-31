# Assistant SQL GenAI Local

Ce projet est un assistant intelligent capable de transformer des questions en langage naturel (Français) en requêtes SQL exécutables. Il utilise un LLM local (**Ollama**) pour garantir la confidentialité des données.

## Architecture

- **Frontend :** Streamlit
- **Backend :** Python
- **Database :** SQLite (générée dynamiquement à partir de CSV)
- **AI Engine :** Ollama (CodeLlama) + LangChain

### 1. Prérequis
- Python 3.9+
- [Ollama](https://ollama.com) installé et lancé.
- Télécharger le modèle :
  ```bash
  ollama pull codellama

## 2. Installation
-   pip install -r requirements.txt

## 3. Lancement
-   python db_setup.py (pour créer la base de données)
-   streamlit run app.py

## Recommandations
- Définir le thème sur "Light" pour un rendu plus agréable

# Lien vers la demo
