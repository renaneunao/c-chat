import os
from PIL import Image, ImageDraw
import requests
from ldap3 import Server, Connection, NTLM, ALL

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

import warnings

# Suprime avisos específicos do Pydub
warnings.filterwarnings("ignore", category=RuntimeWarning)


def get_llm(model_name, temperature):
    from langchain_community.chat_models import ChatOllama
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    import google.generativeai as genai
    # Configure Generative AI with API key
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    # from langchain.chains import LLMChain
    from langchain_community.llms import NLPCloud


    if model_name == "gemini-1.5-flash":
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=temperature)
    elif model_name == "gemini-1.5-pro":
        return ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=temperature)
    elif model_name == "gemini-pro":
        return ChatGoogleGenerativeAI(model="gemini-pro", temperature=temperature)
    elif model_name == "gpt-3.5-turbo":
        return ChatOpenAI(model="gpt-3.5-turbo", temperature=temperature)
    elif model_name == "gpt-4o-mini":
        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
    elif model_name == "gpt-4o":
        return ChatOpenAI(model="gpt-4o", temperature=temperature)
    elif model_name == "llama3":
        return ChatOllama(model="llama3", temperature=temperature)
    elif model_name == "llama3.1:8b":
        return ChatOllama(model="llama3.1:8b", temperature=temperature)
    elif model_name == "default_nlpcloud":
        return NLPCloud()

def get_embeddings(embeddings_name, model):
    from langchain_openai import OpenAIEmbeddings
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    # Definir as instâncias de embedding
    google_embeddings = GoogleGenerativeAIEmbeddings(model=model)
    openai_embeddings = OpenAIEmbeddings(model=model)
    if embeddings_name == "Google":
        return google_embeddings
    elif embeddings_name == "Openai":
        return openai_embeddings

def autoplay_audio(file_path: str, placeholder, autoplay):
    import base64
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()

    # Construindo a tag <audio> com base no valor de autoplay
    autoplay_attr = "autoplay" if autoplay else ""

    md = f"""
    <audio controls {autoplay_attr}>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """

    placeholder.markdown(md, unsafe_allow_html=True)

def gerar_audio(st, model, voice, resposta_obtida, autoplay):
    audio_file_path = "output.mp3"
    try:
        # Create a placeholder for the audio player
        audio_placeholder = st.empty()
        # Check if the audio has already been generated
        if st.session_state.audio_generated:
            autoplay_audio(audio_file_path, audio_placeholder, autoplay=False)
            return
        else:
            with st.spinner('Gerando áudio...'):
                response = get_client_openai().audio.speech.create(
                    model=model,
                    voice=voice,
                    input=resposta_obtida
                )
                response.write_to_file(audio_file_path)

                # Clear any previous audio player
                audio_placeholder.empty()
                # Autoplay the generated audio
                autoplay_audio(audio_file_path, audio_placeholder, autoplay=autoplay)

                st.session_state.audio_generated = True
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o áudio: {e}")

def get_client_openai():
    from openai import OpenAI
    api = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api)
    return client

def get_db():
    from langchain_community.utilities import SQLDatabase
    # Carregar variáveis de conexão
    host = os.getenv('DB_HOST')
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    db_schema = os.getenv('DB_SCHEMA')
    db_port = int(os.getenv('DB_PORT', 3306))

    # Conectar ao banco de dados
    db = SQLDatabase.from_uri(
        f"mysql+mysqlconnector://{username}:{password}@{host}:{db_port}/{db_schema}?charset=utf8mb4&collation=utf8mb4_general_ci")

    table_info = db.get_table_info()

    return db, table_info

def atualizar_historico(pergunta, query_resposta, resposta, st):
    try:
        resposta_cortada = resposta[:1000]  # Cortar a resposta para no máximo 200 caracteres
    except:
        resposta_cortada = resposta
    st.session_state.historico.append((pergunta, query_resposta, resposta_cortada))
    # Manter apenas as últimas 5 perguntas e respostas
    if len(st.session_state.historico) > 5:
        st.session_state.historico.pop(0)

def gerar_contexto(st, prefix: str):
    if prefix != "":
        # Inicializa o contexto com o prefixo
        contexto = f"$$$==========Instructions, PAY ATTENTION: {prefix}==========$$$"
    else:
        # Inicializa o contexto vazio
        contexto = ""

    # Concatena as últimas 10 interações do histórico, limitando cada resposta a 200 caracteres
    for pergunta, query_resposta, resposta in st.session_state.historico[-10:]:
        resposta_truncada = resposta[:200]  # Limita a resposta a 200 caracteres
        contexto += f"Pergunta: {pergunta}\nQuery Usada: {query_resposta}\nResposta: {resposta_truncada}\n\n"

    return contexto

def get_manager():
    import extra_streamlit_components as stx
    return stx.CookieManager()

def add_uploaded_files(files, st):
    """Adiciona novos arquivos carregados à lista da sessão, evitando duplicados."""
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    existing_files = set(file.name for file in st.session_state.uploaded_files)

    new_files = [file for file in files if file.name not in existing_files]

    st.session_state.uploaded_files.extend(new_files)

def round_image_corners(image, radius):
    """Arredonda os cantos da imagem com um determinado raio e torna o fundo transparente."""
    # Certifique-se de que a imagem esteja em modo RGBA
    image = image.convert("RGBA")

    # Cria uma máscara com os cantos arredondados
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, image.size[0], image.size[1]), radius=radius, fill=255)

    # Aplica a máscara à imagem
    rounded_image = Image.new('RGBA', image.size)
    rounded_image.paste(image, mask=mask)

    return rounded_image

def list_users(st):
    api_fields = {
        'api_user': 'M4Y0U77WQTQM5AI',
        'api_token': 'AAKT5Z-P4U1C1-HZZYJC-IIYUEZ-W2ALM1-HWCQSS-KTSNI3-200SZZ',
        'api_module': 'Usuarios',
        'api_action': 'listarUsuarios'
    }

    try:
        response = requests.post(
            'https://intranet.sicoobcredicaf.com.br/api',
            data=api_fields,
            verify=False
        )
        response.raise_for_status()
        return response.json() if isinstance(response.json(), list) else []
    except requests.RequestException as e:
        st.error(f"Erro na solicitação: {str(e)}")
        return []

def autenticar(loginAD, senha):
    server = Server('ldap://172.19.53.201:389', get_info=ALL)
    user_with_domain = f'credicaf.local\\{loginAD}'
    conn = Connection(server, user=user_with_domain, password=senha, authentication=NTLM)

    if conn.bind():
        return loginAD
    return None


