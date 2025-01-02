import streamlit as st
from streamlit_cookies_controller import CookieController

def set_cookie(controller):
    st.header("Definir um Cookie")
    cookie_name = st.text_input("Nome do cookie:", "cookie_name")
    cookie_value = st.text_input("Valor do cookie:", "testing")
    if st.button("Set Cookie"):
        controller.set(cookie_name, cookie_value)
        st.success(f"Cookie '{cookie_name}' definido com valor '{cookie_value}'!")

def get_all_cookies(controller):
    st.header("Obter Todos os Cookies")
    if st.button("Get All Cookies"):
        cookies = controller.getAll()
        st.write(cookies)  # Mostra todos os cookies em uma tabela

def get_specific_cookie(controller):
    st.header("Obter um Cookie Específico")
    cookie_to_get = st.text_input("Nome do cookie para obter:", "cookie_name")
    if st.button("Get Cookie"):
        cookie = controller.get(cookie_to_get)
        if cookie is not None:
            st.write(f"Valor do cookie '{cookie_to_get}': {cookie}")
        else:
            st.error(f"Cookie '{cookie_to_get}' não encontrado.")

def remove_cookie(controller):
    st.header("Remover um Cookie")
    cookie_to_remove = st.text_input("Nome do cookie para remover:", "cookie_name")
    if st.button("Remove Cookie"):
        controller.remove(cookie_to_remove)
        st.success(f"Cookie '{cookie_to_remove}' removido com sucesso!")

def check_cookie_removed(controller):
    st.header("Verificar se um Cookie foi Removido")
    cookie_to_check = st.text_input("Nome do cookie para verificar:", "cookie_name")
    if st.button("Check Cookie Removed"):
        cookie_check = controller.get(cookie_to_check)
        if cookie_check is None:
            st.write(f"Cookie '{cookie_to_check}' foi removido com sucesso!")
        else:
            st.write(f"Cookie '{cookie_to_check}' ainda existe com valor: {cookie_check}")

def run_cookie_test():
    # Inicializa o CookieController
    controller = CookieController()

    # Chama as funções de teste do cookie
    set_cookie(controller)
    get_all_cookies(controller)
    get_specific_cookie(controller)
    remove_cookie(controller)
    check_cookie_removed(controller)

def main():
    # Configuração da página do Streamlit
    st.set_page_config('Cookie QuickStart', '🍪', layout='wide')

    # Título da aplicação
    st.title("Teste do Cookie Controller")

    # Chama a função de teste do cookie
    run_cookie_test()

if __name__ == "__main__":
    main()
