import os
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from database_utils import run_select
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

# Injetar os CSS externos do AG Grid para o tema "alpine-dark"
st.markdown(
    """
    <link rel="stylesheet" href="https://unpkg.com/ag-grid-community/dist/styles/ag-grid.css">
    <link rel="stylesheet" href="https://unpkg.com/ag-grid-community/dist/styles/ag-theme-alpine-dark.css">
    """,
    unsafe_allow_html=True
)

# Injetar CSS extra para forçar o fundo escuro e definir o estilo do container dos filtros (frame)
st.markdown(
    """
    <style>
      .ag-theme-alpine-dark {
          --ag-background-color: #121212 !important;
          --ag-foreground-color: #e0e0e0 !important;
          --ag-header-background-color: #1e1e1e !important;
          --ag-header-text-color: #e0e0e0 !important;
          --ag-cell-text-color: #e0e0e0 !important;
          --ag-border-color: #333333 !important;
      }
      .ag-theme-alpine-dark, .ag-theme-alpine-dark * {
          background-color: var(--ag-background-color) !important;
          color: var(--ag-foreground-color) !important;
      }
      .filter-container {
          border: 1px solid #ccc;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 20px;
      }
    </style>
    """,
    unsafe_allow_html=True
)

css_file = os.path.join("styles", "styles.css")
if os.path.exists(css_file):
    with open(css_file) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# --- Mapeamentos para a geração do PDF ---
mapping_header = {
    "Solicitante": "solicitante",
    "Proprietário": "proprietario",
    "Propriedade": "propriedade",
    "Laudo": "descricao",
    "Cultura": "nomacultura",
    "Cidade/UF": "municipio",
    "Matricula": "numero",
    "Nº Laudo": "idlaudo",
    "Nº Pedido": "pedido",
    "Data Entrada": "entrada",
    "Data Emissão": "data"
}

mapping_amostras = {
    "Amostra Nº": "numamostra",
    "Talhão": "talhao",
    "Identificação da amostra": "amostra",
    "cm Selo de Qualidade": "selo"
}

mapping_resultados = {
    "Determinação Unidade": "det_unidade",
    "pH Água 1: 2,5": "ph",
    "pH CaCl2 1: 2,5": "ph_cacl",
    "P_Resina mg/dm³": "p",
    "K_Mehlich-1 mg/dm³": "prem",
    "K cmolc": "k1",
    "Ca_KCl cmolc": "ca",
    "Mg_KCl cmolc": "mg",
    "Al cmolc": "al",
    "H+Al_SMP cmolc": "h_al",
    "S mg/dm³": "s",
    "C.O %": "co",
    "M.O %": "mo",
    "B mg/dm³": "b",
    "Cu_DTPA mg/dm³": "cu",
    "Fe_DTPA mg/dm³": "fe",
    "Mn_DTPA mg/dm³": "mn",
    "Zn_DTPA mg/dm³": "zn",
    "Argila g/kg": "argila",
    "Silte g/kg": "silte",
    "Areia Total g/kg": "areia_total",
    "SB cmolc": "sb",
    "CTC pH7,0 cmolc": "ctc_ph7",
    "CTC efetiva cmolc": "ctc_efetiva",
    "Sat. Base V% %": "sat_base",
    "Sat. Al m% %": "sat_al",
    "Ca/Mg": "ca_mg",
    "Ca/K": "ca_k",
    "Mg/K": "mg_k",
    "Ca+Mg/K": "ca_mg_k",
    "Ca na CTC %": "ca_ctc",
    "Mg na CTC %": "mg_ctc",
    "K na CTC %": "k_ctc",
    "H+Al na CTC %": "hal_ctc",
    "Ca+Mg na CTC %": "camg_ctc",
    "Ca+Mg cmolc": "ca_mg_cmolc",
    "Al na CTC %": "al_ctc",
    "M.O g.dm³": "mo_gdm3",
    "H cmolc": "h_cmolc"
}


def draw_determinacao_unidade(c, det_unit: str, start_y: float) -> float:
    """
    Desenha a linha de Determinação Unidade (usando det_unidade)
    e retorna o y para continuar abaixo.
    """
    if det_unit:
        c.setFont("Helvetica", 9)
        c.drawString(40, start_y, f"Determinação Unidade {det_unit}")
        return start_y - 15
    return start_y


