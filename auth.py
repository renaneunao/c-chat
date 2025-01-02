from UTILS.utils import autenticar, list_users
from streamlit_app import main

def tela_autenticacao(controller, st):
    # print('Entrei na tela de autenticacao e os cookies são: ', controller.getAll())
    requer_autenticacao = controller.get('autenticado')
    _streamlit_xsrf = controller.get('_streamlit_xsrf')
    # print('Requer autenticação: ', requer_autenticacao)
    # print('_streamlit_xsrf: ', _streamlit_xsrf)
    if _streamlit_xsrf is not None:
        requer_autenticacao = False

    if not requer_autenticacao:
        if requer_autenticacao is not None:
            st.title("Tela de Login")

            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")

            if st.button("Login"):
                if autenticar(usuario, senha):
                    controller.set('autenticado', True)
                    users_data = list_users(st)
                    user_details = next((user for user in users_data if user['loginAD'] == usuario), None)

                    if user_details:
                        for key, value in user_details.items():
                            controller.set(key, value)  # Store user details
                        main(controller, st)
                        st.rerun()  # Restart the application

                    else:
                        st.error("Não foi possível obter os detalhes do usuário.")
                else:
                    st.error("Usuário ou senha inválidos. Tente novamente.")
            else:
                controller.set('autenticado', False)
    # st.write('Finalmente os cookies são: ', controller.getAll())