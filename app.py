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

    # Botão de navegação para a página de laudos
    st.markdown("### 🔍 Acesse seus Laudos")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.page_link("pages/app_exames.py", label="📂 Acessar Laudos", icon="📑")

    # Rodapé
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "© 2024 - Sistema de Laudos Agrícolas | Desenvolvido com ❤️ e Streamlit"
        "</div>", unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