def draw_resultados(c, processed_resultados: dict, width: float, start_y: float) -> float:
    """
    Desenha a tabela de parâmetros/valores (menos Determinação Unidade)
    e retorna o y para continuar abaixo.
    """
    resultados_data = [["Parâmetro", "Valor"]]
    for pdf_field, db_field in mapping_resultados.items():
        if pdf_field == "Determinação Unidade":
            continue
        valor = processed_resultados.get(db_field, "")
        resultados_data.append([pdf_field, valor])

    t = Table(resultados_data, colWidths=[250, 100])
    t.setStyle(TableStyle([
        ('GRID',       (0, 0), (-1, -1), 1, colors.white),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 8),
        ('ALIGN',      (1, 1), (-1, -1), 'CENTER'),
    ]))

    t_w, t_h = t.wrap(width-80, start_y)
    if start_y - t_h < 50:
        c.showPage()
        start_y = A4[1] - 50

    t.drawOn(c, 40, start_y - t_h)
    return start_y - t_h - 20

# ===============================
# Funções para obter dados dos filtros
# ===============================


def obter_proprietarios(tabela, data_inicio, data_fim):
    sql = f"""
    SELECT DISTINCT TRIM(proprietario) AS proprietario 
    FROM {tabela} 
    WHERE entrada BETWEEN '{data_inicio.strftime("%Y-%m-%d")}' AND '{data_fim.strftime("%Y-%m-%d")}'
    ORDER BY proprietario
    """
    df = run_select(sql)
    if df.empty:
        return []
    return df['proprietario'].dropna().unique().tolist()


def obter_propriedades_por_proprietario(tabela, proprietario):
    sql = f"""
    SELECT DISTINCT TRIM(propriedade) AS propriedade 
    FROM {tabela} 
    WHERE TRIM(proprietario) = '{proprietario}'
    ORDER BY propriedade
    """
    df = run_select(sql)
    if df.empty:
        return []
    return df['propriedade'].dropna().unique().tolist()


def obter_talhoes_por_propriedade(tabela, propriedade):
    sql = f"""
    SELECT DISTINCT 
           CASE 
             WHEN TRIM(talhao) = '' OR talhao IS NULL THEN 'Talhao Não Informado!'
             ELSE TRIM(talhao)
           END AS talhao 
    FROM {tabela} 
    WHERE LOWER(TRIM(propriedade)) = LOWER('{propriedade}')
    ORDER BY talhao
    """
    df = run_select(sql)
    if df.empty:
        return []
    return df['talhao'].dropna().unique().tolist()

# ===============================
# Funções auxiliares para PDF e consulta
# ===============================


def draw_header_table(c, rec, width, y):
    # Ajusta campos faltantes
    cultura = rec.get('cultura', '')
    municipio = rec.get('municipio', '')
    numero = rec.get('numero', '')

    data_fields = [
        ['Solicitante:', 'Proprietário:', 'Propriedade:'],
        [rec.get('solicitante', ''), rec.get(
            'proprietario', ''), rec.get('propriedade', '')],
        ['Laudo:', '', ''],
        [rec.get('descricao', ''), '', ''],
        ['Cultura:', 'Cidade/UF:', 'Matrícula:'],
        [cultura, municipio, numero],
        ['Nº Laudo:', 'Nº Pedido:', ''],
        [rec.get('idlaudo', ''), rec.get('pedido', ''), ''],
        ['Data Entrada:', 'Data Emissão:', ''],
        [rec.get('entrada', ''), rec.get('data', ''), '']
    ]
    table = Table(data_fields, colWidths=[(width-60)/3]*3)
    style = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT')
    ])
    table.setStyle(style)
    tw, th = table.wrap(width-60, y)
    table.drawOn(c, 30, y-th)
    return y-th-10


