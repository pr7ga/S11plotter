import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import numpy as np

st.title("Analisador de Antenas - S11 x Frequência")

# Upload do CSV
uploaded_file = st.file_uploader("Carregue um arquivo CSV", type=["csv"])

if uploaded_file is not None:
    # Lê o conteúdo do arquivo em memória
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    lines = content.splitlines()

    # Encontrar a linha "BEGIN"
    begin_index = None
    for i, line in enumerate(lines):
        if line.strip().upper() == "BEGIN":
            begin_index = i + 1
            break

    if begin_index is None:
        st.error("Não foi encontrada a seção BEGIN no arquivo.")
    else:
        # Ler os dados após "BEGIN"
        data_str = "\n".join(lines[begin_index:])
        df = pd.read_csv(StringIO(data_str), names=["Frequência (Hz)", "S11 (dB)"])

        # Converte colunas para numérico e elimina linhas inválidas
        df["Frequência (Hz)"] = pd.to_numeric(df["Frequência (Hz)"], errors="coerce")
        df["S11 (dB)"] = pd.to_numeric(df["S11 (dB)"], errors="coerce")
        df = df.dropna().reset_index(drop=True)

        if df.empty:
            st.error("Não foi possível carregar dados numéricos válidos do arquivo.")
        else:
            # Controles da interface
            min_freq = st.number_input("Frequência mínima (Hz)", value=float(df["Frequência (Hz)"].min()))
            max_freq = st.number_input("Frequência máxima (Hz)", value=float(df["Frequência (Hz)"].max()))
            min_s11 = st.number_input("S11 mínimo (dB)", value=float(df["S11 (dB)"].min()))
            max_s11 = st.number_input("S11 máximo (dB)", value=float(df["S11 (dB)"].max()))
            titulo = st.text_input("Título do gráfico", value="S11 em função da Frequência")

            # Filtra os dados
            df_filtrado = df[(df["Frequência (Hz)"] >= min_freq) & (df["Frequência (Hz)"] <= max_freq)]
            df_filtrado = df_filtrado[(df_filtrado["S11 (dB)"] >= min_s11) & (df_filtrado["S11 (dB)"] <= max_s11)]

            if df_filtrado.empty:
                st.warning("Nenhum dado encontrado com os filtros aplicados.")
            else:
                # Gráfico S11 x Frequência
                fig, ax = plt.subplots()
                ax.plot(df_filtrado["Frequência (Hz)"], df_filtrado["S11 (dB)"], label="S11")
                ax.axhline(-10, color="red", linestyle="--", label="-10 dB")
                ax.set_xlabel("Frequência (Hz)")
                ax.set_ylabel("S11 (dB)")
                ax.set_title(titulo)
                ax.legend()
                ax.grid(True)
                st.pyplot(fig)

                # Identificação de múltiplas bandas
                mask = df_filtrado["S11 (dB)"] <= -10
                bandas = []
                in_band = False
                f_start = None

                for i in range(len(df_filtrado)):
                    if mask.iloc[i] and not in_band:
                        # início de uma banda
                        in_band = True
                        f_start = df_filtrado["Frequência (Hz)"].iloc[i]
                    elif not mask.iloc[i] and in_band:
                        # fim da banda
                        in_band = False
                        f_end = df_filtrado["Frequência (Hz)"].iloc[i-1]
                        bandas.append((f_start, f_end))
                # Se terminou dentro de uma banda, fecha no último ponto
                if in_band:
                    f_end = df_filtrado["Frequência (Hz)"].iloc[-1]
                    bandas.append((f_start, f_end))

                if not bandas:
                    st.error("Não foi encontrada nenhuma faixa de frequência com S11 ≤ -10 dB.")
                else:
                    st.success("Faixas de ressonância encontradas:")
                    for i, (f1, f2) in enumerate(bandas, start=1):
                        bw = f2 - f1
                        st.write(f"**Banda {i}:** {bw/1e6:.3f} MHz (de {f1/1e6:.3f} MHz até {f2/1e6:.3f} MHz)")
