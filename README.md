
# Tira-dúvidas Credicaf

O projeto Tira-dúvidas CREDICAF é uma aplicação web interativa desenvolvida com Streamlit, que visa fornecer um assistente virtual para responder perguntas e esclarecer dúvidas relacionadas aos produtos e serviços do Sicoob Credicaf. Utilizando tecnologias de processamento de linguagem natural (NLP) e integração com diferentes fontes de dados, a aplicação permite consultas a documentos, bancos de dados SQL, arquivos CSV, vídeos do YouTube e páginas da web.


## Screenshots

![App Screenshot](https://iili.io/din4T8l.png)


## Instalação

Instalação Tira-dúvidas Credicaf. É necessário autenticação. Somente usuários autorizados conseguem instalar.

```bash
pip install git+https://github.com/credicaf/credicaf-chat.git
```

Navegue até o diretório do projeto

```bash
cd tira-duvidas-credicaf
```

Depois execute a instalação das requisições

```bash
pip install -r requirements.txt
```

Execute a aplicação

```bash
streamlit run streamlit_app.py
```

## Funcionalidades principais:

Autenticação de Usuário: Acesso seguro à aplicação através de um sistema de login simples.
Consulta Simples: Permite que os usuários façam perguntas diretas e recebam respostas instantâneas.
Consulta à Base de Conhecimento: Os usuários podem consultar documentos disponíveis, como PDFs e textos, para obter informações detalhadas.
Consulta SQL: Integração com bancos de dados SQL, permitindo que os usuários façam perguntas e recebam respostas baseadas em dados estruturados.
Consulta CSV: Carregamento e análise de arquivos CSV, possibilitando consultas sobre dados tabulares.
Consulta/Resumo de Vídeos do YouTube: Capacidade de extrair informações e resumos de vídeos do YouTube.
Consulta à Documentação Online: Acesso a informações de documentação disponível na web.
Geração de Áudio-Resposta: Opção para gerar respostas em formato de áudio, com diferentes opções de voz e modelos de síntese.
## Stack utilizada

Streamlit: Framework para criação de aplicações web interativas em Python.

Python: Linguagem de programação utilizada para o desenvolvimento da lógica da aplicação.
