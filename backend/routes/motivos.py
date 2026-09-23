from fastapi import APIRouter, Depends, HTTPException, status

import crud
import schemas
from dependencies import ExigirPapel, SessionDep
from models import PapelUsuario

router = APIRouter(prefix="/motivos", tags=["Motivos de Saída"])

# Apenas ASSISTENCIA e ADMIN podem cadastrar novos motivos
permite_gestao = Depends(
    ExigirPapel([PapelUsuario.ASSISTENCIA, PapelUsuario.ADMIN])
)


@router.get(
    "/",
    response_model=list[schemas.MotivoSaidaResponse],
    summary="Lista todos os motivos de saída ativos",
)
def listar_motivos(db: SessionDep):
    return crud.listar_motivos(db, apenas_ativos=True)


@router.post(
    "/",
    response_model=schemas.MotivoSaidaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[permite_gestao],
    summary="Cria um novo motivo de saída padronizado",
)
def criar_motivo(dados: schemas.MotivoSaidaCreate, db: SessionDep):
    return crud.criar_motivo(db, dados)