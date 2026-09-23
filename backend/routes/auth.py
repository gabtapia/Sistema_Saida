from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import crud
import schemas
from dependencies import ExigirPapel, SessionDep, UsuarioDep
from models import PapelUsuario
from security import criar_access_token, verificar_senha

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Dependência que restringe o acesso exclusivamente a administradores
exigir_admin = Depends(ExigirPapel([PapelUsuario.ADMIN]))


@router.post("/login", response_model=schemas.Token)
def login(
    dados_login: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep,
):
    usuario = crud.obter_usuario_por_email(db, dados_login.username)
    if not usuario or not verificar_senha(dados_login.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou palavra-passe incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilizador inativo no sistema.",
        )

    papel_str = (
        usuario.papel.value
        if hasattr(usuario.papel, "value")
        else str(usuario.papel)
    )
    dados_token = {"sub": usuario.email, "papel": papel_str}
    token_acesso = criar_access_token(dados=dados_token)
    return {"access_token": token_acesso, "token_type": "bearer"}


@router.post(
    "/usuarios",
    response_model=schemas.UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[exigir_admin],  # <--- BLOQUEIA O ACESSO A QUEM NÃO FOR ADMIN
    summary="Regista um novo utilizador (Apenas Administrador)",
)
def criar_usuario(
    dados: schemas.UsuarioCreate,
    db: SessionDep,
    usuario_atual: Annotated[UsuarioDep, exigir_admin],
):
    usuario_existente = crud.obter_usuario_por_email(db, dados.email)
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um utilizador registado com este e-mail.",
        )
    return crud.criar_usuario(db, dados)


@router.get(
    "/me",
    response_model=schemas.UsuarioResponse,
    summary="Retorna os dados do utilizador atualmente autenticado",
)
def obter_dados_me(usuario_atual: UsuarioDep):
    return usuario_atual