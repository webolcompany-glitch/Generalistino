import streamlit as st
import pandas as pd
import datetime

# Configurazione pagina
st.set_page_config(page_title="Generatore Listino", layout="wide")
st.title("📦 Generatore Listino da File Fornitore")

# --- Sidebar ---
st.sidebar.header("⚙️ Impostazioni listino")

markup_percent = st.sidebar.number_input(
    "📈 Ricarico percentuale (%)", min_value=0.0, max_value=500.0, value=70.0, step=0.5
)

fornitore = st.sidebar.selectbox("Seleziona fornitore", ["DFL", "Idealux"])
mercato = st.sidebar.selectbox(
    "Seleziona mercato di vendita",
    ["Italia", "Germania", "Francia", "Spagna", "Paesi Bassi", "Belgio"],
)

sigle_mercati = {
    "Italia": "IT",
    "Germania": "DE",
    "Francia": "FR",
    "Spagna": "ES",
    "Paesi Bassi": "NL",
    "Belgio": "BE",
}
sigla = sigle_mercati.get(mercato, "XX")

qta_min = 0
if fornitore == "Idealux":
    qta_min = st.sidebar.number_input("Quantità minima (Idealux)", min_value=0, value=1, step=1)

# --- Funzioni costo spedizione ---
def costo_spedizione_IT(peso):
    if peso <= 2:
        return 5.71
    elif peso <= 3:
        return 5.81
    elif peso <= 5:
        return 7.02
    elif peso <= 10:
        return 9.66
    elif peso <= 25:
        return 13.92
    elif peso <= 49:
        return 21.73
    return None

def costo_spedizione_DE(peso):
    if peso <= 1:
        return 8.97
    elif peso <= 2:
        return 9.86
    elif peso <= 3:
        return 10.74
    elif peso <= 5:
        return 11.72
    elif peso <= 10:
        return 13.03
    elif peso <= 15:
        return 15.02
    elif peso <= 20:
        return 16.90
    elif peso <= 25:
        return 21.09
    elif peso <= 30:
        return 22.98
    return None

def costo_spedizione_FR(peso):
    if peso <= 1:
        return 9.98
    elif peso <= 2:
        return 10.99
    elif peso <= 3:
        return 12.02
    elif peso <= 5:
        return 13.15
    elif peso <= 10:
        return 15.88
    elif peso <= 15:
        return 18.01
    elif peso <= 20:
        return 20.03
    elif peso <= 25:
        return 24.83
    elif peso <= 30:
        return 26.85
    return None

def costo_spedizione_NL(peso):
    if peso <= 1:
        return 9.26
    elif peso <= 2:
        return 10.16
    elif peso <= 3:
        return 12.02
    elif peso <= 5:
        return 12.11
    elif peso <= 10:
        return 13.97
    elif peso <= 15:
        return 16.68
    elif peso <= 20:
        return 19.34
    elif peso <= 25:
        return 23.61
    elif peso <= 30:
        return 26.27
    return None

def costo_spedizione_ES(peso):
    if peso <= 1:
        return 10.11
    elif peso <= 2:
        return 11.14
    elif peso <= 3:
        return 12.02
    elif peso <= 5:
        return 14.46
    elif peso <= 10:
        return 16.90
    elif peso <= 15:
        return 19.43
    elif peso <= 20:
        return 21.79
    elif peso <= 25:
        return 28.79
    elif peso <= 30:
        return 31.13
    return None

def costo_spedizione_BE(peso):
    if peso <= 1:
        return 10.72
    elif peso <= 2:
        return 11.77
    elif peso <= 3:
        return 12.82
    elif peso <= 5:
        return 14.01
    elif peso <= 10:
        return 15.87
    elif peso <= 15:
        return 18.62
    elif peso <= 20:
        return 21.28
    elif peso <= 25:
        return 26.22
    elif peso <= 30:
        return 28.88
    return None

spedizioni = {
    "Italia": (costo_spedizione_IT, "Free_it"),
    "Germania": (costo_spedizione_DE, "Free_de"),
    "Francia": (costo_spedizione_FR, "Free_fr"),
    "Paesi Bassi": (costo_spedizione_NL, "Free_nl"),
    "Spagna": (costo_spedizione_ES, "Free_es"),
    "Belgio": (costo_spedizione_BE, "Free_be"),
}

