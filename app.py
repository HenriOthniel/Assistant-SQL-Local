import sqlite3
import pandas as pd
import streamlit as st

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(
    page_title="SQL GenAI Local",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE CSS ---
st.markdown("""
<style>
    /* Styles généraux pour ressembler à un site web */
    .main {
        background-color: #f8f9fa;
        padding: 20px;
    }
    
    /* Header de site web */
    .website-header {
        background: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        border-left: 5px solid #4a6fa5;
    }
    
    /* Titre principal */
    .main-title {
        color: #2c3e50;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    
    .subtitle {
        color: #7f8c8d;
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Cards modernes */
    .web-card {
        background: white;
        border-radius: 12px;
        padding: 1.8rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
        transition: transform 0.2s ease;
    }
    
    .web-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }
    
    .card-title {
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1.2rem;
        padding-bottom: 0.8rem;
        border-bottom: 2px solid #f1f3f5;
    }
    
    /* Boutons modernes */
    .stButton > button {
        background-color: #4a6fa5;
        color: white;
        border: none;
        padding: 0.8rem 1.8rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #3a5a80;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(74, 111, 165, 0.2);
    }
    
    /* Inputs style site web */
    .stTextInput > div > div > input {
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 0.9rem;
        font-size: 1rem;
        background-color: white;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4a6fa5;
        box-shadow: 0 0 0 3px rgba(74, 111, 165, 0.1);
        outline: none;
    }
    
    /* Textarea style moderne */
    .stTextArea > div > div > textarea {
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        background-color: white;
    }
    
    /* Sidebar style site web */
    section[data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #e9ecef;
    }
    
    .sidebar-title {
        color: #2c3e50;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f1f3f5;
    }
    
    /* Dataframes style */
    .dataframe {
        border-radius: 8px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        font-weight: 600;
        color: #2c3e50;
        font-size: 1rem;
    }
    
    /* Metrics et statuts */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        background-color: #e8f5e9;
        color: #2e7d32;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    
    /* Séparateurs */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e9ecef, transparent);
        margin: 1rem 0;
    }
    
    /* Code blocks */
    code {
        background-color: #f8f9fa;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        border: 1px solid #e9ecef;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    
    /* Alertes style site */
    .stAlert {
        border-radius: 8px;
        border: 1px solid;
    }
    
    .stSuccess {
        border-color: #c8e6c9;
    }
    
    .stError {
        border-color: #ffcdd2;
    }
    
    .stWarning {
        border-color: #fff3cd;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER DU SITE ---
st.markdown("""
<div class="website-header">
    <h1 class="main-title">Assistant Data SQL Local</h1>
    <h5 class="subtitle">Analysez vos données avec l'IA en langage naturel</h5>
</div>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
@st.cache_resource
def get_engine():
    db = SQLDatabase.from_uri("sqlite:///data_projet.db")
    schema = db.get_table_info()
    
    template = """
    Tu es un expert en Data Engineering et en requêtage SQL.
    Voici le schéma de la base de données :
    
    {schema}
    
    Tes instructions :
    - L'utilisateur parle en Français. Traduis les termes métier vers les noms de tables en Anglais.
        (Exemple : "Acteur" -> table 'actor', "Ville" -> table 'city').
    - Analyse les noms de colonnes pour trouver les liens.
        (Exemple : si tu vois 'actor_id' dans une table et 'id' dans la table 'actor', c'est une jointure).
    - Si la question nécessite plusieurs tables, fais un JOIN SQL standard.
    - Ignore la casse (majuscule/minuscule).
    - Réponds UNIQUEMENT le code SQL valide, sans explications, sans balises Markdown.
    
    Question utilisateur : {question}
    SQL Query :
    """
    
    prompt = PromptTemplate(
        input_variables=["question"],
        partial_variables={"schema": schema},
        template=template
    )
    
    llm = OllamaLLM(model="codellama", temperature=0)
    
    return llm, prompt

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<p class="sidebar-title">Navigation</p>', unsafe_allow_html=True)
    
    # Statut du système
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
        <p style="font-weight: 600; color: #2c3e50; margin-bottom: 0.5rem;">État du système</p>
        <span class="status-badge">● Connecté</span>
        <span class="status-badge">IA Active</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Tables disponibles
    try:
        conn = sqlite3.connect('data_projet.db')
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'", 
            conn
        )
        conn.close()
        
        st.markdown("**📊 Tables disponibles :**")
        for table in tables['name'].tolist():
            st.markdown(f"`{table}`")
    except:
        st.warning("Base non connectée")

# --- CONTENU PRINCIPAL ---

# Section Assistant IA
st.markdown("""
<div class="web-card">
    <div class="card-title">Assistant IA</div>
    <p style="color: #666; margin-bottom: 1.5rem;">Posez vos questions, l'assistant génère les requêtes SQL.</p>
</div>
""", unsafe_allow_html=True)

try:
    llm, prompt_template = get_engine()
except Exception as e:
    st.error("Erreur : Vérifiez que 'data_projet.db' existe bien (lancez db_setup.py).")

st.markdown('<h5 style="color: #2c3e50; margin-bottom: 10px;">Votre question</h5>', unsafe_allow_html=True)
question = st.text_input(
    "",
    placeholder="Ex : Combien d'acteurs y a-t-il ?",
    label_visibility="collapsed"
)

if question:
    with st.spinner("Analyse en cours..."):
        try:
            full_prompt = prompt_template.format(question=question)
            result = llm.invoke(full_prompt)
            result = result.strip()
            
            if result.upper().startswith("SELECT"):
                conn = sqlite3.connect('data_projet.db')
                query_result = pd.read_sql_query(result, conn)
                conn.close()

                if not query_result.empty:
                    st.success("Résultats trouvés :")
                    st.dataframe(query_result, hide_index=True)
                else:
                    st.warning("Aucun résultat trouvé.")
            
            else:
                st.error("Cette commande n'est pas autorisée !")

            with st.expander("Requête SQL générée"):
                st.code(result, language="sql")
                    
        except Exception as e:
            st.error(f"Erreur : {e}")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Section Console SQL
st.markdown("""
<div class="web-card">
    <div class="card-title">Console SQL</div>
    <p style="color: #666; margin-bottom: 1.5rem;">Exécutez directement vos requêtes SQL.</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<h5 style="color: #2c3e50; margin-bottom: 10px;">Console SQL</h5>', unsafe_allow_html=True)

with st.expander("Console SQL Manuelle (Cliquer pour ouvrir/fermer)"):
    st.caption("Espace réservé pour tester vos propres requêtes.")
    
    col_sql, col_action = st.columns([3, 1])
    
    with col_sql:
        user_sql = st.text_area("Écrire du SQL :", height=100, placeholder="SELECT * FROM stock WHERE...")
    
    with col_action:
        st.write("")
        st.write("")
        st.write("")
        run_btn = st.button("Exécuter SQL", key="btn_manual")

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

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 1.5rem; font-size: 0.9rem;">
    <p>© 2026 SQL GenAI Local | Powered by The Dream Team</p>
</div>
""", unsafe_allow_html=True)