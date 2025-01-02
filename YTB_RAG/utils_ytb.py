from langchain_community.document_loaders import YoutubeLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
# noinspection PyUnresolvedReferences
from UTILS.utils import gerar_contexto, atualizar_historico

def get_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=1000)
    return text_splitter.split_text(text)


def get_conversational_chain(llm):
    prompt_template = """
    Como um especialista em responder perguntas sobre transcrições do youtube, 
    seu papel é fornecer respostas claras, concisas e precisas. 
    Mantenha sempre um tom profissional e informativo. Sempre traga referências.

    Contexto:\n {context}\n
    Pergunta: \n{question}\n

    Resposta:
    """
    model = llm
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)


def load_or_create_vector_store(text_chunks, embeddings, st):
    if "vector_store_youtube" in st.session_state:
        vector_store_youtube = st.session_state.vector_store_youtube
    else:
        vector_store_youtube = FAISS.from_texts(text_chunks, embedding=embeddings)
        st.session_state.vector_store_youtube = vector_store_youtube
    return vector_store_youtube


# Função para limpar o cache na sessão
def clear_cache_in_session(st):
    st.session_state.pop("text_cache_youtube", None)
    st.session_state.pop("vector_store_youtube", None)


# Função para atualizar o cache na sessão
def update_cache_in_session(text_chunks, st):
    if "text_cache_youtube" not in st.session_state:
        st.session_state.text_cache_youtube = {}

    for chunk in text_chunks:
        st.session_state.text_cache_youtube[chunk] = True


# Função para carregar o cache da sessão
def load_cache_from_session(st):
    return st.session_state.get("text_cache_youtube", {})


# Função principal para responder perguntas baseadas na transcrição do YouTube
def youtube_video_question(user_question, llm, st, videos, prefix, embeddings):
    # Limpar cache antes de processar novos vídeos
    clear_cache_in_session(st)

    all_transcripts = []
    print(f'videos carregados: {videos}')

    # Carregar as transcrições para cada vídeo na lista, apenas para URLs não vazios
    for video_url in videos:
        if video_url:
            loader = YoutubeLoader.from_youtube_url(video_url, language=["pt", "pt-BR"])
            transcript_youtube = loader.load()

            text_chunks = get_chunks(transcript_youtube[0].page_content)
            all_transcripts.extend(text_chunks)

    # Update session cache
    update_cache_in_session(all_transcripts, st)

    vector_store_youtube = load_or_create_vector_store(all_transcripts, embeddings, st)

    context = gerar_contexto(st, prefix)

    try:
        docs = vector_store_youtube.similarity_search(user_question)
        chain = get_conversational_chain(llm)
        response = chain({"input_documents": docs, "question": user_question, "context": context},
                         return_only_outputs=False)
        resposta = response["output_text"]

        atualizar_historico(user_question, None, resposta, st)

        if resposta:
            return resposta
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar sua pergunta: {e}")
