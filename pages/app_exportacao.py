import streamlit as st
import pandas as pd
import io
from database_utils import run_select

# Dicionário que mapeia as unidades e seus respectivos laudos
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


def main():
    st.title("📤 Exportação de Laudos Agrícolas")

    # Selecionar unidade
    unidade_selecionada = st.selectbox(
        "Selecione a unidade", list(UNIDADES_LAUDOS.keys()))

    # Selecionar laudo
    laudo_selecionado = st.selectbox("Selecione o tipo de laudo", list(
        UNIDADES_LAUDOS[unidade_selecionada].keys()))

    # Definir tamanho da página para paginação
    page_size = st.slider("Registros por página", 10, 100, 20)
    page_number = st.number_input("Página", min_value=1, step=1, value=1)

    if st.button("🔍 Carregar Dados"):
        try:
            # Obtém a tabela correspondente
            tabela_laudo = UNIDADES_LAUDOS[unidade_selecionada][laudo_selecionado]

            # Executa a consulta SQL
            sql = f"SELECT * FROM {tabela_laudo}"
            df_laudo = run_select(sql)

            # Paginação manual
            total_registros = len(df_laudo)
            start_idx = (page_number - 1) * page_size
            end_idx = start_idx + page_size
            df_paginado = df_laudo.iloc[start_idx:end_idx]

            # Exibe a tabela paginada
            st.write(
                f"Exibindo registros {start_idx + 1} a {end_idx} de {total_registros}.")
            st.dataframe(df_paginado)

            # Exportar para Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_laudo.to_excel(writer, index=False, sheet_name="Laudo")
                writer.close()
            output.seek(0)

            st.download_button(
                label="📥 Baixar Excel",
                data=output,
                file_name=f"{laudo_selecionado}_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Ocorreu um erro ao consultar os dados: {e}")


if __name__ == "__main__":
    main()
