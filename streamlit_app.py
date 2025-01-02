import os
import ast
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import urllib3
import re
from PIL import Image
import requests
from streamlit_extras.colored_header import colored_header
from streamlit_extras.grid import grid


# Importações úteis
from UTILS.utils import (get_llm,
                         get_embeddings,
                         get_db,
                         gerar_audio,
                         add_uploaded_files,
                         round_image_corners,
                         )
from DOC_RAG.utils_pdf import user_input, list_documents, pdf_directory
from SQL_RAG.utils_sql import converse_com_sql
from CSV_RAG.utils_csv import converse_com_csv
from YTB_RAG.utils_ytb import youtube_video_question
from URL_RAG.utils_url import url_question
from TALK.talk import converse

from streamlit_extras.bottom_container import bottom
from streamlit_extras.add_vertical_space import add_vertical_space

# Suprimir warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Carregar variáveis de ambiente
load_dotenv()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def main(controller, st):
    # Função para aguardar até que o cookie 'foto' esteja disponível
    def wait_for_cookie(controller, cookie_name, timeout=10):
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            cookie_value = controller.get(cookie_name)
            if cookie_value is not None:
                return cookie_value
            time.sleep(0.5)  # Aguarda meio segundo antes de verificar novamente
        return None  # Retorna None se o cookie não for encontrado dentro do tempo limite

    # Obtém o cookie 'foto', aguardando se necessário
    foto_cookie = wait_for_cookie(controller, 'foto')

    # Verifica se o cookie 'foto' foi carregado
    if foto_cookie is not None:
        # Se o cookie estiver disponível, constrói a URL da imagem
        url_imagem = f'https://intranet.sicoobcredicaf.com.br/sys/conteudo/usuarios/{foto_cookie}'
        image = Image.open(requests.get(url_imagem, stream=True).raw)
    else:
        # Caso contrário, usa a imagem padrão (logo_path)
        current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
        logo_path = current_dir / "images/Sicoob Logo.png"
        st.warning("Imagem do usuário não está disponível. Usando logo padrão.")
        image = Image.open(logo_path)
        controller.set('autenticado', False)
        main(controller, st)
        st.rerun()

    # Arredondar os cantos da imagem
    rounded_image = round_image_corners(image, radius=100)

    # Exibir a imagem em colunas
    col1, col2 = st.columns([1, 8])

    with col1:
        st.image(rounded_image, width=60)

    with col2:
        nome_usuario = controller.get("nome")
        colored_header(
            label="CrediChat",
            description=f"Bem-vindo {nome_usuario}. Estou aqui para auxiliar você!",
            color_name="blue-green-70",
        )
    # st.write(controller.getAll())

    # Obtendo o caminho absoluto do diretório
    current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
    logo_path = current_dir / "images/Sicoob Logo.png"

    # Construindo o caminho absoluto para a foto sicoob
    sicoob_image_path = current_dir / "images/sicoob.jpg"

    # Carregar a imagem usando PIL
    logo_image = Image.open(sicoob_image_path)

    # Arredondar os cantos da imagem da logo
    rounded_logo = round_image_corners(logo_image, radius=50)  # Ajuste o raio conforme necessário

    # Sidebar image
    st.sidebar.image(rounded_logo, caption="IA Assistant CREDICAF", use_column_width=True)

    current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
    logo_path = current_dir / "images/Sicoob Logo.png"
    logo_icone = Image.open(logo_path)

    # URL da imagem do usuário
    foto = controller.get('foto')
    if foto is None:
        url_imagem = logo_path
    else:
        url_imagem = f'https://intranet.sicoobcredicaf.com.br/sys/conteudo/usuarios/{foto}'

    try:
        # Carregar a imagem usando PIL
        image = Image.open(requests.get(url_imagem, stream=True).raw)
    except:
        controller.set('autenticado', False)
        main(controller, st)
        st.rerun()

    # Arredondar os cantos da imagem
    foto_usuario = round_image_corners(image, radius=100)

    # Query type selection in the sidebar (value retrieved from cookies)
    with st.sidebar.expander("🔍 Tipo de Consulta", expanded=True):
        cookie_query_option = controller.get('ck_query_option')
        if cookie_query_option is None:
            cookie_query_option = 'Consulta Simples'

        query_option = st.radio(
            "Escolha o tipo de consulta:",
            ["Consulta Simples", "Consulta à Base de Conhecimento", "Consulta SQL", "Consulta CSV",
             "Consulta/Resumo Vídeos Youtube", "Consulta à Documentação Online"],
            index=["Consulta Simples", "Consulta à Base de Conhecimento", "Consulta SQL", "Consulta CSV",
                   "Consulta/Resumo Vídeos Youtube", "Consulta à Documentação Online"].index(cookie_query_option),
            key="wdg_query_option"
        )
        controller.set('ck_query_option', query_option)

    # Configuration options in the sidebar (values retrieved from cookies)
    with st.sidebar.expander("⚙️ Configurações", expanded=False):
        cookie_gerar_audio_response = controller.get('ck_gerar_audio_response')
        if cookie_gerar_audio_response is None:
            cookie_gerar_audio_response = False

        gerar_audio_response = st.checkbox("Gerar Áudio-Resposta", value=cookie_gerar_audio_response,
                                           key="wdg_gerar_audio_response")
        controller.set('ck_gerar_audio_response', gerar_audio_response)

        if gerar_audio_response:
            cookie_voice_box = controller.get('ck_voice_box')
            if cookie_voice_box is None:
                cookie_voice_box = 'nova'

            voice_box = st.selectbox(
                "Opções de voz 🗣️",
                ["nova", "alloy", "echo", "fable", "onyx", "shimmer"],
                index=["nova", "alloy", "echo", "fable", "onyx", "shimmer"].index(cookie_voice_box),
                key="wdg_voice_box"
            )
            controller.set('ck_voice_box', voice_box)

            cookie_model_voice = controller.get('ck_model_voice')
            if cookie_model_voice is None:
                cookie_model_voice = 'tts-1'

            model_voice = st.selectbox(
                "Opções de modelo de voz 🤖",
                ["tts-1", "tts-1-hd"],
                index=["tts-1", "tts-1-hd"].index(cookie_model_voice),
                key="wdg_model_voice"
            )
            controller.set('ck_model_voice', model_voice)

            cookie_autoplay_audio_response = controller.get('ck_autoplay_audio_response')
            if cookie_autoplay_audio_response is None:
                cookie_autoplay_audio_response = False

            autoplay_audio_response = st.checkbox(
                "Autoplay Áudio Resposta",
                value=cookie_autoplay_audio_response,
                key="wdg_autoplay_audio_response"
            )
            controller.set('ck_autoplay_audio_response', autoplay_audio_response)

        cookie_llm_class = controller.get('ck_llm_class')
        if cookie_llm_class is None:
            cookie_llm_class = 'Openai'

        llm_class = st.selectbox(
            "Opções de LLM 🤖",
            ["Openai", "Google", "NLPCloud"],
            index=["Openai", "Google", "NLPCloud"].index(cookie_llm_class),
            key="wdg_llm_class"
        )
        controller.set('ck_llm_class', llm_class)

        if llm_class == "Openai":
            cookie_llm_model_openai = controller.get('ck_llm_model_openai')
            if cookie_llm_model_openai is None:
                cookie_llm_model_openai = 'gpt-4o-mini'

            llm_model_openai = st.selectbox(
                "Escolha o modelo OpenAI LLM",
                ['gpt-3.5-turbo', 'gpt-4o-mini', 'gpt-4o'],
                index=['gpt-3.5-turbo', 'gpt-4o-mini', 'gpt-4o'].index(cookie_llm_model_openai),
                key="wdg_llm_model_openai"
            )
            controller.set('ck_llm_model_openai', llm_model_openai)

        elif llm_class == "Google":
            cookie_llm_model_google = controller.get('ck_llm_model_google')
            if cookie_llm_model_google is None:
                cookie_llm_model_google = 'gemini-1.5-flash'

            llm_model_google = st.selectbox(
                "Escolha o modelo Google LLM",
                ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro'],
                index=['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro'].index(cookie_llm_model_google),
                key="wdg_llm_model_google"
            )
            controller.set('ck_llm_model_google', llm_model_google)

        cookie_temperature = controller.get('ck_temperature')
        if cookie_temperature is None:
            cookie_temperature = 0.5

        temperature = st.number_input(
            "Temperatura para a LLM:",
            min_value=0.0, max_value=1.0,
            value=cookie_temperature,
            step=0.1, format="%.1f", key="wdg_temperature"
        )
        controller.set('ck_temperature', temperature)

        # Embedding settings
        cookie_embeddings_class = controller.get('ck_embeddings_class')
        if cookie_embeddings_class is None:
            cookie_embeddings_class = "Openai"  # Valor padrão

        embeddings_class = st.selectbox(
            "Opções de embedding 🤖",
            ["Openai", "Google"],
            index=["Openai", "Google"].index(cookie_embeddings_class),
            key="wdg_embeddings_class"
        )
        controller.set('ck_embeddings_class', embeddings_class)

        if embeddings_class == "Openai":
            cookie_embeddings_model_openai = controller.get('ck_embeddings_model_openai')
            if cookie_embeddings_model_openai is None:
                cookie_embeddings_model_openai = "text-embedding-ada-002"  # Valor padrão

            embeddings_model_openai = st.selectbox(
                "Escolha o modelo OpenAI Embeddings",
                ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
                index=["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"].index(
                    cookie_embeddings_model_openai),
                key="wdg_embeddings_model_openai"
            )
            controller.set('ck_embeddings_model_openai', embeddings_model_openai)

        elif embeddings_class == "Google":
            cookie_embeddings_model_google = controller.get('ck_embeddings_model_google')
            if cookie_embeddings_model_google is None:
                cookie_embeddings_model_google = "models/embedding-001"  # Valor padrão

            embeddings_model_google = st.selectbox(
                "Escolha o modelo Google Embeddings",
                ["models/embedding-001"],
                index=["models/embedding-001"].index(cookie_embeddings_model_google),
                key="wdg_embeddings_model_google"
            )
            controller.set('ck_embeddings_model_google', embeddings_model_google)

        # Context input for LLM
        cookie_llm_context_structural = controller.get('ck_llm_context_structural')
        if cookie_llm_context_structural is None:
            cookie_llm_context_structural = f'Meu nome é {controller.get("nome")}'  # Valor padrão

        llm_context_structural = st.text_area(
            "Contexto para LLM:",
            help="Insira um contexto para seu assistente.",
            value=cookie_llm_context_structural,
            key="wdg_llm_context_structural"
        )
        controller.set('ck_llm_context_structural', llm_context_structural)

        if query_option == "Consulta à Base de Conhecimento":
            with st.sidebar.expander("⚙️ Configurações Especiais de Documentos", expanded=False):

                # Verifica se há um valor no cookie 'ck_llm_context_pdf', caso contrário, define um valor padrão
                cookie_llm_context_pdf = controller.get('ck_llm_context_pdf')
                if cookie_llm_context_pdf is None:
                    cookie_llm_context_pdf = ''  # Valor padrão

                # Campo para inserir o contexto para a LLM
                llm_context_pdf = st.text_area(
                    "Contexto para LLM Documentos:",
                    help="Insira um contexto adicional que deseja fornecer para a LLM durante a consulta.",
                    value=cookie_llm_context_pdf,
                    key="wdg_llm_context_pdf"
                )
                controller.set('ck_llm_context_pdf', llm_context_pdf)

                # Carregador de arquivos com suporte a múltiplos tipos de documentos
                uploaded_files_pdf = st.file_uploader(
                    "Carregue um ou mais arquivos Documentos:",
                    accept_multiple_files=True,
                    type=["pdf", "docx", "txt", "mp3", "mp4", "opus"],
                    key="wdg_uploaded_files_pdf"
                )

                # Se os arquivos forem carregados, salvá-los no controller e chamar a função add_uploaded_files
                if uploaded_files_pdf:
                    controller.set('ck_uploaded_files_pdf', uploaded_files_pdf)
                    add_uploaded_files(uploaded_files_pdf, st)

        if query_option == "Consulta CSV":
            with st.sidebar.expander("⚙️ Configurações Especiais de CSV", expanded=False):

                # Verifica se há um valor no cookie 'ck_encoding_option'
                cookie_encoding_option = controller.get('ck_encoding_option')
                if cookie_encoding_option is None:
                    cookie_encoding_option = 'ISO-8859-1'  # Valor padrão

                # Escolha da codificação de arquivos CSV
                encoding_option = st.selectbox(
                    "Escolha a codificação dos arquivos CSV:",
                    ['ISO-8859-1', 'utf-8', 'utf-16'],
                    index=['ISO-8859-1', 'utf-8', 'utf-16'].index(cookie_encoding_option),
                    help="Escolha a codificação correta dos arquivos CSV para evitar erros de decodificação.",
                    key="wdg_encoding_option"
                )
                controller.set('ck_encoding_option', encoding_option)

                # Verifica se há um valor no cookie 'ck_delimiter_option'
                cookie_delimiter_option = controller.get('ck_delimiter_option')
                if cookie_delimiter_option is None:
                    cookie_delimiter_option = ','  # Valor padrão

                # Delimitador de CSV
                delimiter_option = st.text_input(
                    "Delimitador de CSV:",
                    value=cookie_delimiter_option,
                    help="Especifique o delimitador usado nos arquivos CSV, por exemplo, ',' ou ';'.",
                    key="wdg_delimiter_option"
                )
                controller.set('ck_delimiter_option', delimiter_option)

                # Número máximo de linhas para exibir
                max_rows = controller.get('ck_max_rows')
                if max_rows is None:
                    max_rows = 10  # Valor padrão

                max_rows = st.number_input(
                    "Número máximo de linhas para exibir:",
                    min_value=1,
                    max_value=10,
                    value=max_rows,
                    help="Defina o número máximo de linhas a serem exibidas para cada arquivo CSV.",
                    key="wdg_max_rows"
                )
                controller.set('ck_max_rows', max_rows)

                # Pular linhas em branco
                skip_blank_lines = controller.get('ck_skip_blank_lines')
                if skip_blank_lines is None:
                    skip_blank_lines = True  # Valor padrão

                skip_blank_lines = st.checkbox(
                    "Pular linhas em branco",
                    value=skip_blank_lines,
                    key="wdg_skip_blank_lines"
                )
                controller.set('ck_skip_blank_lines', skip_blank_lines)

                # Contexto para LLM CSV
                llm_context_csv = controller.get('ck_llm_context_csv')
                if llm_context_csv is None:
                    llm_context_csv = ''  # Valor padrão

                llm_context_csv = st.text_area(
                    "Contexto para LLM CSV:",
                    help="Insira um contexto adicional que deseja fornecer para a LLM durante a consulta.",
                    value=llm_context_csv,
                    key="wdg_llm_context_csv"
                )
                controller.set('ck_llm_context_csv', llm_context_csv)

                # Formatar para Excel no padrão CREDICAF
                format_excel_credicaf = controller.get('ck_format_excel_credicaf')
                if format_excel_credicaf is None:
                    format_excel_credicaf = True  # Valor padrão

                format_excel_credicaf = st.checkbox(
                    "Formatar para Excel no Padrão CREDICAF",
                    value=format_excel_credicaf,
                    help="Selecione se deseja que os dados sejam formatados para Excel no padrão CREDICAF.",
                    key="wdg_format_excel_credicaf"
                )
                controller.set('ck_format_excel_credicaf', format_excel_credicaf)

                # Mostrar arquivos concatenados
                show_concatenated_files = controller.get('ck_show_concatenated_files')
                if show_concatenated_files is None:
                    show_concatenated_files = True  # Valor padrão

                show_concatenated_files = st.checkbox(
                    "Mostrar arquivos concatenados",
                    value=show_concatenated_files,
                    help="Selecione para visualizar todos os arquivos CSV carregados como um único DataFrame concatenado.",
                    key="wdg_show_concatenated_files"
                )
                controller.set('ck_show_concatenated_files', show_concatenated_files)

        if query_option == "Consulta à Documentação Online":
            with st.sidebar.expander("⚙️ Configurações Especiais de Documentação Online", expanded=False):

                # Verifica se há um valor salvo no controller
                llm_context_doc_on = controller.get('ck_llm_context_doc_on')
                if llm_context_doc_on is None:
                    llm_context_doc_on = ''  # Define o valor padrão

                # Campo para inserir o contexto para a LLM
                llm_context_doc_on = st.text_area(
                    "Contexto para LLM da Documentação:",
                    help="Insira um contexto adicional que deseja fornecer para a LLM durante a consulta.",
                    value=llm_context_doc_on,
                    key="wdg_llm_context_doc_on"
                )
                controller.set('ck_llm_context_doc_on', llm_context_doc_on)

    # Botão para sair da conta
    if st.sidebar.button('Sair da Conta'):
        controller.set('autenticado', False)
        st.write("Ate mais, {0}!".format(controller.get('nome')))
        st.write('Atualize a página para realizar novas consultas.')
        # for key in controller.getAll().keys():  # Obtém todas as chaves
        #     controller.set(key, None)
        st.rerun()

    llm_model = None
    if llm_class == "Google":
        llm_model = llm_model_google
    elif llm_class == "Openai":
        llm_model = llm_model_openai

    embedding_model = None
    if embeddings_class == "Google":
        embedding_model = embeddings_model_google
    elif embeddings_class == "Openai":
        embedding_model = embeddings_model_openai

    llms_indisponiveis = ["gpt-3.5-turbo", "gpt-4o"]
    if llm_model in llms_indisponiveis:
        st.error("Modelo de LLM indisponível no momento. Por favor, escolha outro.")
        st.stop()

    embeddings = get_embeddings(embeddings_class, embedding_model)
    llm_answer = get_llm(llm_model, temperature)

    if 'historico' not in st.session_state:
        st.session_state.historico = []


    if query_option == "Consulta Simples":
        # Inicializa o estado da sessão, se necessário
        if "messages_consulta_simples" not in st.session_state:
            st.session_state.messages_consulta_simples = []
        try:
            with bottom():
                # Criar colunas para o botão de limpeza e a caixa de texto
                col1, col2 = st.columns([1, 8], gap="small")

                with col1:
                    # Botão de limpar sem espaçamento adicional
                    if st.button("🔃", key="clear_button", use_container_width=True, help='Limpar historico'):
                        st.session_state.messages_consulta_simples = []
                        st.session_state.contexto_previo = ''
                        st.rerun()

                with col2:
                    # Entrada de texto para a pergunta
                    pergunta = st.text_input(placeholder="Digite sua pergunta:", key="simple_question_input",
                                             label_visibility="collapsed", label="Pergunta:")

                # Se houver uma pergunta
                if pergunta:
                    # Adiciona a pergunta do usuário ao histórico
                    st.session_state.messages_consulta_simples.append({"role": "user", "content": pergunta})

                    # Recupera o contexto existente de interações anteriores
                    contexto_previo = st.session_state.get('contexto_previo', '')

                    # Chama a função converse passando a pergunta e o contexto anterior
                    resposta_obtida = converse(
                        question=pergunta,
                        llm_answer=llm_answer,
                        prefix=llm_context_structural,
                    )

                    # Atualiza o contexto com a nova interação
                    st.session_state.contexto_previo = f"{contexto_previo}\nUser: {pergunta}\nAgent: {resposta_obtida}"

                    # Adiciona a resposta ao histórico
                    st.session_state.messages_consulta_simples.append({"role": "assistant", "content": resposta_obtida})

                    # Se a opção de gerar áudio estiver habilitada
                    if gerar_audio_response:
                        gerar_audio(st, model_voice, voice_box, resposta_obtida,
                                    autoplay=autoplay_audio_response)

            # Exibe o histórico de mensagens do chat com imagens
            for message in st.session_state.messages_consulta_simples:
                if message["role"] == "user":
                    with st.chat_message("user", avatar=foto_usuario):  # Adiciona sua foto como avatar
                        st.write(message["content"])
                elif message["role"] == "assistant":
                    with st.chat_message("assistant", avatar=logo_icone):  # Adiciona a foto do robô como avatar
                        st.write(message["content"])

        except Exception as e:
            print(e)
            st.error(f"Ocorreu um erro ao processar a sua pergunta: Tente novamente mais tarde.")
            st.write(e)
            st.stop()

    elif query_option == "Consulta à Base de Conhecimento":

        # Inicializa o estado da sessão, se necessário

        if "messages_base_conhecimento" not in st.session_state:
            st.session_state.messages_base_conhecimento = []

        with st.spinner("Processando Documentos..."):
            try:
                st.write("Documentos disponíveis:")
                pdf_files, directory_files, uploaded_files = list_documents(pdf_directory, st)
                chosen_pdf_id = st.selectbox("Escolha o documento para consulta:", options=["TODOS"] + pdf_files,
                                             format_func=lambda x: x.split("/")[-1],
                                             key="document_selector")

                with bottom():
                    # Criar colunas para o botão de limpeza e a caixa de texto
                    col1, col2 = st.columns([1, 8], gap="small")

                    with col1:
                        if st.button("🔃", key="clear_button", use_container_width=True, help='Limpar historico'):
                            # Limpa o histórico de mensagens da base de conhecimento
                            st.session_state.messages_base_conhecimento = []
                            st.session_state.user_question_input = ""  # Também limpa o campo de entrada do usuário
                            st.rerun()

                    with col2:
                        # Caixa de texto para a pergunta
                        user_question = st.text_input("Faça uma pergunta e vamos tentar resolver",
                                                     # Pegue o valor da sessão
                                                     value=st.session_state.get("user_question_input", ""),
                                                     placeholder="Digite sua pergunta:", label_visibility="collapsed")


                    if user_question:
                        # Adiciona a pergunta do usuário ao histórico
                        st.session_state.messages_base_conhecimento.append(
                            {"role": "user", "content": user_question})

                        # Chama a função user_input para obter a resposta
                        resposta_obtida = user_input(user_question, llm_answer, st, chosen_pdf_id, embeddings,
                                                     llm_context_structural, llm_context_pdf)

                        # Adiciona a resposta ao histórico
                        st.session_state.messages_base_conhecimento.append(
                            {"role": "assistant", "content": resposta_obtida})

                        # Se a opção de gerar áudio estiver habilitada
                        if gerar_audio_response:
                            gerar_audio(st, model_voice, voice_box, resposta_obtida,
                                        autoplay=autoplay_audio_response)
                        # Limpa a caixa de texto após enviar
                        st.session_state.user_question_input = ""

                # Exibe o histórico de mensagens do chat

                for message in st.session_state.messages_base_conhecimento:
                    if message["role"] == "user":
                        with st.chat_message("user", avatar=foto_usuario):  # Adiciona sua foto como avatar
                            st.write(message["content"])
                    elif message["role"] == "assistant":
                        with st.chat_message("assistant", avatar=logo_icone):  # Adiciona a foto do robô como avatar
                            st.write(message["content"])


            except Exception as e:
                st.error(f"Ocorreu um erro ao processar os documentos: {e}")

    elif query_option == "Consulta SQL":
        if "messages_consulta_sql" not in st.session_state:
            st.session_state.messages_consulta_sql = []
        try:
            # Conectar ao banco de dados
            db, table_info = get_db()
            st.write("Por favor, escolha uma das opções abaixo para continuar:")
            # Inicializar o grupo pré-selecionado como "Cliente"
            if "selected_group" not in st.session_state:
                st.session_state.selected_group = "cliente"

            # Estilos personalizados para os botões
            button_style = """
            <style>
            div.stButton > button {
                border: 2px solid transparent;
                padding: 0.6em;
            }
            div.stButton > button.selected {
                border: 2px solid #007BFF;
            }
            </style>
            """
            st.markdown(button_style, unsafe_allow_html=True)

            # Layout dos botões sem espaço entre eles
            col1, col2, col3 = st.columns([1, 1, 1])

            # Função para determinar a classe "selected"
            def is_selected(group):
                return st.session_state.selected_group == group

            # Botão "Cliente"
            with col1:
                if st.button("Gostaria de consultar informações de um cliente?", key="cliente_button"):
                    st.session_state.selected_group = "cliente"
                    st.session_state.messages_consulta_sql = []

            # Botão "Agência"
            with col2:
                if st.button("Precisa de informações sobre uma agência?", key="agencia_button"):
                    st.session_state.selected_group = "agencia"
                    st.session_state.messages_consulta_sql = []

            # Botão "Grupo Econômico"
            with col3:
                if st.button("Quer saber mais sobre um grupo econômico?", key="grupo_eco_button"):
                    st.session_state.selected_group = "grupo_economico"
                    st.session_state.messages_consulta_sql = []

            # Adicionar bordas azuis ao botão selecionado
            st.markdown(f"""
                <style>
                div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {{
                    border-color: {"#007BFF" if is_selected("cliente") else "transparent"};
                }}
                div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {{
                    border-color: {"#007BFF" if is_selected("agencia") else "transparent"};
                }}
                div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {{
                    border-color: {"#007BFF" if is_selected("grupo_economico") else "transparent"};
                }}
                </style>
            """, unsafe_allow_html=True)

            # Layout do input, botão de procurar e nome do cliente
            col_input, col_button, col_cliente = st.columns([3, 1, 2])

            if st.session_state.selected_group == "cliente":
                grupo_selecionado = st.session_state.selected_group
                # Função para validar se a entrada contém apenas números
                def validar_cpf_cnpj(cpf_cnpj):
                    return bool(re.match(r'^\d+$', cpf_cnpj))

                def buscar_nome_cliente(db, cpf_cnpj):
                    # Consultar o nome do cliente usando db.run
                    query = f"SELECT nom_cliente FROM T_SQL_CLIENTE WHERE num_cpf_cnpj = '{cpf_cnpj}'"  # Consulta com f-string
                    print(f"Query construída: {query}")  # Debug: mostra a consulta construída

                    # Executando a consulta e retornando o resultado
                    try:
                        print("Executando a consulta...")  # Debug: antes de executar a consulta
                        resultado = db.run(query)  # Consulta executada como string formatada
                        print("Consulta executada com sucesso.")  # Debug: após execução da consulta

                        # Verificar o formato do resultado
                        print(f"Resultado da consulta (tipo): {type(resultado)}")  # Debug: tipo do resultado
                        print(f"Resultado da consulta: {resultado}")  # Debug: imprime o resultado da consulta

                        # Se o resultado for uma string, tentamos interpretá-lo
                        if isinstance(resultado, str):
                            print("O resultado é uma string. Tentando interpretá-lo...")  # Debug
                            try:
                                resultado = eval(resultado)  # Tenta converter a string em uma estrutura de dados
                            except Exception as e:
                                print(f"Erro ao interpretar o resultado: {e}")
                                return "Cliente não encontrado. Verifique se o CPF ou CNPJ informado é correto."

                        # Verificar se o resultado é uma lista e não está vazia
                        if isinstance(resultado, list) and resultado:
                            print("Cliente encontrado.")  # Debug: cliente encontrado
                            return resultado[0][0]  # Retorna o nome do cliente corretamente
                        else:
                            print("Nenhum cliente encontrado.")  # Debug: cliente não encontrado
                            return "Cliente não encontrado."
                    except Exception as err:
                        print(f"Erro ao executar a consulta: {err}")  # Debug: imprime o erro
                        return f"Erro: {err}"

                def buscar_cpf_por_nome(db, nome):
                    # Consultar o CPF do cliente usando db.run
                    query = f"SELECT num_cpf_cnpj FROM T_SQL_CLIENTE WHERE nom_cliente LIKE '{nome}%'"
                    print(f"Query construída: {query}")

                    try:
                        print("Executando a consulta...")
                        resultado = db.run(query)
                        print("Consulta executada com sucesso.")

                        if isinstance(resultado, str):
                            print("O resultado é uma string. Tentando interpretá-lo...")
                            try:
                                resultado = eval(resultado)
                            except Exception as e:
                                print(f"Erro ao interpretar o resultado: {e}")
                                return "Cliente não encontrado. Verifique se o nome informado é correto."

                        if isinstance(resultado, list) and resultado:
                            print("CPF encontrado.")
                            return resultado[0][0]  # Retorna o CPF
                        else:
                            print("Nenhum CPF encontrado.")
                            return "Cliente não encontrado."
                    except Exception as err:
                        print(f"Erro ao executar a consulta: {err}")
                        return f"Erro: {err}"

                # Colunas para organizar a interface
                col_input, col_dropdown, col_button, col_cliente = st.columns([3, 2, 2, 5])

                my_grid = grid([3, 2, 2, 5], vertical_align="bottom")

                # Elemento de entrada com dica e sem título
                cookie_cpf_cnpj_sql = controller.get('ck_cpf_cnpj_sql')
                if cookie_cpf_cnpj_sql is None:
                    cookie_cpf_cnpj_sql = ""
                cpf_cnpj = my_grid.text_input("CPF OU CNPJ", placeholder="CPF ou CNPJ", key="cpf_cnpj_input",
                                                 value=cookie_cpf_cnpj_sql, label_visibility="collapsed")
                controller.set('ck_cpf_cnpj_sql', cpf_cnpj)

                # Dropdown para selecionar entre CPF e Nome
                cookie_opcao_consulta_sql = controller.get('ck_opcao_consulta_sql')
                if cookie_opcao_consulta_sql is None:
                    cookie_opcao_consulta_sql = 'CPF'
                search_type = my_grid.selectbox("Buscar por:", ["CPF", "Nome"],
                                                   index=["CPF", "Nome"].index(cookie_opcao_consulta_sql), label_visibility="collapsed")

                # Limpar CPF/CNPJ para validação se o tipo de busca for CPF
                cpf_cnpj_limpo = cpf_cnpj.replace(" ", "").replace(".", "").replace("-", "").replace("/", "")
                cpf_cnpj_valido = search_type == "CPF" and validar_cpf_cnpj(cpf_cnpj_limpo)

                # Botão de procurar, habilitado se o tipo de busca for "Nome" ou CPF válido
                if my_grid.button("Procurar", key="procurar_button",
                                     disabled=(search_type == "CPF" and not cpf_cnpj_valido), use_container_width=True):
                    if search_type == "CPF":
                        nome_cliente = buscar_nome_cliente(db, cpf_cnpj_limpo)
                        controller.set('ck_nome_sql', nome_cliente.title())
                        st.session_state.cpf_cnpj_sql = cpf_cnpj_limpo
                    else:  # Se o dropdown for "Nome"
                        nome_cliente = cpf_cnpj  # O texto inserido será considerado o nome
                        cpf_cnpj_result = buscar_cpf_por_nome(db, nome_cliente)
                        controller.set('ck_nome_sql', nome_cliente.title())
                        controller.set('ck_cpf_cnpj_sql', cpf_cnpj_result)

                # Mensagem de erro se o CPF/CNPJ for inválido
                if not cpf_cnpj_valido and cpf_cnpj and search_type == "CPF":
                    my_grid.error(
                        "Por favor, insira apenas números no CPF ou CNPJ, sem espaços ou caracteres especiais.")

                # Exibir resultados, se aplicável
                if controller.get('ck_nome_sql') is not None:
                    if search_type == "CPF":
                        my_grid.write(f"Nome do cliente: {controller.get('ck_nome_sql')}")
                    else:
                        my_grid.write(f"CPF/CNPJ do cliente: {controller.get('ck_cpf_cnpj_sql')}")

            elif st.session_state.selected_group == "agencia":
                grupo_selecionado = st.session_state.selected_group
                @st.cache_data()  # O cache será armazenado por 10 minutos (600 segundos)
                def obter_agencias_do_sql(_db):
                    query = "SELECT nom_agencia FROM T_SQL_AGENCIA"
                    try:
                        resultado = _db.run(query)
                        print(f"Resultado bruto: {resultado}")

                        # Verificar se o resultado é uma string e tentar convertê-lo de volta para lista de tuplas
                        if isinstance(resultado, str):
                            try:
                                # Converter a string para um objeto de lista usando ast.literal_eval
                                resultado = ast.literal_eval(resultado)
                                print(f"Resultado convertido para lista: {resultado}")
                            except Exception as err:
                                st.error(f"Erro ao converter o resultado de string para lista: {err}")
                                return []

                        # Agora verificar se o resultado é uma lista de tuplas
                        if isinstance(resultado, list) and resultado:
                            # Extrair os nomes das agências da lista de tuplas
                            lista_agencias = [row[0] for row in resultado]  # row[0] pega o primeiro item da tupla
                            print(f"Lista de agências: {lista_agencias}")
                            return lista_agencias
                        else:
                            return []
                    except Exception as err:
                        st.error(f"Erro ao buscar agências: {err}")
                        return []

                with col_input:
                    lista_agencias = obter_agencias_do_sql(db)
                    agencia_selecionada = st.selectbox("Escolha uma agência", lista_agencias, key="agencia_select",
                                                       label_visibility="collapsed")
                with col_button:
                    controller.set('ck_agencia_sql', agencia_selecionada)

                with col_cliente:
                    agencia_selecionada = controller.get('ck_agencia_sql')
                    if agencia_selecionada is not None:
                        st.write(f"Nome da Agência: {agencia_selecionada}")

            elif st.session_state.selected_group == "grupo_economico":
                grupo_selecionado = st.session_state.selected_group
                @st.cache_data(ttl=600)  # Cache por 10 minutos
                def obter_grupos_economicos_do_sql(_db):
                    query = "SELECT cod_grupo_economico, nom_grupo_economico FROM T_SQL_GRUPO_ECONOMICO"
                    try:
                        resultado = _db.run(query)
                        print(f"Resultado bruto: {resultado}")

                        # Verificar se o resultado é uma string e tentar convertê-lo de volta para lista de tuplas
                        if isinstance(resultado, str):
                            try:
                                # Converter a string para um objeto de lista usando ast.literal_eval
                                resultado = ast.literal_eval(resultado)
                                print(f"Resultado convertido para lista: {resultado}")
                            except Exception as err:
                                st.error(f"Erro ao converter o resultado de string para lista: {err}")
                                return []

                        # Agora verificar se o resultado é uma lista de tuplas
                        if isinstance(resultado, list) and resultado:
                            # Retorna uma lista de tuplas (numero_grupo, nome_grupo)
                            return resultado
                        else:
                            return []
                    except Exception as err:
                        st.error(f"Erro ao buscar grupos econômicos: {err}")
                        return []
                lista_grupos = obter_grupos_economicos_do_sql(db)  # Busca os grupos econômicos do SQL
                if lista_grupos:
                    with col_input:
                        # Exibe os grupos econômicos no selectbox com o formato "numero_grupo - nome_grupo"
                        grupo_selecionado = st.selectbox(
                            "Escolha um grupo econômico",
                            [f"{grupo[1]} - {grupo[0]}" for grupo in lista_grupos],  # Exibir "numero - nome"
                            key="grupo_eco_select"
                        )
                    with col_button:
                        # Separar o número e o nome do grupo selecionado
                        numero_grupo, nome_grupo = grupo_selecionado.split(" - ")

                        # Usar o controller.set para armazenar o ID e o nome do grupo selecionado
                        controller.set('ck_grupo_economico_id', numero_grupo)
                        controller.set('ck_grupo_economico_nome', nome_grupo)

                    with col_cliente:
                        # Recuperar o ID e o nome do grupo econômico do controller
                        ck_grupo_economico_id = controller.get('ck_grupo_economico_id')
                        ck_grupo_economico_nome = controller.get('ck_grupo_economico_nome')

                        if ck_grupo_economico_id is not None and ck_grupo_economico_nome is not None:
                            st.write(f"Grupo Econômico: {ck_grupo_economico_nome} (ID: {ck_grupo_economico_id})")
                else:
                    st.write("Nenhum grupo econômico encontrado.")

            # Campo de pergunta SQL
            if 'selected_group' in st.session_state:
                grupo_selecionado = st.session_state.selected_group
                pergunta = ''
                titulo_direcionado = ''
                if grupo_selecionado == 'cliente':
                    nome_cliente_sql = controller.get('ck_nome_sql')
                    cpf_cnpj_sql = controller.get('ck_cpf_cnpj_sql')
                    if nome_cliente_sql:
                        titulo_direcionado = f'Digite sua pergunta sobre o cliente {nome_cliente_sql}:'
                    else:
                        titulo_direcionado = "Digite sua pergunta:"

                    # Adiciona informações ao final da pergunta, se disponíveis
                    if cpf_cnpj_sql:
                        pergunta += f' CPF/CNPJ: {cpf_cnpj_sql}'
                    if nome_cliente_sql:
                        pergunta += f' Cliente: {nome_cliente_sql}'

                elif grupo_selecionado == 'agencia':
                    if agencia_selecionada:
                        titulo_direcionado = f'Digite sua pergunta sobre a agência {agencia_selecionada}:'
                    else:
                        titulo_direcionado = "Digite sua pergunta:"

                    # Adiciona informações ao final da pergunta, se disponíveis
                    if agencia_selecionada:
                        pergunta += (f""" Agência: {agencia_selecionada}. Use este nome para identificar a agência na tabela T_SQL_AGENCIA. 
                                          Em vez de responder "A agência chamada...", responda "A agência de NOME...". """)

                elif grupo_selecionado == 'grupo_economico':
                    if ck_grupo_economico_id:
                        titulo_direcionado = f'Digite sua pergunta sobre o grupo econômico {ck_grupo_economico_nome} - {ck_grupo_economico_id}:'
                    else:
                        titulo_direcionado = "Digite sua pergunta:"

                    if pergunta:
                        # Adiciona informações ao final da pergunta, se disponíveis
                        if ck_grupo_economico_nome:
                            pergunta += (f""" Grupo Econômico: {ck_grupo_economico_nome}. Caso seja interessante, segue também
                                              o código do grupo econômico: {ck_grupo_economico_id}. Ambas informações são encontradas
                                              na tabela T_SQL_GRUPO_ECONOMICO.""")

                with bottom():
                    # Criar colunas para o botão de limpeza e a caixa de texto
                    col1, col2 = st.columns([1, 8], gap="small")

                    with col1:
                        if st.button("🔃", key="clear_button", use_container_width=True, help='Limpar historico'):
                                st.session_state.messages_consulta_sql = []
                                st.session_state.contexto_previo = ''
                                st.rerun()

                    with col2:
                        # Entrada de texto para a pergunta
                        question = st.text_input(placeholder=titulo_direcionado, label='Digite sua pergunta', label_visibility="collapsed")
                        question_final = question + pergunta
                        print(f"A pergunta que chegou aqui na column2 é: {question_final}")

                    if question:
                        # Adiciona a pergunta do usuário ao histórico
                        st.session_state.messages_consulta_sql.append(
                            {"role": "user", "content": question})

            if question:
                with st.spinner("Carregando resposta..."):
                    resposta_obtida = converse_com_sql(
                        question=question_final,
                        llm_answer=llm_answer,
                        db=db,
                        embeddings=embeddings,
                        st=st,
                        prefix=llm_context_structural
                    )

                # Adiciona a resposta ao histórico
                st.session_state.messages_consulta_sql.append(
                    {"role": "assistant", "content": resposta_obtida})

                if gerar_audio_response:
                    gerar_audio(st, model_voice, voice_box, resposta_obtida, autoplay=autoplay_audio_response)
                add_vertical_space(1)
                # st.write(resposta_obtida)
                # Limpa a caixa de texto após enviar
                st.session_state.user_question_input = ""

                # Exibe o histórico de mensagens do chat
            for message in st.session_state.messages_consulta_sql:
                if message["role"] == "user":
                    with st.chat_message("user", avatar=foto_usuario):  # Adiciona sua foto como avatar
                        st.write(message["content"])
                elif message["role"] == "assistant":
                    with st.chat_message("assistant", avatar=logo_icone):  # Adiciona a foto do robô como avatar
                        st.write(message["content"])

        except Exception as e:
            print(e)
            st.error(f"Ocorreu um erro ao conectar com o banco de dados: Tente novamente mais tarde.")
            st.write(e)
            st.stop()

    elif query_option == "Consulta CSV":
        # Inicializa o estado da sessão, se necessário
        if "messages_csv" not in st.session_state:
            st.session_state.messages_csv = []

        uploaded_files = st.file_uploader(
            "Carregue um ou mais arquivos CSV:",
            accept_multiple_files=True,
            type=["csv"],
            key="csv_file_uploader"

        )

        if uploaded_files:
            dataframes = []

            for file in uploaded_files:
                try:
                    df = pd.read_csv(file,
                                     encoding=encoding_option,
                                     delimiter=delimiter_option,
                                     skip_blank_lines=skip_blank_lines)
                    dataframes.append(df)
                except UnicodeDecodeError:
                    st.error(
                        f"Erro ao decodificar o arquivo {file.name}. Tente outro arquivo ou use uma codificação diferente.")
                    continue

            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                st.session_state.combined_df = combined_df
                st.write("Dados carregados:")
                if show_concatenated_files:
                    st.dataframe(combined_df.head(max_rows))

                else:
                    for df in dataframes:
                        st.dataframe(df)

                with bottom():
                    # Criar colunas para o botão de limpeza e a caixa de texto
                    col1, col2 = st.columns([1, 8], gap="small")

                    with col1:
                        if st.button("🔃", key="clear_button", use_container_width=True, help='Limpar historico'):
                            st.session_state.messages_csv = []
                            st.session_state.contexto_previo = ''
                            st.rerun()

                    with col2:
                        pergunta_csv = st.text_input(placeholder="Digite sua pergunta:", key="sql_question_input", label='',
                                                     label_visibility="collapsed")
                        if pergunta_csv:
                            try:
                                resposta_obtida = converse_com_csv(pergunta_csv,
                                                                   llm_answer,
                                                                   st,
                                                                   llm_context_csv,
                                                                   llm_context_structural,
                                                                   max_rows,
                                                                   format_excel_credicaf)

                                # Adiciona a pergunta do usuário ao histórico
                                st.session_state.messages_csv.append({"role": "user", "content": pergunta_csv})

                                # Adiciona a resposta ao histórico
                                if isinstance(resposta_obtida, pd.DataFrame):
                                    st.session_state.messages_csv.append(
                                        {"role": "assistant", "content": "Resposta obtida em dataframe:"})
                                    st.session_state.messages_csv.append(
                                        {"role": "assistant", "content": resposta_obtida.to_html(index=False)})

                                elif isinstance(resposta_obtida, str):
                                    st.session_state.messages_csv.append({"role": "assistant", "content": resposta_obtida})
                                else:
                                    st.session_state.messages_csv.append(
                                        {"role": "assistant", "content": "Tipo de resposta desconhecido."})

                            except Exception as e:
                                st.error(f"Ocorreu um erro ao executar a consulta: {str(e)}")


                # Exibir a última mensagem após o botão de envio
                for message in st.session_state.messages_csv:
                    if message["role"] == "user":
                        with st.chat_message("user", avatar=foto_usuario):
                            st.write(message["content"])
                    elif message["role"] == "assistant":
                        with st.chat_message("assistant", avatar=logo_icone):
                            if message["content"].startswith("Resposta obtida em dataframe:"):
                                st.markdown(message["content"], unsafe_allow_html=True)
                            else:
                                st.write(message["content"])

    elif query_option == "Consulta/Resumo Vídeos Youtube":
        # Inicializa o estado da sessão, se necessário
        if "messages_youtube" not in st.session_state:
            st.session_state.messages_youtube = []
        try:

            with st.expander("Insira até 10 URLs", expanded=False):
                urls = []
                for i in range(10):
                    url = st.text_input(f"URL {i + 1}", key=f"url_{i}")
                    if url:
                        urls.append(url)

                # Exibir a lista de URLs inseridas
                if urls:
                    st.write("URLs inseridas:")
                    st.write(urls)

            if urls:
                # Entrada de texto para a pergunta
                with bottom():
                    # Criar colunas para o botão de limpeza e a caixa de texto
                    col1, col2 = st.columns([1, 8], gap="small")

                    with col1:
                        if st.button("🔃", key="clear_button", use_container_width=True, help='Limpar historico'):
                                st.session_state.messages_youtube = []
                                st.session_state.contexto_previo = ''
                                st.rerun()

                    with col2:
                        # Entrada de texto para a pergunta
                        pergunta = st.text_input(placeholder="Digite sua pergunta:", key="simple_question_input",
                                                 label_visibility="collapsed", label="Pergunta:")


                    # Se houver uma pergunta e ainda não tiver sido obtida uma resposta
                    if pergunta:

                        # Recupere o contexto existente de interações anteriores
                        contexto_previo = st.session_state.get('contexto_previo', '')

                        # Chama a função converse passando a pergunta e o contexto anterior
                        resposta_obtida = youtube_video_question(
                            user_question=pergunta,
                            llm=llm_answer,
                            st=st,
                            prefix=llm_context_structural,
                            videos=urls,
                            embeddings=embeddings
                        )

                        # Atualiza o contexto com a nova interação
                        st.session_state.contexto_previo = f"{contexto_previo}\nUser: {pergunta}\nAgent: {resposta_obtida}"

                        # Se a opção de gerar áudio estiver habilitada
                        if gerar_audio_response:
                            gerar_audio(st, model_voice, voice_box, resposta_obtida, autoplay=autoplay_audio_response)

                        # Mostra a resposta na interface
                        # st.write(resposta_obtida)

                    for message in st.session_state.messages_youtube:
                        if message["role"] == "user":
                            with st.chat_message("user", avatar=foto_usuario):  # Adiciona sua foto como avatar
                                st.write(message["content"])
                        elif message["role"] == "assistant":
                            with st.chat_message("assistant", avatar=logo_icone):  # Adiciona a foto do robô como avatar
                                st.write(message["content"])

        except Exception as e:
            print(e)
            st.error(f"Ocorreu um erro ao processar a sua pergunta: Tente novamente mais tarde.")
            st.stop()

    elif query_option == "Consulta à Documentação Online":
        # Inicializa o estado da sessão, se necessário
        if "messages_doc_online" not in st.session_state:
            st.session_state.messages_doc_online = []
        try:

            with st.expander("Insira até 10 URLs", expanded=False):
                urls = []
                for i in range(10):
                    url = st.text_input(f"URL {i + 1}", key=f"url_{i}")
                    if url:
                        urls.append(url)

                # Exibir a lista de URLs inseridas
                if urls:
                    st.write("URLs inseridas:")
                    st.write(urls)

            if urls:
                # Entrada de texto para a pergunta
                with bottom():
                    # Criar colunas para o botão de limpeza e a caixa de texto
                    col1, col2 = st.columns([1, 8], gap="small")

                    with col1:
                        if st.button("🔃", key="clear_button", use_container_width=True, help='Limpar historico'):
                                st.session_state.messages_doc_online = []
                                st.session_state.contexto_previo = ''
                                st.rerun()
                    with col2:
                        # Entrada de texto para a pergunta
                        pergunta = st.text_input(placeholder="Digite sua pergunta:", key="simple_question_input",
                                                 label_visibility="collapsed", label="Pergunta:")


                # Se houver uma pergunta e ainda não tiver sido obtida uma resposta
                if pergunta:

                    # Recupere o contexto existente de interações anteriores
                    contexto_previo = st.session_state.get('contexto_previo', '')

                    # Chama a função converse passando a pergunta e o contexto anterior
                    resposta_obtida = url_question(
                        user_question=pergunta,
                        llm=llm_answer,
                        st=st,
                        prefix=llm_context_structural,
                        urls=urls,
                        context_doc_on=llm_context_doc_on,
                        embeddings=embeddings
                    )

                    # Atualiza o contexto com a nova interação
                    st.session_state.contexto_previo = f"{contexto_previo}\nUser: {pergunta}\nAgent: {resposta_obtida}"

                    # Se a opção de gerar áudio estiver habilitada
                    if gerar_audio_response:
                        gerar_audio(st, model_voice, voice_box, resposta_obtida, autoplay=autoplay_audio_response)

                    # Mostra a resposta na interface
                    st.write(resposta_obtida)

            for message in st.session_state.messages_doc_online:
                if message["role"] == "user":
                    with st.chat_message("user", avatar=foto_usuario):  # Adiciona sua foto como avatar
                        st.write(message["content"])
                elif message["role"] == "assistant":
                    with st.chat_message("assistant", avatar=logo_icone):  # Adiciona a foto do robô como avatar
                        st.write(message["content"])

        except Exception as e:
            print(e)
            st.error(f"Ocorreu um erro ao processar a sua pergunta: Tente novamente mais tarde.")
            st.stop()

