import streamlit as st
import pandas as pd
import io
from datetime import date
from database_utils import run_select

# Mapeamento de laudos por unidade
UNIDADES_LAUDOS = {
    "Ceres": {
        "Água": "tb_ceres_agua",
        "Calcário": "tb_ceres_calcario",
        "Composto Orgânico": "tb_ceres_composto_organico",
        "Fertilizante": "tb_ceres_fertilizante",
        "Folha": "tb_ceres_folha_str",
        "Solo": "tb_ceres_solo"
    },
    "Patrocínio": {
        "Água": "tb_patrocinio_agua",
        "Calcário": "tb_patrocinio_calcario",
        "Folha": "tb_patrocinio_folha",
        "Solo": "tb_patrocinio_solo"
    },
    "Croplab": {
        "Água": "tb_croplab_agua",
        "Composto Orgânico": "tb_croplab_composto_organico",
        "Fertilizante": "tb_croplab_fertilizante",
        "Solo": "tb_croplab_solo"
    }
}

# ---------------------- 🚀 Funções Otimizadas 🚀 ----------------------


@st.cache_data
def consultar_dados(tabela_laudo, data_inicio, data_fim):
    """Executa a consulta SQL considerando o filtro de data."""
    sql = f"SELECT * FROM {tabela_laudo} WHERE entrada BETWEEN '{data_inicio}' AND '{data_fim}' ORDER BY entrada DESC"
    return run_select(sql)


def gerar_excel(df):
    """Cria um arquivo Excel na memória."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Laudo")
    output.seek(0)
    return output

# ---------------------- 🎯 Interface Profissional 🎯 ----------------------


def main():
    st.set_page_config(page_title="Exportação de Laudos", layout="wide")
    st.title("📤 Exportação de Laudos Agrícolas")

    # 🔹 Seleção da Unidade e Tipo de Laudo
    col1, col2 = st.columns(2)
    with col1:
        unidade_selecionada = st.selectbox(
            "📍 Selecione a unidade", list(UNIDADES_LAUDOS.keys()))
    with col2:
        laudo_selecionado = st.selectbox("📑 Selecione o tipo de laudo", list(
            UNIDADES_LAUDOS[unidade_selecionada].keys()))

    # Definir a tabela
    tabela_laudo = UNIDADES_LAUDOS[unidade_selecionada][laudo_selecionado]

    # 🔹 Filtro de Data (Intervalo)
    col3, col4 = st.columns(2)
    with col3:
        data_inicio = st.date_input("📅 Data Inicial", value=date(2020, 1, 1))
    with col4:
        data_fim = st.date_input("📅 Data Final", value=date.today())

    # Configurar paginação
    registros_por_pagina = st.slider("📊 Registros por página", 10, 100, 20)

    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = 1  # Iniciar na primeira página

    # Botão para carregar os dados
    if st.button("🔍 Buscar Dados"):
        try:
            df_laudo = consultar_dados(tabela_laudo, data_inicio, data_fim)

            if df_laudo.empty:
                st.warning(
                    "⚠️ Nenhum registro encontrado para o período selecionado.")
            else:
                st.write(
                    f"📌 **{len(df_laudo)} registros encontrados** no período de **{data_inicio} a {data_fim}**.")

                # 🔹 Paginação
                # Calcula total de páginas
                total_paginas = max(
                    1, -(-len(df_laudo) // registros_por_pagina))

                # Botões de paginação
                col_pag1, col_pag2, col_pag3 = st.columns([1, 3, 1])
                with col_pag1:
                    if st.button("⬅️ Anterior") and st.session_state.pagina_atual > 1:
                        st.session_state.pagina_atual -= 1
                with col_pag3:
                    if st.button("➡️ Próxima") and st.session_state.pagina_atual < total_paginas:
                        st.session_state.pagina_atual += 1

                # Exibir registros da página atual
                inicio = (st.session_state.pagina_atual - 1) * \
                    registros_por_pagina
                fim = inicio + registros_por_pagina
                df_paginado = df_laudo.iloc[inicio:fim]

                st.write(
                    f"📌 Página **{st.session_state.pagina_atual} de {total_paginas}** | Exibindo registros **{inicio+1} a {min(fim, len(df_laudo))}**")
                st.dataframe(df_paginado, use_container_width=True, height=400)

                # 🔹 Exportação para Excel
                st.markdown("---")
                st.subheader("📥 Exportação para Excel")

                excel_bytes = gerar_excel(df_laudo)
                st.download_button(
                    label="📥 Baixar Arquivo Excel",
                    data=excel_bytes,
                    file_name=f"{laudo_selecionado}_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as e:
            st.error(f"⚠️ Erro ao carregar os dados: {e}")


if __name__ == "__main__":
    main()
