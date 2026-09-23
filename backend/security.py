from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from dotenv import load_dotenv
import os

load_dotenv()

# ----------------------------------------------------------------------
# CONFIGURAÇÕES DE CRIPTOGRAFIA E JWT
# ----------------------------------------------------------------------
# NOTA: Em ambiente de produção, carrega a SECRET_KEY de variáveis de ambiente (.env)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Gestor de hash com bcrypt
password_hash = PasswordHash((BcryptHasher(),))


# ----------------------------------------------------------------------
# GESTÃO DE PALAVRAS-PASSE
# ----------------------------------------------------------------------
def gerar_hash_senha(senha: str) -> str:
    """Gera o hash seguro da palavra-passe em texto puro."""
    return password_hash.hash(senha)


def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    """Valida se a palavra-passe inserida coincide com o hash guardado."""
    return password_hash.verify(senha_pura, senha_hash)


# ----------------------------------------------------------------------
# GESTÃO DE TOKENS JWT
# ----------------------------------------------------------------------
def criar_access_token(dados: dict, tempo_expiracao: timedelta | None = None) -> str:
    """Cria um token JWT assinado contendo os dados (claims) especificados."""
    dados_para_codificar = dados.copy()

    agora = datetime.now(timezone.utc)
    if tempo_expiracao:
        expira_em = agora + tempo_expiracao
    else:
        expira_em = agora + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    dados_para_codificar.update({"exp": expira_em, "iat": agora})
    token_jwt = jwt.encode(dados_para_codificar, SECRET_KEY, algorithm=ALGORITHM)
    return token_jwt


def descodificar_access_token(token: str) -> dict | None:
    """Descodifica o token JWT e valida a assinatura e expiração."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None