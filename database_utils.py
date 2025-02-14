# database_utils.py
import pyodbc
import contextlib
import configparser
import pandas as pd


@contextlib.contextmanager
def db_connection():
    config = configparser.ConfigParser()
    config.read("config/config.ini")

    driver = config["DATABASE"]["DRIVER"]
    server = config["DATABASE"]["SERVER"]
    database = config["DATABASE"]["DATABASE"]
    user = config["DATABASE"]["USER"]       # ex.: LeitorDash
    password = config["DATABASE"]["PASSWORD"]

    conn_str = (
        f"Driver={{{driver}}};"
        f"Server={server};"
        f"Database={database};"
        f"UID={user};"
        f"PWD={password};"
    )
    conn = pyodbc.connect(conn_str)
    try:
        yield conn
    finally:
        conn.close()


def run_select(sql_query):
    """
    Retorna um DataFrame com o resultado do SELECT.
    """
    with db_connection() as conn:
        df = pd.read_sql(sql_query, conn)
    return df
