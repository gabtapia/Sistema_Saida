import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Controle de Saídas - IFPR",
    page_icon="🏫",
    layout="centered",
)

# ----------------------------------------------------------------------
# ESTADO DA SESSÃO
# ----------------------------------------------------------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "usuario" not in st.session_state:
    st.session_state.usuario = None


def obter_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def realizar_login(email: str, senha: str) -> bool:
    try:
        resposta = requests.post(
            f"{API_URL}/auth/login",
            data={"username": email, "password": senha},
        )
        if resposta.status_code == 200:
            dados = resposta.json()
            st.session_state.token = dados["access_token"]

            # Procura os dados do utilizador autenticado
            resp_me = requests.get(
                f"{API_URL}/auth/me", headers=obter_headers()
            )
            if resp_me.status_code == 200:
                st.session_state.usuario = resp_me.json()
                return True
        st.error("Credenciais inválidas ou utilizador inativo.")
        return False
    except requests.exceptions.ConnectionError:
        st.error("Erro ao conectar à API. O servidor FastAPI está ligado?")
        return False


def realizar_logout():
    st.session_state.token = None
    st.session_state.usuario = None
    st.rerun()


# ----------------------------------------------------------------------
# TELA DE LOGIN (LARGURA BALANCEADA)
# ----------------------------------------------------------------------
if not st.session_state.token:
    _, col_centro, _ = st.columns([1, 2.2, 1])

    with col_centro:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## Sistema de Controle de Saídas")
        st.caption("Instituto Federal do Paraná — Módulo de Saídas Antecipadas")

        with st.container(border=True):
            st.subheader("Autenticação")
            with st.form("form_login"):
                email = st.text_input(
                    "E-mail institucional",
                    placeholder="exemplo@ifpr.edu.br",
                )
                senha = st.text_input(
                    "Palavra-passe",
                    type="password",
                    placeholder="••••••••",
                )

                submetido = st.form_submit_button(
                    "Entrar", width='stretch'
                )

                if submetido:
                    if email and senha:
                        if realizar_login(email, senha):
                            st.rerun()
                    else:
                        st.warning("Preencha todos os campos.")
    st.stop()

# ----------------------------------------------------------------------
# BARRA LATERAL (INFORMAÇÕES DO UTILIZADOR)
# ----------------------------------------------------------------------
usuario = st.session_state.usuario
st.sidebar.markdown(f"**Utilizador:** {usuario['nome']}")
st.sidebar.markdown(f"**E-mail:** {usuario['email']}")
st.sidebar.markdown(f"**Perfil:** `{usuario['papel']}`")
if st.sidebar.button("Terminar Sessão", width='stretch'):
    realizar_logout()

st.title("Controle de Saídas IFPR")

# ----------------------------------------------------------------------
# NAVEGAÇÃO CONDICIONAL POR PERFIL
# ----------------------------------------------------------------------
papel = usuario["papel"]

abas_disponiveis = []
if papel in ["ASSISTENCIA", "ADMIN"]:
    abas_disponiveis.append("Nova Autorização")
if papel in ["PORTARIA", "ADMIN"]:
    abas_disponiveis.append("Portaria (Liberações)")
abas_disponiveis.append("Histórico e Auditoria")
if papel == "ADMIN":
    abas_disponiveis.append("Gestão de Motivos")

abas = st.tabs(abas_disponiveis)

