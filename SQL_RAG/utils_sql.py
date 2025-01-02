from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_community.vectorstores import FAISS
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.prompts import (
    ChatPromptTemplate, FewShotPromptTemplate, MessagesPlaceholder, PromptTemplate, SystemMessagePromptTemplate,
)
from dotenv import load_dotenv
import json
from getpass import getuser

# noinspection PyUnresolvedReferences
from UTILS.utils import atualizar_historico, gerar_contexto

username = getuser()
load_dotenv()

class SQLHandler(BaseCallbackHandler):
    def __init__(self):
        self.sql_result = None

    def on_agent_action(self, action, **kwargs):
        """Run on agent action. if the tool being used is sql_db_query,
         it means we're submitting the sql and we can
         record it as the final sql"""
        print(f"Action received: {action}")
        if action.tool == "sql_db_query":
            self.sql_result = action.tool_input
            print(f"SQL Result updated: {self.sql_result}")


def converse_com_sql(question, llm_answer, db, embeddings, st, prefix):

    contexto = gerar_contexto(st, '')

    # No caso das consultas em SQL, é necessário passar o prefix direto na pergunta
    question = prefix + ', ' + question

    # Define o CallbackHandler personalizado
    sql_log_handler = SQLHandler()

    # Abrir e ler o arquivo de instruções
    with open('SQL_RAG/instrucoes_sql_prefix.txt', 'r', encoding='utf-8') as file:
        instrucoes = file.read()

    # Abrir e ler o arquivo de exemplos
    with open('SQL_RAG/examples.txt', 'r', encoding='utf-8') as f:
        examples = json.load(f)

    # Criar o prefixo do sistema
    system_prefix = f"""Context provided by the user with last few questions, queries, answers and instructions: [{contexto}]

        You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct {{dialect}} query to run, then look at the results of the
        query and return the answer.
        Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most
        {{top_k}} results.
        You can order the results by a relevant column to return the most interesting examples in the database.
        Never query for all the columns from a specific table, only ask for the relevant columns given the question.
        You have access to the following tables: {{table_info}}.

        {instrucoes}

        Here are some examples of user inputs and their corresponding SQL queries:
    """

    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        embeddings,
        FAISS,
        k=20,
        input_keys=["input"],
    )

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=PromptTemplate.from_template(
            "User input: {input}\nSQL query: {query}"
        ),
        prefix=system_prefix,
        suffix="",
    )

    full_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate(prompt=few_shot_prompt),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    toolkit = SQLDatabaseToolkit(db=db, llm=llm_answer)

    agent_executor = create_sql_agent(
        max_iterations=20,
        llm=llm_answer,
        agent_type="openai-tools",
        verbose=True,
        prompt=full_prompt,
        toolkit=toolkit,
        format_instructions=prefix,
        top_k=100,
        dialect='MySQL',
        agent_executor_kwargs={
            "callbacks": [sql_log_handler],  # Adiciona o handler aqui
        }
    )

    query_usada = None
    # Executar a pergunta
    response = agent_executor.invoke({'input': question})
    resposta_obtida = response['output']
    print(f"Response from agent: {resposta_obtida}")

    print(f"SQL Log Handler Result: {sql_log_handler.sql_result}")
    if sql_log_handler.sql_result:
        if 'query' in sql_log_handler.sql_result:
            query_usada = str(sql_log_handler.sql_result['query'])
            print(f"SQL Query Used: {query_usada}")
        else:
            print("No 'query' key found in SQL result.")
    else:
        print("No SQL query was recorded.")

    atualizar_historico(question, query_usada, resposta_obtida, st)
    return resposta_obtida
