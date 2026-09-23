from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

import crud
import schemas
from dependencies import ExigirPapel, SessionDep, UsuarioDep
from models import PapelUsuario, StatusSaida

router = APIRouter(prefix="/saidas", tags=["Controle de Saídas"])

# Validações de papel
exigir_assistencia = Depends(
    ExigirPapel([PapelUsuario.ASSISTENCIA, PapelUsuario.ADMIN])
)
exigir_portaria = Depends(
    ExigirPapel([PapelUsuario.PORTARIA, PapelUsuario.ADMIN])
)


@router.post(
    "/",
    response_model=schemas.RegistroSaidaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Emite uma autorização de saída (Assistência de Alunos)",
)
def autorizar_saida(
    dados: schemas.RegistroSaidaCreate,
    db: SessionDep,
    usuario_atual: Annotated[UsuarioDep, exigir_assistencia],
):
    # Valida se o motivo selecionado existe
    motivo = crud.obter_motivo_por_id(db, dados.motivo_id)
    if not motivo or not motivo.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O motivo de saída selecionado é inválido ou está inativo.",
        )

    novo_registro = crud.criar_autorizacao(
        db=db, dados=dados, autorizador_id=usuario_atual.id
    )
    # Recarrega com os joins para retornar no schema completo
    return crud.obter_saida_por_id(db, novo_registro.id)


@router.get(
    "/pendentes",
    response_model=list[schemas.RegistroSaidaResponse],
    summary="Lista autorizações pendentes aguardando confirmação na portaria",
)
def listar_saidas_pendentes(db: SessionDep, usuario_atual: UsuarioDep):
    return crud.listar_saidas_pendentes(db)


@router.patch(
    "/{registro_id}/confirmar",
    response_model=schemas.RegistroSaidaResponse,
    summary="Confirma a saída do estudante (Portaria)",
)
def confirmar_saida_portaria(
    registro_id: int,
    db: SessionDep,
    usuario_atual: Annotated[UsuarioDep, exigir_portaria],
):
    registro = crud.obter_saida_por_id(db, registro_id)
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registo de autorização não encontrado.",
        )
    if registro.status != StatusSaida.AUTORIZADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não é possível confirmar. O estado atual deste registo é '{registro.status}'.",
        )

    crud.confirmar_saida_portaria(
        db=db, registro=registro, porteiro_id=usuario_atual.id
    )
    return crud.obter_saida_por_id(db, registro_id)


@router.get(
    "/historico",
    response_model=list[schemas.RegistroSaidaResponse],
    summary="Histórico geral de todas as autorizações e saídas confirmadas",
)
def historico_geral(db: SessionDep, usuario_atual: UsuarioDep):
    return crud.listar_historico(db)