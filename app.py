import streamlit as st
import pandas as pd
import sqlite3
from langchain_ollama import OllamaLLM
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_core.prompts import PromptTemplate

# --- CONFIGURATION ---
st.set_page_config(page_title="SQL GenAI Local", layout="wide")

st.title("🤖 Assistant Data SQL Local")
st.markdown("---")

# --- INITIALISATION DU MOTEUR (Caché pour la performance) ---
@st.cache_resource
def get_engine():
   # 1. Connexion à ta base générée par les CSV
    db = SQLDatabase.from_uri("sqlite:///data_projet.db")
    
    # 2. Récupération du schéma (La liste de toutes tes tables CSV)
    schema = db.get_table_info()
    
    # 3. Le Prompt "Sherlock Holmes" (Pour déduire les liens)
    # On explique à l'IA comment relier les CSV entre eux
    template = """
    Tu es un expert en Data Engineering et SQL.
    Voici le schéma de la base de données (généré à partir de fichiers CSV) :
    
    {schema}
    
    Tes instructions :
    1. L'utilisateur parle en Français. Traduis les termes métier vers les noms de tables en Anglais.
       (Ex: "Acteur" -> table 'actor', "Ville" -> table 'city').
    2. Analyse les noms de colonnes pour trouver les liens. 
       (Exemple : si tu vois 'actor_id' dans une table et 'id' dans une table 'actor', c'est une jointure).
    3. Si la question nécessite plusieurs tables, fais un JOIN SQL standard.
    4. Ignore la casse (majuscule/minuscule).
    5. Réponds UNIQUEMENT le code SQL valide, sans explications, sans balises Markdown.
    
    Question utilisateur : {question}
    SQL Query:
    """
    
    prompt = PromptTemplate(
        input_variables=["question"],
        partial_variables={"schema": schema},
        template=template
    )
    
    llm = OllamaLLM(model="codellama", temperature=0)
    
    return llm, prompt

try:
    llm, prompt_template = get_engine()
except Exception as e:
    st.error("Erreur : Vérifiez que 'data_projet.db' existe bien (lancez db_setup.py).")

# --- INTERFACE UTILISATEUR ---

st.subheader("💬 Discuter avec les données")
question = st.text_input("Votre question :", placeholder="Ex: Quel est le nombre d'acteurs ?")

if question:
    with st.spinner("L'IA analyse la base de données..."):
        try:
            # On utilise invoke pour obtenir toutes les étapes intermédiaires
            full_prompt = prompt_template.format(question=question)
            result = llm.invoke(full_prompt)
            result = result.strip()
            print(result)
            pos = result.find("SELECT")

            if pos == 0:
                # On ré-exécute manuellement pour être sûr d'afficher le tableau
                conn = sqlite3.connect('data_projet.db')
                query_result = pd.read_sql_query(result, conn)
                conn.close()

                if not query_result.empty:
                    # 1. Affichage de la réponse textuelle du LLM
                    st.success("Voici ce que j'ai trouvé :")
                    st.dataframe(query_result, hide_index=True)
                else:
                    st.warning("Aucun résultat trouvé.")
            
            else:
                st.error("L'éxécution de cette commande va altérer la base de données et nous n'avons pas ce droit !")

            with st.expander("Voir la requête SQL générée"):
                st.code(result, language="sql")
                    
        except Exception as e:
            st.error(f"Erreur : {e}")

st.markdown("---")

with st.expander("🛠️ Console SQL Manuelle (Cliquer pour ouvrir/fermer)"):
    st.caption("Espace réservé pour tester vos propres requêtes.")
    
    col_sql, col_action = st.columns([3, 1])
    
    with col_sql:
        user_sql = st.text_area("Écrire du SQL :", height=100, placeholder="SELECT * FROM stock WHERE...")
    
    with col_action:
        st.write("") # Petit espace pour aligner le bouton
        st.write("") 
        run_btn = st.button("▶️ Exécuter SQL", key="btn_manual")

    if run_btn and user_sql:
        try:
            conn = sqlite3.connect('data_projet.db')
            # Si c'est un SELECT -> Tableau
            if user_sql.strip().upper().startswith("SELECT"):
                df_manual = pd.read_sql_query(user_sql, conn)
                st.write(f"Résultats ({len(df_manual)} lignes) :")
                st.dataframe(df_manual, hide_index=True)
            # Sinon (UPDATE/INSERT) -> Message de succès
            else:
                cursor = conn.cursor()
                cursor.execute(user_sql)
                conn.commit()
                st.success(f"Action effectuée ! {cursor.rowcount} lignes modifiées.")
            conn.close()
        except Exception as e:
            st.error(f"Erreur SQL : {e}")

with st.expander("📊 Voir la liste des tables de la base de données"):
    if st.button("🔄 Rafraîchir le tableau"):
        conn = sqlite3.connect('data_projet.db')
        df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'", conn)
        st.dataframe(df, hide_index=True)
        conn.close()
