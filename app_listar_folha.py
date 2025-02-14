import streamlit as st
import pyodbc
import pandas as pd
import configparser
import contextlib
import os

#
# 1) Context manager para conexão ao banco via config.ini
#


@contextlib.contextmanager
def db_connection():
    # Lê config.ini
    config = configparser.ConfigParser()
    config.read("config/config.ini")  # Ajuste caminho se necessário

    driver = config["DATABASE"]["DRIVER"]
    server = config["DATABASE"]["SERVER"]
    database = config["DATABASE"]["DATABASE"]
    user = config["DATABASE"]["USER"]
    password = config["DATABASE"]["PASSWORD"]

    # Monta a connection string para pyodbc
    conn_str = (
        f"Driver={{{driver}}};"
        f"Server={server};"
        f"Database={database};"
        f"UID={user};"
        f"PWD={password};"
    )

    # Cria a conexão
    conn = pyodbc.connect(conn_str)
    try:
        yield conn
    finally:
        conn.close()  # Fecha quando sai do bloco "with"

#
# 2) Função para executar consulta SQL e retornar DataFrame
#


def consultar_top_1000_folha():
    with db_connection() as conn:
        query = "SELECT TOP 1000 * FROM tb_ceres_folha_str"
        df = pd.read_sql(query, conn)
    return df

#
# 3) Aplicação Streamlit
#


def main():
    st.title("Listar TOP 1000 da tabela tb_ceres_folha_str")

    if st.button("Carregar Dados"):
        try:
            df_folha = consultar_top_1000_folha()
            st.write(f"Retornados {len(df_folha)} registros.")
            st.dataframe(df_folha)
        except Exception as e:
            st.error(f"Ocorreu um erro ao consultar: {e}")


if __name__ == "__main__":
    main()
