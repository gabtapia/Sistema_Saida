import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import PapelUsuario, Usuario

load_dotenv()

# ----------------------------------------------------------------------
# BANCO DE DADOS
# ----------------------------------------------------------------------

SessionDep = Annotated[Session, Depends(get_db)]

# ----------------------------------------------------------------------
# AUTENTICAÇÃO E DEPENDÊNCIAS DE USUÁRIO
# ----------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "chave_fallback_caso_nao_definida")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Indica para o FastAPI qual endpoint gera o token (útil para o botão 'Authorize' no Swagger)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def obter_usuario_atual(
    db: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]
) -> Usuario:
    """Extrai e valida o token JWT, retornando a instância do usuário autenticado."""
    excecao_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise excecao_credenciais
    except JWTError:
        raise excecao_credenciais

    query = select(Usuario).where(Usuario.email == email)
    usuario = db.scalar(query)

    if usuario is None or not usuario.ativo:
        raise excecao_credenciais

    return usuario


UsuarioDep = Annotated[Usuario, Depends(obter_usuario_atual)]


# ----------------------------------------------------------------------
# CONTROLE DE ACESSO BASEADO EM PAPEL (RBAC)
# ----------------------------------------------------------------------
class ExigirPapel:
    """Valida se o usuário autenticado possui o papel necessário para acessar o endpoint."""

    def __init__(self, papeis_permitidos: list[PapelUsuario]):
        self.papeis_permitidos = papeis_permitidos

    def __call__(self, usuario: UsuarioDep) -> Usuario:
        if usuario.papel not in self.papeis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: seu perfil não possui autorização para esta ação.",
            )
        return usuario