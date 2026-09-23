import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import crud
import models
import schemas
from database import Base, SessionLocal, engine
from routes import auth_router, motivos_router, saidas_router

load_dotenv()

# Origens permitidas vindas do .env (separadas por vírgula)
ALLOWED_ORIGINS = [
    origem.strip()
    for origem in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501"
    ).split(",")
    if origem.strip()
]


def popular_dados_iniciais():
    """Cria dados essenciais de arranque se a base de dados estiver vazia."""
    with SessionLocal() as db:
        # 1. Utilizador Administrador Padrão (carregado via .env)
        admin_email = os.getenv("FIRST_SUPERUSER_EMAIL", "admin@ifpr.edu.br")
        admin_nome = os.getenv("FIRST_SUPERUSER_NAME", "Administrador Geral")
        admin_senha = os.getenv("FIRST_SUPERUSER_PASSWORD", "admin123")

        admin_existente = crud.obter_usuario_por_email(db, admin_email)
        if not admin_existente:
            crud.criar_usuario(
                db,
                schemas.UsuarioCreate(
                    nome=admin_nome,
                    email=admin_email,
                    senha=admin_senha,
                    papel=models.PapelUsuario.ADMIN,
                ),
            )

        # 2. Utilizadores Operacionais Padrão (Assistência e Portaria)
        if not crud.obter_usuario_por_email(db, "assistencia@ifpr.edu.br"):
            crud.criar_usuario(
                db,
                schemas.UsuarioCreate(
                    nome="Assistente de Alunos",
                    email="assistencia@ifpr.edu.br",
                    senha="senha123",
                    papel=models.PapelUsuario.ASSISTENCIA,
                ),
            )

        if not crud.obter_usuario_por_email(db, "portaria@ifpr.edu.br"):
            crud.criar_usuario(
                db,
                schemas.UsuarioCreate(
                    nome="Porteiro Plantonista",
                    email="portaria@ifpr.edu.br",
                    senha="senha123",
                    papel=models.PapelUsuario.PORTARIA,
                ),
            )

        # 3. Motivos Padronizados Iniciais
        motivos_existentes = crud.listar_motivos(db, apenas_ativos=False)
        if not motivos_existentes:
            motivos_padrao = [
                "Consulta Médica / Tratamento",
                "Transporte Intermunicipal",
                "Assuntos Familiares Particulares",
                "Atestado / Problemas de Saúde",
                "Estágio / Atividade Externa",
            ]
            for descricao in motivos_padrao:
                crud.criar_motivo(db, schemas.MotivoSaidaCreate(descricao=descricao))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    popular_dados_iniciais()
    yield


app = FastAPI(
    title=os.getenv("APP_NAME", "Sistema de Controlo de Saídas - IFPR"),
    description="API RESTful modular para autorização e liberação de estudantes.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configurado pelas origens do .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(motivos_router)
app.include_router(saidas_router)


@app.get("/", tags=["Health"])
def healthcheck():
    return {
        "status": "online",
        "sistema": os.getenv("APP_NAME", "Controlo de Saída Antecipada IFPR"),
        "versao": "1.0.0",
    }