import enum
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ----------------------------------------------------------------------
# ENUMS
# ----------------------------------------------------------------------
class PapelUsuario(str, enum.Enum):
    ASSISTENCIA = "ASSISTENCIA"
    PORTARIA = "PORTARIA"
    ADMIN = "ADMIN"


class StatusSaida(str, enum.Enum):
    AUTORIZADO = "AUTORIZADO"
    CONCLUIDO = "CONCLUIDO"
    CANCELADO = "CANCELADO"


# ----------------------------------------------------------------------
# MODELOS
# ----------------------------------------------------------------------
class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(150), unique=True, index=True, nullable=False
    )
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    papel: Mapped[PapelUsuario] = mapped_column(
        String(20), default=PapelUsuario.ASSISTENCIA, nullable=False
    )
    ativo: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relacionamentos com as operações de saída
    autorizacoes_emitidas: Mapped[list["RegistroSaida"]] = relationship(
        "RegistroSaida",
        back_populates="autorizador",
        foreign_keys="RegistroSaida.autorizado_por_id",
    )
    saidas_liberadas: Mapped[list["RegistroSaida"]] = relationship(
        "RegistroSaida",
        back_populates="porteiro",
        foreign_keys="RegistroSaida.porteiro_id",
    )


class MotivoSaida(Base):
    __tablename__ = "motivos_saida"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    descricao: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    ativo: Mapped[bool] = mapped_column(default=True, nullable=False)

    registros: Mapped[list["RegistroSaida"]] = relationship(
        "RegistroSaida", back_populates="motivo"
    )


class RegistroSaida(Base):
    __tablename__ = "registros_saida"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Dados do Estudante
    matricula: Mapped[str] = mapped_column(
        String(30), index=True, nullable=False
    )
    nome_estudante: Mapped[str] = mapped_column(String(120), nullable=False)
    turma: Mapped[str] = mapped_column(String(50), nullable=False)

    # Vínculo com a tabela de motivos + campo livre para detalhamento
    motivo_id: Mapped[int] = mapped_column(
        ForeignKey("motivos_saida.id"), nullable=False
    )
    observacao: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Detalhes adicionais, se houver

    # Etapa 1: Emissão da Autorização
    autorizado_por_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False
    )
    data_autorizacao: Mapped[datetime] = mapped_column(
        DateTime, insert_default=func.now(), nullable=False
    )

    # Etapa 2: Confirmação na Portaria
    porteiro_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    data_saida_efetiva: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Status de ciclo de vida
    status: Mapped[StatusSaida] = mapped_column(
        String(20), default=StatusSaida.AUTORIZADO, nullable=False
    )

    # Relacionamentos ORM bidirecionais
    motivo: Mapped["MotivoSaida"] = relationship(
        "MotivoSaida", back_populates="registros"
    )
    autorizador: Mapped["Usuario"] = relationship(
        "Usuario",
        foreign_keys=[autorizado_por_id],
        back_populates="autorizacoes_emitidas",
    )
    porteiro: Mapped["Usuario | None"] = relationship(
        "Usuario",
        foreign_keys=[porteiro_id],
        back_populates="saidas_liberadas",
    )