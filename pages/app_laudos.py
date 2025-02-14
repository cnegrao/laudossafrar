import streamlit as st
from database_utils import run_select

# Dicionário que mapeia as unidades e seus respectivos laudos
UNIDADES_LAUDOS = {
    "Ceres": {
        "Água": "tb_ceres_agua",
        "Calcário": "tb_ceres_calcario",
        "Composto Orgânico": "tb_ceres_composto_organico",
        "Fertilizante": "tb_ceres_fertilizante",
        "Folha": "tb_ceres_folha",
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

    if st.button("Carregar Dados"):
        try:
            # Obtém a tabela correspondente
            tabela_laudo = UNIDADES_LAUDOS[unidade_selecionada][laudo_selecionado]

            # Executa a consulta SQL
            sql = f"SELECT TOP 1000 * FROM {tabela_laudo}"
            df_laudo = run_select(sql)

            # Exibe os dados no Streamlit
            st.write(
                f"Exibindo {len(df_laudo)} registros do laudo **{laudo_selecionado}** na unidade **{unidade_selecionada}**.")
            st.dataframe(df_laudo)
        except Exception as e:
            st.error(f"Ocorreu um erro ao consultar os dados: {e}")


if __name__ == "__main__":
    main()
