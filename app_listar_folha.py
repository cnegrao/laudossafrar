# app.py

import streamlit as st
from database_utils import run_select


def main():
    st.title("Listar TOP 1000 da tabela tb_ceres_folha_str")

    if st.button("Carregar Dados"):
        try:
            # Definimos a query para buscar os primeiros 1000 registros
            query = "SELECT TOP 1000 * FROM tb_ceres_folha_str"
            df_folha = run_select(query)

            st.write(f"Retornados {len(df_folha)} registros.")
            st.dataframe(df_folha)
        except Exception as e:
            st.error(f"Ocorreu um erro ao consultar: {e}")


if __name__ == "__main__":
    main()
