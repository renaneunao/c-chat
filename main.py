from streamlit_cookies_controller import CookieController
from streamlit_app import main
from auth import tela_autenticacao
import streamlit as st
from pathlib import Path

if __name__ == "__main__":

    current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
    logo_path = current_dir / "images/Sicoob Logo.png"

    # Configurando a página
    st.set_page_config(
        page_title="CrediChat",
        page_icon=str(logo_path),
    )

    # Inicializa o controlador de cookies
    controller = CookieController()

    autenticado = controller.get("autenticado")

    # Estrutura de navegação entre as páginas
    if autenticado:
        main(controller, st)
    else:
        tela_autenticacao(controller, st)