# ----------------------------------------------------------------------
# ABA 1: NOVA AUTORIZAÇÃO (ASSISTÊNCIA / ADMIN)
# ----------------------------------------------------------------------
if "Nova Autorização" in abas_disponiveis:
    idx = abas_disponiveis.index("Nova Autorização")
    with abas[idx]:
        st.header("Emitir Autorização de Saída")

        resp_motivos = requests.get(
            f"{API_URL}/motivos/", headers=obter_headers()
        )
        motivos = (
            resp_motivos.json() if resp_motivos.status_code == 200 else []
        )
        mapa_motivos = {m["descricao"]: m["id"] for m in motivos}

        if not mapa_motivos:
            st.warning("Não há motivos de saída cadastrados no sistema.")
        else:
            with st.form("form_autorizacao", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    matricula = st.text_input("Matrícula do Estudante")
                    nome_aluno = st.text_input("Nome do Estudante")
                with col2:
                    turma = st.text_input("Turma / Curso")
                    motivo_sel = st.selectbox(
                        "Motivo da Saída", options=list(mapa_motivos.keys())
                    )

                observacao = st.text_area(
                    "Observações / Justificação", height=100
                )
                enviar = st.form_submit_button("Autorizar Saída")

                if enviar:
                    if not (matricula and nome_aluno and turma):
                        st.warning("Preencha todos os campos obrigatórios.")
                    else:
                        payload = {
                            "matricula": matricula,
                            "nome_estudante": nome_aluno,
                            "turma": turma,
                            "motivo_id": mapa_motivos[motivo_sel],
                            "observacao": observacao,
                        }
                        resp_envio = requests.post(
                            f"{API_URL}/saidas/",
                            json=payload,
                            headers=obter_headers(),
                        )
                        if resp_envio.status_code == 201:
                            st.success(
                                f"Saída para {nome_aluno} autorizada com sucesso!"
                            )
                        else:
                            st.error(
                                f"Erro: {resp_envio.json().get('detail', 'Falha ao autorizar.')}"
                            )

# ----------------------------------------------------------------------
# ABA 2: PORTARIA (PORTARIA / ADMIN)
# ----------------------------------------------------------------------
if "Portaria (Liberações)" in abas_disponiveis:
    idx = abas_disponiveis.index("Portaria (Liberações)")
    with abas[idx]:
        st.header("Estudantes Aguardando Confirmação no Portão")
        if st.button("Atualizar Lista"):
            st.rerun()

        resp_pendentes = requests.get(
            f"{API_URL}/saidas/pendentes", headers=obter_headers()
        )

        if resp_pendentes.status_code == 200:
            pendentes = resp_pendentes.json()
            if not pendentes:
                st.info("Nenhuma liberação pendente no momento.")
            else:
                for item in pendentes:
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 2, 2])
                        with c1:
                            st.markdown(
                                f"**{item['nome_estudante']}** (Matrícula: `{item['matricula']}`)"
                            )
                            st.caption(
                                f"Turma: {item['turma']} | Motivo: {item['motivo']['descricao']}"
                            )
                            if item.get("observacao"):
                                st.caption(f"Obs: {item['observacao']}")
                        with c2:
                            st.caption(
                                f"Autorizado em: {item['data_autorizacao'][:16].replace('T', ' ')}"
                            )
                            st.caption(
                                f"Por: {item['autorizador']['nome'] if item.get('autorizador') else 'N/D'}"
                            )
                        with c3:
                            if st.button(
                                "Confirmar Saída",
                                key=f"conf_{item['id']}",
                                width='stretch',
                            ):
                                resp_conf = requests.patch(
                                    f"{API_URL}/saidas/{item['id']}/confirmar",
                                    headers=obter_headers(),
                                )
                                if resp_conf.status_code == 200:
                                    st.success(
                                        f"Saída de {item['nome_estudante']} registada!"
                                    )
                                    st.rerun()
                                else:
                                    st.error("Erro ao confirmar liberação.")
        else:
            st.error("Erro ao carregar lista de pendentes.")

# ----------------------------------------------------------------------
# ABA 3: HISTÓRICO GERAL (TODOS OS PERFIS)
# ----------------------------------------------------------------------
if "Histórico e Auditoria" in abas_disponiveis:
    idx = abas_disponiveis.index("Histórico e Auditoria")
    with abas[idx]:
        st.header("Histórico Completo de Saídas")

        resp_hist = requests.get(
            f"{API_URL}/saidas/historico", headers=obter_headers()
        )
        if resp_hist.status_code == 200:
            historico = resp_hist.json()
            if not historico:
                st.info("Nenhum registo encontrado.")
            else:
                linhas = []
                for h in historico:
                    linhas.append(
                        {
                            "ID": h["id"],
                            "Estudante": h["nome_estudante"],
                            "Matrícula": h["matricula"],
                            "Turma": h["turma"],
                            "Motivo": (
                                h["motivo"]["descricao"]
                                if h.get("motivo")
                                else "-"
                            ),
                            "Estado": h["status"],
                            "Autorizado Por": (
                                h["autorizador"]["nome"]
                                if h.get("autorizador")
                                else "-"
                            ),
                            "Data Autorização": (
                                h["data_autorizacao"][:16].replace("T", " ")
                                if h.get("data_autorizacao")
                                else "-"
                            ),
                            "Porteiro": (
                                h["porteiro"]["nome"]
                                if h.get("porteiro")
                                else "-"
                            ),
                            "Data Saída": (
                                h["data_saida_efetiva"][:16].replace("T", " ")
                                if h.get("data_saida_efetiva")
                                else "-"
                            ),
                        }
                    )
                df = pd.DataFrame(linhas)
                df = df.sort_values(by="ID", ascending=True)
                st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.error("Erro ao consultar histórico.")

# ----------------------------------------------------------------------
# ABA 4: GESTÃO DE MOTIVOS (ADMIN)
# ----------------------------------------------------------------------
if "Gestão de Motivos" in abas_disponiveis:
    idx = abas_disponiveis.index("Gestão de Motivos")
    with abas[idx]:
        st.header("Cadastrar Novo Motivo de Saída")
        with st.form("form_novo_motivo", clear_on_submit=True):
            novo_motivo = st.text_input("Descrição do Motivo")
            cadastrar = st.form_submit_button("Adicionar Motivo")

            if cadastrar:
                if novo_motivo.strip():
                    resp_cad = requests.post(
                        f"{API_URL}/motivos/",
                        json={"descricao": novo_motivo.strip()},
                        headers=obter_headers(),
                    )
                    if resp_cad.status_code == 201:
                        st.success("Motivo registado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao cadastrar motivo.")
                else:
                    st.warning("Preencha a descrição do motivo.")