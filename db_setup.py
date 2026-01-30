import sqlite3
import pandas as pd
import os

def init_db():
    # Connexion (crée le fichier s'il n'existe pas)
    conn = sqlite3.connect('data_projet.db')
    cursor = conn.cursor()
    
    # Suppression pour repartir à zéro (optionnel, utile pour les tests)
    cursor.execute('DROP TABLE IF EXISTS stock')
    
    csv_folder = "data"

    for file in os.listdir(csv_folder):
        if file.endswith(".csv"):
            table_name = file.replace(".csv", "")
            file_path = os.path.join(csv_folder, file)

            print(f"Import du fichier : {file} → table '{table_name}'")

            df = pd.read_csv(file_path)

            df.to_sql(
                name=table_name,
                con=conn,
                if_exists="replace",
                index=False
            )
    
    conn.commit()
    conn.close()
    print("✅ Base de données 'data_projet.db' créée avec succès !")

if __name__ == "__main__":
    init_db()