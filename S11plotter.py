import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

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
            # Controles
            min_freq = st.number_input("Frequência mínima (Hz)", value=float(df["Frequência (Hz)"].min()))
            max_freq = st.number_input("Frequência máxima (Hz)", value=float(df["Frequência (Hz)"].max()))
            min_s11 = st.number_input("S11 mínimo (dB)", value=float(df["S11 (dB)"].min()))
            max_s11 = st.number_input("S11 máximo (dB)", value=float(df["S11 (dB)"].max()))
            titulo = st.text_input("Título do gráfico", value="S11 em função da Frequência")

            df_filtrado = df[(df["Frequência (Hz)"] >= min_freq) & (df["Frequência (Hz)"] <= max_freq)]
            df_filtrado = df_filtrado[(df_filtrado["S11 (dB)"] >= min_s11) & (df_filtrado["S11 (dB)"] <= max_s11)]

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
                fig, ax = plt.subplots()
                ax.plot(df_filtrado["Frequência (Hz)"], df_filtrado["S11 (dB)"], label="S11")
                ax.axhline(-10, color="black", linestyle="--", label="-10 dB")

                # cores primárias fortes para cada banda
                cores = ["red", "blue", "green", "yellow", "cyan", "magenta", "orange", "purple"]

                for i, (f1, f2, f_res) in enumerate(bandas, start=1):
                    cor = cores[(i-1) % len(cores)]
                    bw_norm = (f2 - f1) / f_res * 100
                    largura = (f2 - f1)/1e6
                    ax.axvspan(f1, f2, color=cor, alpha=0.5,
                               label=(f"B{i}: {bw_norm:.1f}% BW | "
                                      f"{largura:.2f} MHz "
                                      f"({f1/1e6:.2f}-{f2/1e6:.2f} MHz) "
                                      f"Res: {f_res/1e6:.2f} MHz"))

                ax.set_xlabel("Frequência (Hz)")
                ax.set_ylabel("S11 (dB)")
                ax.set_title(titulo)
                ax.set_ylim(min_s11, max_s11)  # escala do gráfico definida pelo usuário
                ax.legend()
                ax.grid(True)
                st.pyplot(fig)

                # Tabela das bandas
                if bandas:
                    st.success("Faixas de ressonância encontradas:")
                    for i, (f1, f2, f_res) in enumerate(bandas, start=1):
                        bw_norm = (f2 - f1) / f_res * 100
                        st.write(
                            f"**Banda {i}:** {bw_norm:.2f}% BW "
                            f"(de {f1/1e6:.3f} a {f2/1e6:.3f} MHz) | "
                            f"Largura: {(f2-f1)/1e6:.2f} MHz | "
                            f"Ressonância: {f_res/1e6:.3f} MHz"
                        )
