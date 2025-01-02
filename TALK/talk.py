from dotenv import load_dotenv
from getpass import getuser
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.schema import HumanMessage, AIMessage

username = getuser()
load_dotenv()

# Armazenamento de histórico de sessões
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Função para lidar com a interação usando o histórico de mensagens
def converse(question, llm_answer, prefix, session_id='abc2'):
    # Recuperar histórico da sessão
    message_history = get_session_history(session_id)

    # Construir o contexto a partir do histórico de mensagens
    previous_messages = "\n".join(
        [f"Human: {msg.content}" if isinstance(msg, HumanMessage) else f"Assistant: {msg.content}"
         for msg in message_history.messages]
    )

    # Definir o prompt, incluindo contexto de interações anteriores
    prompt = f"{prefix}, Here is the context from previous interactions: {previous_messages}\nHuman: {question}\n"

    try:
        # Executar com histórico
        with_message_history = RunnableWithMessageHistory(llm_answer, get_session_history)
        config = {"configurable": {"session_id": session_id}}

        # Enviar mensagem para o modelo
        response = with_message_history.invoke([HumanMessage(content=question)], config=config)

        # Adicionar nova interação ao histórico
        message_history.add_message(HumanMessage(content=question))
        message_history.add_message(AIMessage(content=response.content))

        # Extrair resposta e exibir
        resposta_obtida = response.content.strip()
        print(f"Response content: {resposta_obtida}")
        return resposta_obtida

    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred while processing the request."