# --- Caricamento file ---
uploaded_file = st.file_uploader(
    f"📁 Carica il file del fornitore {fornitore} (.xlsx o .csv)", type=["xlsx", "csv"]
)

if uploaded_file:
    try:
        # Lettura file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, delimiter=";", encoding="utf-8")
        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ File caricato con successo!")
        st.subheader("📊 Dati originali (prime 20 righe)")
        st.dataframe(df.head(20), use_container_width=True)
        st.info(f"🔍 Ricarico selezionato: **{markup_percent:.2f}%**")

        # Normalizzazione dati per fornitore
        if fornitore == "DFL":
            totale_iniziale = len(df)
            # Escludo MV > 1
            df = df[df["MV"] <= 1]
            esclusi_mv = totale_iniziale - len(df)
            st.info(f"Esclusi {esclusi_mv} prodotti con MV > 1 per DFL.")

            # Filtro disponibilità per secondo file (lo applichiamo poi solo in aggiornamento)
            # ma qui lo usiamo per calcolare peso e altro
            df["PesoVolumetrico"] = (df["VolumeMt3"] * 1_000_000) / 5000
            df["PesoVolumetrico"].fillna(0, inplace=True)
            df["PesoPezzoKg"].fillna(0, inplace=True)
            df["PesoSpedizione"] = df[["PesoPezzoKg", "PesoVolumetrico"]].max(axis=1)

            cod_art = df["CodiceArticolo"].astype(str)
            prezzo_netto = df["PrezzoNetto"]
            barcode = df["Barcode"].astype(str)

        else:  # Idealux
            totale_iniziale = len(df)
            df = df.rename(
                columns={
                    "Nr": "CodiceArticolo",
                    "Prezzo netto": "PrezzoNetto",
                    "Peso Lordo": "PesoPezzoKg",
                    "Volume Scatola": "VolumeMt3",
                    "Magazzino": "Magazzino",
                    "Prezzo Al Pubblico": "PrezzoAlPubblico",
                }
            )
            # Escludo magazzino < qta_min
            df = df[df["Magazzino"] >= qta_min]
            esclusi_magazzino = totale_iniziale - len(df)
            st.info(f"Esclusi {esclusi_magazzino} prodotti con magazzino < {qta_min} per Idealux.")

            df["PesoVolumetrico"] = (df["VolumeMt3"] * 1_000_000) / 5000
            df["PesoVolumetrico"].fillna(0, inplace=True)
            df["PesoPezzoKg"].fillna(0, inplace=True)
            df["PesoSpedizione"] = df[["PesoPezzoKg", "PesoVolumetrico"]].max(axis=1)

            cod_art = df["CodiceArticolo"].astype(str)
            prezzo_netto = df["PrezzoNetto"]
            barcode = df["CodiceArticolo"].astype(str)

        # Calcolo costo spedizione e prezzo acquisto
        costo_sped_func, fulfillment_channel = spedizioni[mercato]
        df["CostoSpedizione"] = df["PesoSpedizione"].apply(costo_sped_func)

        # Prezzo finale (Idealux usa Prezzo Al Pubblico)
        if fornitore == "Idealux":
            # Usare "Prezzo Al Pubblico" come prezzo finale
            df["PrezzoAcquisto"] = df["PrezzoAlPubblico"]
        else:
            df["PrezzoAcquisto"] = prezzo_netto + df["CostoSpedizione"]

        moltiplicatore = 1 + (markup_percent / 100)
        oggi = datetime.datetime.now().strftime("%Y%m%d")

        # --- Listino completo Amazon (solo per Italia) ---
        if mercato == "Italia":
            totale_listino_iniziale = len(df)
            # Escludo prodotti con peso > 49 kg
            df_listino = df[df["PesoSpedizione"] <= 49].copy()
            esclusi_peso = totale_listino_iniziale - len(df_listino)
            st.info(f"Esclusi {esclusi_peso} prodotti con peso superiore a 49 kg per il listino Amazon IT.")

            # Filtro disponibilità per DFL
            if fornitore == "DFL":
                totale_listino_disp = len(df_listino)
                df_listino = df_listino[
                    ~df_listino["Disponibilita"].str.lower().isin(["non disponibile", "limitata"])
                ]
                esclusi_disponibilita = totale_listino_disp - len(df_listino)
                st.info(f"Esclusi {esclusi_disponibilita} prodotti non disponibili o con disponibilità limitata per DFL nel listino Amazon IT.")

            prezzo_acquisto_listino = df_listino["PrezzoAcquisto"] * moltiplicatore

            df_listino_output = pd.DataFrame()
            df_listino_output["SKU"] = (
                f"{fornitore}_"
                + cod_art.loc[df_listino.index].astype(str)
            )
            df_listino_output["Tipo di ID esterna del prodotto"] = "EAN"
            df_listino_output["ID esterna del prodotto"] = barcode.loc[df_listino.index]
            df_listino_output["Condizione dell'articolo"] = "Nuovo"
            df_listino_output["Gruppo spedizione venditore"] = "Spedizione Gratis"
            df_listino_output["Codice canale di gestione (IT)"] = "DEFAULT"
            df_listino_output["Quantità (IT)"] = 10 if fornitore == "DFL" else df_listino["Magazzino"]
            df_listino_output["Tempo di gestione (IT)"] = 1
            df_listino_output["Prezzo EUR (Vendita su Amazon, IT)"] = prezzo_acquisto_listino.round(2)

            st.subheader("📦 Listino completo Amazon (per mercato ITALIA)")
            st.dataframe(df_listino_output.head(20), use_container_width=True)

            file_name_listino = f"listino_{fornitore.lower()}_{sigla}_{oggi}.csv"
            csv_listino = df_listino_output.to_csv(index=False).encode("utf-8")

            st.download_button(
                "💾 Scarica Listino completo Amazon (IT)",
                data=csv_listino,
                file_name=file_name_listino,
                mime="text/csv",
            )

        # --- Aggiorna prezzi e quantità Amazon (tutti i mercati) ---
        df_aggiorna = df.copy()

        # Funzione quantità aggiornata con filtro disponibilità per DFL
        def get_quantity(row):
            if fornitore == "DFL":
                disponibile = str(row.get("Disponibilita", "")).strip().lower()
                if disponibile in ["non disponibile", "limitata"]:
                    return 0
                elif disponibile == "disponibile":
                    return 10
                else:
                    return 0
            else:  # Idealux
                try:
                    magazzino = int(row.get("Magazzino", 0))
                except:
                    magazzino = 0
                return magazzino if magazzino > 0 else 0

        df_aggiorna["Quantità_Aggiorna"] = df_aggiorna.apply(get_quantity, axis=1)

        totale_prodotti_agg = len(df_aggiorna)
        prodotti_disponibili = (df_aggiorna["Quantità_Aggiorna"] > 0).sum()
        prodotti_esclusi = totale_prodotti_agg - prodotti_disponibili

        st.info(f"Nel file aggiornamento: prodotti disponibili {prodotti_disponibili} su {totale_prodotti_agg}. Esclusi {prodotti_esclusi} per disponibilità o magazzino.")

        prezzo_acquisto_aggiorna = df_aggiorna["PrezzoAcquisto"] * moltiplicatore

        df_aggiorna_output = pd.DataFrame()
        df_aggiorna_output["SKU"] = (
            f"{fornitore}_"
            + cod_art.loc[df_aggiorna.index].astype(str)
        )
        df_aggiorna_output["price"] = prezzo_acquisto_aggiorna.round(2)
        df_aggiorna_output["minimum-seller-allowed-price"] = ""
        df_aggiorna_output["maximum-seller-allowed-price"] = ""
        df_aggiorna_output["quantity"] = df_aggiorna["Quantità_Aggiorna"]
        df_aggiorna_output["fulfillment-channel"] = fulfillment_channel
        df_aggiorna_output["handling-time"] = 1
        df_aggiorna_output["minimum_order_quantity_minimum"] = ""

        st.subheader("📦 Aggiorna prezzi e quantità Amazon")
        st.dataframe(df_aggiorna_output.head(20), use_container_width=True)

        file_name_aggiorna = f"aggiorna_{fornitore.lower()}_{sigla}_{oggi}.csv"
        csv_aggiorna = df_aggiorna_output.to_csv(index=False).encode("utf-8")

        st.download_button(
            "💾 Scarica Aggiorna prezzi e quantità Amazon",
            data=csv_aggiorna,
            file_name=file_name_aggiorna,
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"❌ Errore durante l'elaborazione del file: {e}")
else:
    st.info("📥 Carica un file per iniziare l'elaborazione.")
