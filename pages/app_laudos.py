import os
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from database_utils import run_select
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def gerar_pdf(laudo_record):
    """
    Gera um PDF com o layout desejado, incluindo:
      - Logo e cabeçalho de contato;
      - Dados do laudo (campos do cabeçalho);
      - Tabela de amostras;
      - Seção de Resultados (em coluna).

    O arquivo de logo ("logo_safrar.jpeg") deve estar no mesmo diretório deste arquivo,
    ou informe o caminho absoluto.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Constrói o caminho absoluto para o logo
    logo_path = os.path.join(os.path.dirname(__file__), "logo_safrar.jpeg")
    try:
        c.drawImage(logo_path, 40, height - 100, width=100,
                    preserveAspectRatio=True, mask='auto')
    except Exception as e:
        st.write("Erro ao carregar logo:", e)

    # Cabeçalho principal (centralizado)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 50,
                        "Confiança e Credibilidade ao Seu Alcance")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 65,
                        "AVENIDA ATLANTA, 558 - NOVO MUNDO - Uberlândia-MG")
    c.drawCentredString(width / 2, height - 80, "38407-710")
    c.drawCentredString(width / 2, height - 95,
                        "Fone: (34)3211-3060  |  Email: atendimento.uberlândia@safrar.agr.br")
    c.line(40, height - 110, width - 40, height - 110)

    # Dados do laudo (Cabeçalho)
    start_y = height - 130
    line_height = 14
    c.setFont("Helvetica", 10)
    header_fields = [
        ("Solicitante", laudo_record.get("solicitante", "")),
        ("Proprietário", laudo_record.get("proprietario", "")),
        ("Propriedade", laudo_record.get("propriedade", "")),
        ("Laudo", laudo_record.get("laudo", "")),
        ("Cultura", laudo_record.get("cultura", "")),
        ("Cidade/UF", laudo_record.get("municipio", "")),
        ("Matricula", laudo_record.get("matricula", "")),
        ("Geral Solo", laudo_record.get("geral_solo", "")),
        ("N/I", laudo_record.get("ni", "")),
        ("Nº Laudo", laudo_record.get("idlaudo", "")),
        ("Nº Pedido", laudo_record.get("pedido", "")),
        ("Data Entrada", laudo_record.get("entrada", "")),
        ("Data Emissão", laudo_record.get("data", ""))
    ]
    for label, value in header_fields:
        c.drawString(40, start_y, f"{label}: {value}")
        start_y -= line_height

    c.line(40, start_y - 5, width - 40, start_y - 5)
    start_y -= 20

    # Tabela de Amostras
    # Cabeçalho da tabela
    table_headers = ["Amostra Nº", "Talhão",
                     "Identificação da amostra", "cm Selo de Qualidade"]
    col_widths = [70, 50, 100, 80]
    x = 40
    c.setFont("Helvetica-Bold", 9)
    for i, header in enumerate(table_headers):
        c.drawString(x, start_y, header)
        x += col_widths[i]
    start_y -= line_height
    c.setFont("Helvetica", 9)

    # Exibe as amostras (ex.: uma linha com os dados)
    amostras = laudo_record.get("amostras", [])
    for amostra in amostras:
        x = 40
        for i, field in enumerate(["numamostra", "talhao", "identificacao", "selo"]):
            value = amostra.get(field, "")
            c.drawString(x, start_y, str(value))
            x += col_widths[i]
        start_y -= line_height
        if start_y < 50:
            c.showPage()
            start_y = height - 50

    # Seção de Resultados (exibe os parâmetros em formato de coluna)
    resultados = laudo_record.get("resultados", {})
    if resultados:
        if start_y < 100:
            c.showPage()
            start_y = height - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, start_y, "Resultados:")
        start_y -= 20
        c.setFont("Helvetica", 9)
        for parametro, valor in resultados.items():
            c.drawString(40, start_y, f"{parametro}: {valor}")
            start_y -= line_height
            if start_y < 50:
                c.showPage()
                start_y = height - 50

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def consultar_laudos(tabela, data_inicio, data_fim):
    """
    Consulta os laudos na base filtrando pelo intervalo de datas (campo 'entrada'),
    retornando registros distintos com os campos: idlaudo, entrada, data e pedido.
    """
    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")
    sql = f"""
    SELECT DISTINCT idlaudo, entrada, data, pedido
    FROM {tabela}
    WHERE entrada BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
    ORDER BY entrada DESC
    """
    st.write("SQL Query:", sql)
    df = run_select(sql)
    st.write("Laudos encontrados:", len(df))
    return df


def main():
    st.title("Consulta de Laudos Agrícolas")

    # Armazena o DataFrame e a linha selecionada em session_state
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'selected_row' not in st.session_state:
        st.session_state.selected_row = None

    # Formulário de Filtros
    with st.form("filtro_form"):
        st.header("Filtros de Pesquisa")
        unidade = st.selectbox("Selecione a Unidade", [
                               "Ceres", "Patrocínio", "Croplab"])
        tipo_laudo = st.selectbox("Selecione o Tipo de Laudo", ["Solo"])
        data_inicio = st.date_input("Data Início", value=date(2020, 1, 1))
        data_fim = st.date_input("Data Fim", value=date.today())
        submit = st.form_submit_button("Buscar Laudos")

    if submit:
        st.write("Buscando laudos para:", unidade,
                 tipo_laudo, data_inicio, data_fim)
        tabelas = {
            "Ceres": {"Solo": "tb_ceres_solo"},
            "Patrocínio": {"Solo": "tb_patrocinio_solo"},
            "Croplab": {"Solo": "tb_croplab_solo"}
        }
        tabela = tabelas[unidade][tipo_laudo]
        df = consultar_laudos(tabela, data_inicio, data_fim)
        if df.empty:
            st.error("Nenhum laudo encontrado para os filtros informados.")
            return
        st.session_state.df = df

    # Exibe o grid se houver dados na session_state
    if st.session_state.df is not None:
        st.subheader("Laudos Encontrados")
        df_display = st.session_state.df[['idlaudo', 'entrada', 'data']]
        st.write("DataFrame shape:", df_display.shape)
        st.write("Dados:", df_display)

        # Configura o AgGrid para seleção única
        gb = GridOptionsBuilder.from_dataframe(df_display)
        gb.configure_selection("single", use_checkbox=True)
        grid_options = gb.build()

        grid_response = AgGrid(
            df_display,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            theme="blue",
            height=300,
            fit_columns_on_grid_load=True
        )

        selected_rows = grid_response.get("selected_rows", [])
        st.write("Selected rows (debug):", selected_rows)
        if isinstance(selected_rows, pd.DataFrame):
            selected_rows = selected_rows.to_dict(orient="records")
        if selected_rows and len(selected_rows) > 0:
            st.session_state.selected_row = selected_rows[0]
            st.markdown("### Laudo Selecionado:")
            st.write(st.session_state.selected_row)
        else:
            st.info("Selecione um laudo no grid para gerar o PDF.")

        if st.button("Gerar PDF"):
            if not st.session_state.selected_row:
                st.error("Nenhum laudo selecionado!")
            else:
                laudo_record = st.session_state.selected_row
                # Exemplo de dados completos do laudo para o PDF; em produção, obtenha os dados reais da base.
                laudo_record_full = {
                    "solicitante": "ALEX RIBEIRO DA SILVA",
                    "proprietario": "ALEX RIBEIRO DA SILVA",
                    "propriedade": "VITÓRIA",
                    "laudo": "Padrão cmolc",
                    "cultura": "Geral Solo",
                    "municipio": "N/I",
                    "matricula": "093",
                    "geral_solo": "",
                    "ni": "",
                    "idlaudo": laudo_record.get("idlaudo", ""),
                    "pedido": "1114/2025",
                    "entrada": laudo_record.get("entrada", ""),
                    "data": laudo_record.get("data", ""),
                    "amostras": [
                        {
                            "numamostra": "7480/2025",
                            "talhao": "TH 01",
                            "identificacao": "S6",
                            "selo": "0-20",
                            "analise": "7480/2025"
                        }
                    ],
                    "resultados": {
                        "Determinação Unidade": "7480/2025",
                        "pH Água 1: 2,5": "5,66",
                        "pH CaCl2 1: 2,5": "5,30",
                        "P_Resina mg/dm³": "19,79",
                        "K_Mehlich-1 mg/dm³": "106,55",
                        "K cmolc": "0,27",
                        "Ca_KCl cmolc": "3,72",
                        "Mg_KCl cmolc": "1,75",
                        "Al cmolc": "0,00",
                        "H+Al_SMP cmolc": "3,30",
                        "S mg/dm³": "6,69",
                        "C.O %": "1,70",
                        "M.O %": "2,94",
                        "B mg/dm³": "0,78",
                        "Cu_DTPA mg/dm³": "4,90",
                        "Fe_DTPA mg/dm³": "116,88",
                        "Mn_DTPA mg/dm³": "20,59",
                        "Zn_DTPA mg/dm³": "1,23",
                        "Argila g/kg": "370,00",
                        "Silte g/kg": "100",
                        "Areia Total g/kg": "530,00",
                        "SB cmolc": "5,74",
                        "CTC pH7,0 cmolc": "9,04",
                        "CTC efetiva cmolc": "5,74",
                        "Sat. Base V% %": "63",
                        "Sat. Al m% %": "0,00",
                        "Ca/Mg": "2,12",
                        "Ca/K": "13,65",
                        "Mg/K": "6,42",
                        "Ca+Mg/K": "10,14",
                        "Ca na CTC %": "41,13",
                        "Mg na CTC %": "19,35",
                        "K na CTC %": "3,01",
                        "H+Al na CTC %": "36,49",
                        "Ca+Mg na CTC %": "90,20",
                        "Ca+Mg cmolc": "5,47",
                        "Al na CTC %": "0,00",
                        "M.O g.dm³": "29,40",
                        "H cmolc": "3,30"
                    }
                }
                pdf_bytes = gerar_pdf(laudo_record_full)
                if pdf_bytes:
                    st.download_button(
                        label="Baixar PDF",
                        data=pdf_bytes,
                        file_name=f"laudo_{laudo_record_full['idlaudo']}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Falha ao gerar PDF.")


if __name__ == "__main__":
    main()
