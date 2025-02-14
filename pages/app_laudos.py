import streamlit as st
from datetime import date
from database_utils import run_select

# Dicionário que mapeia as unidades e seus respectivos laudos
UNIDADES_LAUDOS = {
    "Ceres": {
        "Água": "tb_ceres_agua",
        "Calcário": "tb_ceres_calcario",
        "Composto Orgânico": "tb_ceres_composto_organico",
        "Fertilizante": "tb_ceres_fertilizante",
        "Folha": "tb_ceres_folha_str",  # Nome correto da tabela
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


def main():
    st.title("Consulta de Laudos Agrícolas")

    # Selecionar unidade
    unidade_selecionada = st.selectbox(
        "Selecione a unidade", list(UNIDADES_LAUDOS.keys()))

    # Selecionar laudo, baseado na unidade escolhida
    laudo_selecionado = st.selectbox("Selecione o tipo de laudo", list(
        UNIDADES_LAUDOS[unidade_selecionada].keys()))

    # Definir datas padrão para o controle de data
    data_minima = date(2000, 1, 1)  # Menor data permitida
    data_maxima = date(2025, 12, 31)  # Maior data permitida
    data_padrao_inicio = date(2020, 1, 1)  # Data inicial padrão
    data_padrao_fim = date(2020, 12, 31)  # Data final padrão

    # Filtro de Data com valores ajustáveis
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input(
            "Data inicial", value=data_padrao_inicio, min_value=data_minima, max_value=data_maxima)
    with col2:
        data_fim = st.date_input(
            "Data final", value=data_padrao_fim, min_value=data_minima, max_value=data_maxima)

    if st.button("Carregar Dados"):
        try:
            # Obtém a tabela correspondente
            tabela_laudo = UNIDADES_LAUDOS[unidade_selecionada][laudo_selecionado]

            # Construção da query dinâmica com filtro de data
            sql = f"SELECT TOP 1000 * FROM {tabela_laudo}"

            # Adiciona condição de data se o usuário selecionar um período
            if data_inicio and data_fim:
                sql += f" WHERE entrada BETWEEN '{data_inicio}' AND '{data_fim}'"
            elif data_inicio:
                sql += f" WHERE entrada >= '{data_inicio}'"
            elif data_fim:
                sql += f" WHERE entrada <= '{data_fim}'"

            # Executa a consulta SQL
            df_laudo = run_select(sql)

            # Exibe os dados no Streamlit
            st.write(
                f"Exibindo {len(df_laudo)} registros do laudo **{laudo_selecionado}** na unidade **{unidade_selecionada}**.")
            st.dataframe(df_laudo)
        except Exception as e:
            st.error(f"Ocorreu um erro ao consultar os dados: {e}")


if __name__ == "__main__":
    main()
