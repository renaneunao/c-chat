from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain_community.document_loaders import UnstructuredURLLoader
# noinspection PyUnresolvedReferences
from UTILS.utils import gerar_contexto, atualizar_historico


def get_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=1000)
    return text_splitter.split_text(text)


def get_conversational_chain(llm):
    prompt_template = """
    Como um especialista em responder perguntas sobre documentações recebidas de URL, 
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
    if "vector_store_url" in st.session_state:
        vector_store_url = st.session_state.vector_store_url
    else:
        vector_store_url = FAISS.from_texts(text_chunks, embedding=embeddings)
        st.session_state.vector_store_url = vector_store_url
    return vector_store_url



def clear_cache_in_session(st):
    st.session_state.pop("text_cache_url", None)
    st.session_state.pop("vector_store_url", None)


def update_cache_in_session(text_chunks, st):
    st.session_state.text_cache_url = {chunk: True for chunk in text_chunks}


def load_cache_from_session(st):
    return st.session_state.get("text_cache_url", {})


def url_question(user_question, llm, st, urls, prefix, context_doc_on, embeddings):
    current_urls = set(urls)  # Convert URLs to a set for comparison

    if "previous_urls" in st.session_state:
        previous_urls = set(st.session_state.previous_urls)
        if current_urls != previous_urls:
            # Clear cache if URLs have changed
            clear_cache_in_session(st)
    else:
        st.session_state.previous_urls = urls  # Initialize previous_urls if not present

    # Store current URLs in session state
    st.session_state.previous_urls = urls

    all_transcripts = []
    print(f'URLs carregadas: {urls}')

    loader = UnstructuredURLLoader(urls=urls)
    data = loader.load()

    for content in data:
        text_chunks = get_chunks(content.page_content)
        all_transcripts.extend(text_chunks)

    # Update session cache with new content
    update_cache_in_session(all_transcripts, st)

    vector_store_url = load_or_create_vector_store(all_transcripts, embeddings, st)

    context = gerar_contexto(st, prefix + context_doc_on)

    try:
        docs = vector_store_url.similarity_search(user_question)
        chain = get_conversational_chain(llm)
        response = chain({"input_documents": docs, "question": user_question + context, "context": context},
                         return_only_outputs=False)
        resposta = response["output_text"]

        atualizar_historico(user_question, None, resposta, st)

        if resposta:
            return resposta
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar sua pergunta: {e}")
