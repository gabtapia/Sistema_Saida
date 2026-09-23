from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

import models
import schemas
from security import gerar_hash_senha


# ==============================================================================
# OPERAÇÕES DE UTILIZADORES
# ==============================================================================
def obter_usuario_por_email(db: Session, email: str) -> models.Usuario | None:
    query = select(models.Usuario).where(models.Usuario.email == email)
    return db.scalar(query)


def obter_usuario_por_id(db: Session, usuario_id: int) -> models.Usuario | None:
    query = select(models.Usuario).where(models.Usuario.id == usuario_id)
    return db.scalar(query)


def criar_usuario(db: Session, dados: schemas.UsuarioCreate) -> models.Usuario:
    novo_usuario = models.Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        papel=dados.papel,
        ativo=True,
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


def listar_usuarios(db: Session) -> list[models.Usuario]:
    query = select(models.Usuario).order_by(models.Usuario.nome.asc())
    return list(db.scalars(query).all())


# ==============================================================================
# OPERAÇÕES DE MOTIVOS DE SAÍDA
# ==============================================================================
def criar_motivo(db: Session, dados: schemas.MotivoSaidaCreate) -> models.MotivoSaida:
    novo_motivo = models.MotivoSaida(descricao=dados.descricao, ativo=True)
    db.add(novo_motivo)
    db.commit()
    db.refresh(novo_motivo)
    return novo_motivo


def listar_motivos(db: Session, apenas_ativos: bool = True) -> list[models.MotivoSaida]:
    query = select(models.MotivoSaida)
    if apenas_ativos:
        query = query.where(models.MotivoSaida.ativo.is_(True))
    query = query.order_by(models.MotivoSaida.descricao.asc())
    return list(db.scalars(query).all())


def obter_motivo_por_id(db: Session, motivo_id: int) -> models.MotivoSaida | None:
    query = select(models.MotivoSaida).where(models.MotivoSaida.id == motivo_id)
    return db.scalar(query)


# ==============================================================================
# OPERAÇÕES DE REGISTO DE SAÍDAS
# ==============================================================================
def criar_autorizacao(
    db: Session, dados: schemas.RegistroSaidaCreate, autorizador_id: int
) -> models.RegistroSaida:
    """Etapa 1: O servidor de assistência emite a autorização."""
    novo_registro = models.RegistroSaida(
        matricula=dados.matricula,
        nome_estudante=dados.nome_estudante,
        turma=dados.turma,
        motivo_id=dados.motivo_id,
        observacao=dados.observacao,
        autorizado_por_id=autorizador_id,
        status=models.StatusSaida.AUTORIZADO,
    )
    db.add(novo_registro)
    db.commit()
    db.refresh(novo_registro)
    return novo_registro


def obter_saida_por_id(db: Session, registro_id: int) -> models.RegistroSaida | None:
    query = (
        select(models.RegistroSaida)
        .options(
            joinedload(models.RegistroSaida.motivo),
            joinedload(models.RegistroSaida.autorizador),
            joinedload(models.RegistroSaida.porteiro),
        )
        .where(models.RegistroSaida.id == registro_id)
    )
    return db.scalar(query)


def listar_saidas_pendentes(db: Session) -> list[models.RegistroSaida]:
    """Lista as saídas que estão autorizadas mas ainda não foram confirmadas na portaria."""
    query = (
        select(models.RegistroSaida)
        .options(
            joinedload(models.RegistroSaida.motivo),
            joinedload(models.RegistroSaida.autorizador),
        )
        .where(models.RegistroSaida.status == models.StatusSaida.AUTORIZADO)
        .order_by(models.RegistroSaida.data_autorizacao.desc())
    )
    return list(db.scalars(query).all())


def confirmar_saida_portaria(
    db: Session, registro: models.RegistroSaida, porteiro_id: int
) -> models.RegistroSaida:
    """Etapa 2: O porteiro confirma que o aluno saiu fisicamente."""
    registro.status = models.StatusSaida.CONCLUIDO
    registro.porteiro_id = porteiro_id
    registro.data_saida_efetiva = datetime.now()

    db.commit()
    db.refresh(registro)
    return registro


def listar_historico(db: Session) -> list[models.RegistroSaida]:
    """Lista completa com carregamento de todos os relacionamentos para auditoria."""
    query = (
        select(models.RegistroSaida)
        .options(
            joinedload(models.RegistroSaida.motivo),
            joinedload(models.RegistroSaida.autorizador),
            joinedload(models.RegistroSaida.porteiro),
        )
        .order_by(models.RegistroSaida.data_autorizacao.desc())
    )
    return list(db.scalars(query).all())