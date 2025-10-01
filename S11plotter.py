import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
from matplotlib.lines import Line2D

st.title("Analisador de Antenas - S11 x Frequência")

# Upload do CSV
uploaded_file = st.file_uploader("Carregue um arquivo CSV", type=["csv"])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    lines = content.splitlines()

    # Encontrar "BEGIN"
    begin_index = None
    for i, line in enumerate(lines):
        if line.strip().upper() == "BEGIN":
            begin_index = i + 1
            break

    if begin_index is None:
        st.error("Não foi encontrada a seção BEGIN no arquivo.")
    else:
        data_str = "\n".join(lines[begin_index:])
        df = pd.read_csv(StringIO(data_str), names=["Frequência (Hz)", "S11 (dB)"])
        df["Frequência (Hz)"] = pd.to_numeric(df["Frequência (Hz)"], errors="coerce")
        df["S11 (dB)"] = pd.to_numeric(df["S11 (dB)"], errors="coerce")
        df = df.dropna().reset_index(drop=True)

        if df.empty:
            st.error("Não foi possível carregar dados numéricos válidos do arquivo.")
        else:
            # Controles em uma única linha usando st.columns
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                min_freq_mhz = st.number_input(
                    "Frequência mínima (MHz)", 
                    value=float(df["Frequência (Hz)"].min()/1e6), step=0.1
                )
            with col2:
                max_freq_mhz = st.number_input(
                    "Frequência máxima (MHz)", 
                    value=float(df["Frequência (Hz)"].max()/1e6), step=0.1
                )
            with col3:
                min_s11 = st.number_input("S11 mínimo (dB)", value=float(df["S11 (dB)"].min()))
            with col4:
                max_s11 = st.number_input("S11 máximo (dB)", value=float(df["S11 (dB)"].max()))

            titulo = st.text_input("Título do gráfico", value="S11 em função da Frequência")

            # Filtrar dados
            df_filtrado = df[(df["Frequência (Hz)"] >= min_freq_mhz*1e6) & 
                             (df["Frequência (Hz)"] <= max_freq_mhz*1e6)]
            df_filtrado = df_filtrado[(df_filtrado["S11 (dB)"] >= min_s11) & 
                                      (df_filtrado["S11 (dB)"] <= max_s11)]

            if df_filtrado.empty:
                st.warning("Nenhum dado encontrado com os filtros aplicados.")
            else:
                # Identificação das bandas
                mask = df_filtrado["S11 (dB)"] <= -10
                bandas = []
                in_band = False
                f_start = None

                for i in range(len(df_filtrado)):
                    if mask.iloc[i] and not in_band:
                        in_band = True
                        f_start = df_filtrado["Frequência (Hz)"].iloc[i]
                    elif not mask.iloc[i] and in_band:
                        in_band = False
                        f_end = df_filtrado["Frequência (Hz)"].iloc[i-1]
                        sub_df = df_filtrado[(df_filtrado["Frequência (Hz)"] >= f_start) &
                                             (df_filtrado["Frequência (Hz)"] <= f_end)]
                        f_res = sub_df.loc[sub_df["S11 (dB)"].idxmin(), "Frequência (Hz)"]
                        bandas.append((f_start, f_end, f_res))
                if in_band:
                    f_end = df_filtrado["Frequência (Hz)"].iloc[-1]
                    sub_df = df_filtrado[(df_filtrado["Frequência (Hz)"] >= f_start) &
                                         (df_filtrado["Frequência (Hz)"] <= f_end)]
                    f_res = sub_df.loc[sub_df["S11 (dB)"].idxmin(), "Frequência (Hz)"]
                    bandas.append((f_start, f_end, f_res))

                # Gráfico
                fig, ax = plt.subplots(figsize=(10, 6))
                freq_mhz = df_filtrado["Frequência (Hz)"] / 1e6
                ax.plot(freq_mhz, df_filtrado["S11 (dB)"], color="blue", lw=2, label="S11")
                ax.axhline(-10, color="black", linestyle="--", lw=1, label="-10 dB")

                # cores primárias fortes para cada banda
                cores = ["red", "blue", "green", "yellow", "cyan", "magenta", "orange", "purple"]

                # Inserir sombreado e informações das bandas
                y_start = -0.15
                for idx, (f1, f2, f_res) in enumerate(bandas):
                    cor = cores[idx % len(cores)]
                    ax.axvspan(f1/1e6, f2/1e6, color=cor, alpha=0.5)

                    # Cálculo da largura e BW%
                    largura = (f2 - f1)/1e6
                    bw_norm = (f2 - f1) / f_res * 100

                    y_pos = y_start - idx*0.05

                    # "Res:" com fundo colorido
                    ax.text(0.02, y_pos, " ", fontsize=9, ha="left", va="center",
                            transform=ax.transAxes,
                            bbox=dict(facecolor=cor, edgecolor='none', alpha=0.5, boxstyle='round,pad=0.2'))



                    # restante do texto sem fundo
                    ax.text(0.03, y_pos,
                            f"Ressonância: {f_res/1e6:.2f} MHz, BW: {largura:.2f} MHz ({f1/1e6:.1f} a {f2/1e6:.1f} MHz, {bw_norm:.1f}%)",
                            fontsize=9, ha="left", va="center", transform=ax.transAxes)

                ax.set_xlabel("Frequência (MHz)")
                ax.set_ylabel("S11 (dB)")
                ax.set_title(titulo)
                ax.set_ylim(min_s11, max_s11)
                ax.grid(True)

                # Legenda apenas S11 e -10 dB
                legend_elements = [
                    Line2D([0], [0], color='blue', lw=2, label='S11'),
                    Line2D([0], [0], color='black', lw=1, linestyle='--', label='-10 dB')
                ]
                ax.legend(handles=legend_elements, loc='upper right')

                st.pyplot(fig)
