from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models import PapelUsuario, StatusSaida


# ----------------------------------------------------------------------
# SCHEMAS DE AUTENTICAÇÃO E USUÁRIOS
# ----------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: str | None = None
    papel: PapelUsuario | None = None


class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: str
    papel: PapelUsuario = PapelUsuario.ASSISTENCIA


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, description="Senha em texto puro para ser hasheada")


class UsuarioResponse(UsuarioBase):
    id: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# SCHEMAS DE MOTIVOS DE SAÍDA
# ----------------------------------------------------------------------
class MotivoSaidaBase(BaseModel):
    descricao: str = Field(..., min_length=3, max_length=100)


class MotivoSaidaCreate(MotivoSaidaBase):
    pass


class MotivoSaidaResponse(MotivoSaidaBase):
    id: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------------------------
# SCHEMAS DE CONTROLE DE SAÍDA
# ----------------------------------------------------------------------
class RegistroSaidaBase(BaseModel):
    matricula: str = Field(..., min_length=3, max_length=30)
    nome_estudante: str = Field(..., min_length=2, max_length=120)
    turma: str = Field(..., min_length=2, max_length=50)
    motivo_id: int
    observacao: str | None = Field(default=None, description="Observações complementares")


class RegistroSaidaCreate(RegistroSaidaBase):
    """Schema para o Assistente de Alunos emitir a autorização."""
    pass


class RegistroSaidaResponse(RegistroSaidaBase):
    """Schema completo para leitura e histórico, trazendo detalhes do autorizador e porteiro."""
    id: int
    status: StatusSaida
    data_autorizacao: datetime
    autorizador: UsuarioResponse

    # Dados da confirmação da portaria (nulos enquanto pendente)
    data_saida_efetiva: datetime | None = None
    porteiro: UsuarioResponse | None = None
    motivo: MotivoSaidaResponse

    model_config = ConfigDict(from_attributes=True)