def gerar_pdf(rec):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # --- Logo e cabeçalho fixo ---
    logo_path = os.path.join(os.path.dirname(__file__), "logo_safrar.jpeg")
    try:
        c.drawImage(logo_path, 30, h - 80, width=80, height=30, mask='auto')
    except Exception:
        pass

    c.setFont("Helvetica-Bold", 14)
    c.drawString(120, h - 50, "Confiança e Credibilidade ao Seu Alcance")
    c.setFont("Helvetica", 9)
    c.drawString(
        30, h - 95,
        "AVENIDA ATLANTA, 558 - NOVO MUNDO - Uberlândia-MG    Fone: (34)3211-3060"
    )
    y = h - 120

    # --- Cabeçalho com dados do laudo ---
    y = draw_header_table(c, rec, w, y)

    # --- Tabela de Amostras ---
    amos_h = list(mapping_amostras.keys())
    amos_rows = [amos_h]
    for a in rec.get("amostras", []):
        amos_rows.append([a.get(mapping_amostras[k], "") for k in amos_h])

    if len(amos_rows) > 1:
        tbl_amos = Table(amos_rows, colWidths=[60, 50, 100, 100])
        tbl_amos.setStyle(TableStyle([
            ("GRID",      (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0),  colors.grey),
            ("FONTSIZE",  (0, 0), (-1, -1), 8),
            ("ALIGN",     (0, 0), (-1, -1), "CENTER"),
        ]))
        tw, th = tbl_amos.wrap(w - 60, y)
        if y - th < 50:
            c.showPage()
            y = h - 50
        tbl_amos.drawOn(c, 30, y - th)
        y -= th + 10

    # --- Tabela de Resultados (2 colunas: Parâmetro + Valor) ---
    res_header = ["Determinação Unidade", "Valor"]
    res_rows = [res_header]
    # pulamos o primeiro mapeamento (que já virou o cabeçalho)
    for label, field in list(mapping_resultados.items())[1:]:
        valor = rec.get(field, "")
        if str(valor) in ["-1", "-1.0"]:
            valor = ""
        res_rows.append([label, valor])

    tbl_res = Table(res_rows, colWidths=[300, 100])
    tbl_res.setStyle(TableStyle([
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0),  colors.grey),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("ALIGN",      (1, 1), (-1, -1), "CENTER"),
    ]))
    tw, th = tbl_res.wrap(w - 60, y)
    if y - th < 50:
        c.showPage()
        y = h - 50
    tbl_res.drawOn(c, 30, y - th)

    # --- Finaliza ---
    c.showPage()
    c.save()
    return buf.getvalue()

# restante inalterado...


def consultar_laudos(tabela, data_inicio, data_fim):
    sql = f"""
    SELECT idlaudo, entrada, data, pedido, solicitante, numamostra, proprietario, propriedade, talhao
    FROM {tabela}
    WHERE entrada BETWEEN '{data_inicio.strftime("%Y-%m-%d")}' AND '{data_fim.strftime("%Y-%m-%d")}'
    ORDER BY entrada DESC
    """
    df = run_select(sql)
    return df


def consultar_detalhes_laudo(tabela, idlaudo):
    sql = f"SELECT * FROM {tabela} WHERE idlaudo = '{idlaudo}'"
    df = run_select(sql)
    if df.empty:
        return {}
    header = df.iloc[0].to_dict()
    amostras = df.to_dict(orient="records")
    header["amostras"] = amostras
    resultados = {}
    for pdf_field, db_field in mapping_resultados.items():
        resultados[db_field] = header.get(db_field, "")
    header["resultados"] = resultados
    return header


def agrupar_pedidos(df):
    grouped = df.groupby("pedido", as_index=False).agg({
        "idlaudo": "nunique",
        "solicitante": "first",
        "entrada": "first",
        "data": "first"
    })
    grouped.rename(columns={"idlaudo": "total_laudos"}, inplace=True)
    grouped = grouped[["pedido", "total_laudos",
                       "solicitante", "entrada", "data"]]
    grouped["entrada"] = pd.to_datetime(
        grouped["entrada"]).dt.strftime("%d/%m/%Y")
    grouped["data"] = pd.to_datetime(grouped["data"]).dt.strftime("%d/%m/%Y")
    return grouped


