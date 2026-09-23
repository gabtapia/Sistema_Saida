# Sistema de Controle de Saídas Antecipadas (IFPR)

## Visão Geral do Projeto

Este projeto consiste numa aplicação web full-stack desenvolvida para informatizar, auditar e assegurar o processo de autorização e liberação física de saídas antecipadas de estudantes no IFPR. 

A solução elimina o uso de autorizações manuais em papel através de um fluxo assíncrono dividido em duas etapas operacionais protegidas por níveis de acesso (RBAC):
1. **Emissão de Autorização:** Concedida pelo setor pedagógico/assistência estudantil mediante justificativa formal.
2. **Confirmação e Saída Efetiva:** Efetuada no portão pela portaria após conferência de dados, registando carimbo de data/hora pontual e o responsável pela liberação física.

A arquitetura adota uma separação rigorosa entre a API RESTful e a interface do utilizador, assegurando persistência íntegra, segurança baseada em tokens criptográficos e histórico completo de auditoria.

---

## Links de Acesso à Aplicação

* **Interface Web (Frontend - Streamlit):** `http://localhost:8501`
* **API REST (Backend - FastAPI):** `http://127.0.0.1:8000`
* **Documentação Interativa (Swagger UI):** `http://127.0.0.1:8000/docs`
* **Documentação Alternativa (ReDoc):** `http://127.0.0.1:8000/redoc`

---

## Tecnologias Utilizadas

### Backend
* **Python 3.10+:** Linguagem principal do projeto.
* **FastAPI:** Framework web moderno e assíncrono para desenvolvimento da API RESTful de alta performance.
* **SQLAlchemy 2.0+:** ORM moderno em padrão declarativo tipado (`Mapped`, `mapped_column`) para abstração de persistência e modelagem relacional.
* **SQLite:** Motor de base de dados relacional local para retenção e integridade de registos.
* **Pydantic V2:** Validação rigorosa de esquemas de dados de entrada/saída, validação estrutural de e-mails (`email-validator`) e serialização automática.
* **Uvicorn:** Servidor ASGI para execução do serviço FastAPI com suporte a recarga automática (*hot-reload*).
* **Segurança e Criptografia:**
  * **Python-Jose:** Geração, assinatura e decodificação de tokens JWT (*JSON Web Tokens*).
  * **Pwdlib & Bcrypt:** Funções unidirecionais de *hashing* criptográfico seguro para armazenamento de senhas.
* **Python-Dotenv:** Isolamento de segredos e parametrizações operacionais em variáveis de ambiente (`.env`).

### Frontend
* **Streamlit:** Framework dinâmico para construção de interfaces e painéis em Python.
* **Requests:** Comunicação cliente HTTP com o backend RESTful.
* **Pandas:** Estruturação, formatação e ordenação decrescente/crescente dos dados tabulares para auditoria.

---

## Arquitetura e Estrutura do Projeto

O repositório está organizado de forma modular, prevenindo ciclos de importação e isolando responsabilidades:

```text
Sistema_Saida/
├── .env.example              # Modelo documentado das variáveis de ambiente
├── .gitignore                # Regras de exclusão de artefatos temporários e segredos
├── README.md                 # Documentação técnica integral do sistema
├── backend/
│   ├── .env                  # Variáveis de ambiente locais (não versionadas)
│   ├── crud.py               # Lógica de persistência e consultas ao banco (SQLAlchemy)
│   ├── database.py           # Conexão do motor (engine), sessões e base declarativa
│   ├── dependencies.py       # Injeção de dependências (Sessão de BD, Autenticação, RBAC)
│   ├── main.py               # Ponto de entrada FastAPI, ciclo de vida (lifespan) e CORS
│   ├── models.py             # Entidades ORM relacionais e enumerações
│   ├── requirements.txt      # Dependências isoladas da API
│   ├── schemas.py            # Contratos e esquemas de validação Pydantic
│   ├── security.py           # Algoritmos de hash de senha e emissão de tokens JWT
│   └── routes/               # Endpoints segmentados por domínio
│       ├── __init__.py       # Exportação centralizada dos routers
│       ├── auth.py           # Endpoints de autenticação, perfil e emissão de JWT
│       ├── motivos.py        # Endpoints de consulta e cadastro de motivos pré-definidos
│       └── saidas.py         # Endpoints de autorização, confirmação física e histórico
└── app.py                    # Interface Streamlit completa (Login, Abas operacionais e Auditoria)
