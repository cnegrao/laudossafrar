import streamlit as st


def main():
    # Configuração da página principal
    st.set_page_config(page_title="Sistema de Laudos Agrícolas", layout="wide")

    # Cabeçalho fixo no topo
    st.markdown("""
        <style>
            .header {
                background-color: #007A33;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        </style>
        <div class='header'>🌱 Sistema de Laudos Agrícolas</div>
    """, unsafe_allow_html=True)

    # Introdução
    st.markdown("## 📊 Bem-vindo ao Sistema de Laudos Agrícolas")
    st.write(
        "Este sistema permite acessar e analisar laudos de **solo, fertilizantes, folhas, água, calcário e composto orgânico** "
        "de três unidades: **Ceres, Patrocínio e Croplab**."
    )

    # Criando botões para acessar diferentes páginas
    st.markdown("### 🔍 Escolha uma Opção")

    col1, col2 = st.columns(2)

    with col1:
        st.page_link("app_exames", label="📂 Consultar Laudos", icon="📑")

    with col2:
        st.page_link("app_exportacao", label="📤 Exportar Dados", icon="📊")

    # Rodapé
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "© 2024 - Sistema de Laudos Agrícolas | Desenvolvido com ❤️ e Streamlit"
        "</div>", unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