def laudos_por_pedido(df, pedido_val):
    df_filtered = df[df["pedido"] == pedido_val]
    grouped = df_filtered.groupby("idlaudo", as_index=False).agg({
        "entrada": "first",
        "data": "first",
        "solicitante": "first",
        "numamostra": "count"
    })
    grouped.rename(columns={"numamostra": "total_amostras"}, inplace=True)
    grouped = grouped[["idlaudo", "solicitante",
                       "total_amostras", "entrada", "data"]]
    grouped["entrada"] = pd.to_datetime(
        grouped["entrada"]).dt.strftime("%d/%m/%Y")
    grouped["data"] = pd.to_datetime(grouped["data"]).dt.strftime("%d/%m/%Y")
    return grouped


def main():
    st.title("Consulta de Laudos Agrícolas")

    # Inicializa o session state
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'selected_pedido' not in st.session_state:
        st.session_state.selected_pedido = None
    if 'selected_laudo' not in st.session_state:
        st.session_state.selected_laudo = None

    # Filtros de Pesquisa - Todos os campos são exibidos desde o início
    with st.expander("Filtros de Pesquisa", expanded=True):
        with st.container():
            # Linha 1: Unidade e Tipo de Laudo
            col1, col2 = st.columns(2)
            with col1:
                unidade = st.selectbox(
                    "Unidade", ["Ceres", "Patrocínio", "Croplab"], key="selected_unidade", index=0)
            with col2:
                tipo_laudo = st.selectbox(
                    "Tipo de Laudo", ["Solo"], key="selected_tipo_laudo", index=0)

            # Linha 2: Proprietário (linha inteira)
            tabelas = {
                "Ceres": {"Solo": "tb_ceres_solo"},
                "Patrocínio": {"Solo": "tb_croplab_solo"},
                "Croplab": {"Solo": "tb_croplab_solo"}
            }
            tabela = tabelas[unidade][tipo_laudo]
            proprietario_options = obter_proprietarios(
                tabela, date(2020, 1, 1), date.today())
            proprietario_select = st.selectbox("Proprietário", [
                                               "Todos"] + proprietario_options, key="selected_proprietario", index=0)

            # Linha 3: Propriedade e Talhão lado a lado
            col3, col4 = st.columns(2)
            with col3:
                if proprietario_select != "Todos":
                    propriedade_options = obter_propriedades_por_proprietario(
                        tabela, proprietario_select)
                else:
                    propriedade_options = []
                propriedade_select = st.selectbox("Propriedade", [
                                                  "Todos"] + propriedade_options, key="selected_propriedade", index=0)
            with col4:
                if propriedade_select != "Todos":
                    talhao_options = obter_talhoes_por_propriedade(
                        tabela, propriedade_select)
                else:
                    talhao_options = []
                talhao_select = st.selectbox("Talhão", [
                                             "Selecione a Propriedade!"] + talhao_options, key="selected_talhao", index=0)

            # Datas
            col5, col6 = st.columns(2)
            with col5:
                data_inicio = st.date_input("Data Início", value=date(
                    2020, 1, 1), key="selected_data_inicio")
            with col6:
                data_fim = st.date_input(
                    "Data Fim", value=date.today(), key="selected_data_fim")

            submit = st.button("Buscar Pedidos")

        st.markdown("**Filtros Selecionados:**")
        st.write({
            "Unidade": unidade,
            "Tipo de Laudo": tipo_laudo,
            "Proprietário": proprietario_select,
            "Propriedade": propriedade_select,
            "Talhão": talhao_select,
            "Data Início": data_inicio,
            "Data Fim": data_fim
        })

    if submit:
        if not unidade:
            st.warning("Por favor, selecione uma Unidade para continuar.")
        elif not tipo_laudo:
            st.warning("Por favor, selecione um Tipo de Laudo para continuar.")
        else:
            df = consultar_laudos(tabela, data_inicio, data_fim)
            if df.empty:
                st.error("Nenhum laudo encontrado para os filtros informados.")
                return
            if proprietario_select and proprietario_select != "Todos":
                df = df[df["proprietario"].str.strip() == proprietario_select]
            if propriedade_select and propriedade_select != "Todos":
                df = df[df["propriedade"].str.strip() == propriedade_select]
            if talhao_select and talhao_select != "Selecione a Propriedade!":
                df = df[df["talhao"].str.strip() == talhao_select]
            st.session_state.df = df

    if st.session_state.get("df") is not None:
        row_count = st.session_state.df.shape[0]
        st.markdown(f"**Pedidos Encontrados: {row_count}**")

    # Exibição dos pedidos encontrados
    with st.expander("Pedidos Encontrados", expanded=True):
        if st.session_state.get("df") is not None:
            df_pedidos = agrupar_pedidos(st.session_state.df)
            gb1 = GridOptionsBuilder.from_dataframe(df_pedidos)
            gb1.configure_selection("single", use_checkbox=True)
            grid_options1 = gb1.build()
            grid_response1 = AgGrid(
                df_pedidos,
                gridOptions=grid_options1,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                theme="alpine-dark",
                height=200,
                fit_columns_on_grid_load=True
            )
            selected_pedido = grid_response1.get("selected_rows", [])
            if isinstance(selected_pedido, pd.DataFrame):
                selected_pedido = selected_pedido.to_dict(orient="records")
            if selected_pedido and len(selected_pedido) > 0:
                st.session_state.selected_pedido = selected_pedido[0]["pedido"]
                st.markdown("### Pedido Selecionado:")
                st.write(st.session_state.selected_pedido)
            else:
                st.info("Selecione um pedido no grid acima.")

    with st.expander("Laudos do Pedido Selecionado", expanded=True):
        if st.session_state.get("df") is not None and st.session_state.get("selected_pedido"):
            st.subheader("Laudos do Pedido Selecionado")
            df_laudos = laudos_por_pedido(
                st.session_state.df, st.session_state.selected_pedido)
            gb2 = GridOptionsBuilder.from_dataframe(df_laudos)
            gb2.configure_selection("single", use_checkbox=True)
            grid_options2 = gb2.build()
            grid_response2 = AgGrid(
                df_laudos,
                gridOptions=grid_options2,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                theme="alpine-dark",
                height=200,
                fit_columns_on_grid_load=True
            )
            selected_laudo = grid_response2.get("selected_rows", [])
            if isinstance(selected_laudo, pd.DataFrame):
                selected_laudo = selected_laudo.to_dict(orient="records")
            if selected_laudo and len(selected_laudo) > 0:
                st.session_state.selected_laudo = selected_laudo[0]["idlaudo"]
                st.markdown("### Laudo Selecionado:")
                st.write(selected_laudo[0])
            else:
                st.info("Selecione um laudo no grid acima.")

    if st.button("Gerar PDF"):
        if not st.session_state.get("selected_laudo"):
            st.error("Nenhum laudo selecionado!")
        else:
            idlaudo = st.session_state.selected_laudo
            laudo_record_full = consultar_detalhes_laudo(tabela, idlaudo)
            if not laudo_record_full:
                st.error("Falha ao obter os detalhes do laudo.")
                return
            pdf_bytes = gerar_pdf(laudo_record_full)
            if pdf_bytes:
                st.download_button(
                    label="Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"laudo_{laudo_record_full.get('idlaudo', '')}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Falha ao gerar PDF.")


if __name__ == "__main__":
    def agrupar_pedidos(df):
        grouped = df.groupby("pedido", as_index=False).agg({
            "idlaudo": "nunique",
            "solicitante": "first",
            "entrada": "first",
            "data": "first"
        })
        grouped.rename(columns={"idlaudo": "total_laudos"}, inplace=True)
        grouped = grouped[["pedido", "total_laudos",
                           "solicitante", "entrada", "data"]]
        grouped["entrada"] = pd.to_datetime(
            grouped["entrada"]).dt.strftime("%d/%m/%Y")
        grouped["data"] = pd.to_datetime(
            grouped["data"]).dt.strftime("%d/%m/%Y")
        return grouped

    def laudos_por_pedido(df, pedido_val):
        df_filtered = df[df["pedido"] == pedido_val]
        grouped = df_filtered.groupby("idlaudo", as_index=False).agg({
            "entrada": "first",
            "data": "first",
            "solicitante": "first",
            "numamostra": "count"
        })
        grouped.rename(columns={"numamostra": "total_amostras"}, inplace=True)
        grouped = grouped[["idlaudo", "solicitante",
                           "total_amostras", "entrada", "data"]]
        grouped["entrada"] = pd.to_datetime(
            grouped["entrada"]).dt.strftime("%d/%m/%Y")
        grouped["data"] = pd.to_datetime(
            grouped["data"]).dt.strftime("%d/%m/%Y")
        return grouped

    main()
