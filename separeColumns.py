import pandas as pd

# Carica il database VCF in un DataFrame pandas
df = pd.read_csv("/Volumes/SSD/Tesi/DB/result/W3HH-AFA-I_result_2024-05-07_12_36_11.txt", sep="\t")  # Assicurati di impostare correttamente il separatore

for r in df["HGMD.hg38_multianno.txt"]:
    if r != ".":
        df

        # ! TODO




# Divide la colonna "HGMD.hg38_multianno.txt" in più colonne
df_split = df["HGMD.hg38_multianno.txt"].str.split(";", expand=True)

# Rimuovi il nome prima del "=" e mantieni solo il valore dopo "=" per ogni colonna
for col in df_split.columns:
    df_split[col] = df_split[col].str.split("=").str[1]

# Rinomina le colonne
new_columns = []
for col in df_split.columns:
    if isinstance(col, int):  # Verifica se il nome della colonna è un intero
        new_columns.append("unknown_" + str(col))  # Se è un intero, assegna un nome "unknown"
    else:
        new_columns.append(col.split("=")[0])

df_split.columns = new_columns

# Aggiungi "." nelle colonne mancanti per le righe che hanno solo "."
for col in df_split.columns:
    df_split[col] = df_split[col].fillna(".")

# Unisci il DataFrame originale con il DataFrame diviso
df = pd.concat([df, df_split], axis=1)

# Elimina la colonna originale "HGMD.hg38_multianno.txt"
df = df.drop(columns=["HGMD.hg38_multianno.txt"])

# Salva il DataFrame modificato
df.to_csv("nuovo_database.txt", sep="\t", index=False)  # Salva il nuovo database VCF con il separatore corretto

for r in df['unknown_10']:
    if r!=".": print(r)