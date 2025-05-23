import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta, time
import calendar
from pathlib import Path
from telegram_notificacao import enviar_notificacao_telegram

# ==============================================
# CONFIGURAÇÃO INICIAL
# ==============================================
st.set_page_config(
    page_title="Gestão de Medicamentos - Casa de Repouso",
    page_icon="🏥",
    layout="wide"
)

# Configurações de notificação
token = "8102034090:AAEJFwf4Hx7aaHEKzUx0Ob6lQE_GWuVQRzQ"
chat_id = "6113530990"  # chat_id deve ser string
mensagem = "Hora de tomar o remédio!"

# ==============================================
# ESTILOS CSS
# ==============================================
def carregar_estilos():
    st.markdown("""
        <style>
        :root {
            --primary: #4a6fa5;
            --secondary: #166088;
            --accent: #4fc3f7;
            --background: #f5f9ff;
            --card: #ffffff;
            --text: #333333;
            --border: #e0e0e0;
        }

        .main {
            background-color: var(--background);
        }

        .titulo {
            font-size: 2rem;
            font-weight: bold;
            color: var(--secondary);
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent);
        }

        .card {
            background-color: var(--card);
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }

        .stButton>button {
            background-color: var(--primary);
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            border: none;
            transition: all 0.3s;
        }

        .stButton>button:hover {
            background-color: var(--secondary);
            transform: scale(1.02);
        }

        .status-tomou {
            color: #2e7d32;
            font-weight: bold;
            background-color: #e8f5e9;
            padding: 0.3rem 0.6rem;
            border-radius: 20px;
        }

        .status-nao-tomou {
            color: #c62828;
            font-weight: bold;
            background-color: #ffebee;
            padding: 0.3rem 0.6rem;
            border-radius: 20px;
        }

        .dia-calendario {
            padding: 0.5rem;
            min-height: 80px;
            border: 1px solid var(--border);
            text-align: center;
        }

        .dia-atual {
            background-color: #e3f2fd;
            font-weight: bold;
        }

        .com-medicamento {
            background-color: #e8f5e9;
        }

        .notificacao-botoes {
            margin-top: 1rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        </style>
    """, unsafe_allow_html=True)

# ==============================================
# BANCO DE DADOS
# ==============================================
class DatabaseManager:
    def __init__(self):
        self.db_path = Path('data/pacientes.db')
        self.conn = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
    
    def connect(self):
        try:
            Path('data').mkdir(exist_ok=True)
            if not self.db_path.exists():
                self.db_path.touch()
                
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._initialize_tables()
            return self.conn
        except Exception as e:
            st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
            return None
    
    def _initialize_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                idade INTEGER,
                condicao TEXT,
                data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                medicamento TEXT NOT NULL,
                horario TEXT NOT NULL,
                data TEXT NOT NULL,
                tomou INTEGER DEFAULT 0,
                observacoes TEXT,
                FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
            )
        """)
        
        self.conn.commit()

# ==============================================
# FUNÇÕES DE PACIENTES
# ==============================================
def adicionar_paciente(conn, nome, idade, condicao):
    try:
        if not nome.strip():
            st.error("O nome não pode estar vazio")
            return False
        if idade <= 0:
            st.error("Idade inválida")
            return False
            
        conn.execute(
            "INSERT INTO pacientes (nome, idade, condicao) VALUES (?, ?, ?)", 
            (nome.strip(), int(idade), condicao.strip())
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao adicionar paciente: {e}")
        return False

def listar_pacientes(conn):
    try:
        return conn.execute("SELECT * FROM pacientes ORDER BY nome").fetchall()
    except sqlite3.Error as e:
        st.error(f"Erro ao listar pacientes: {e}")
        return []

def atualizar_paciente(conn, id_paciente, nome, idade, condicao):
    try:
        conn.execute(
            "UPDATE pacientes SET nome=?, idade=?, condicao=? WHERE id=?", 
            (nome.strip(), int(idade), condicao.strip(), id_paciente)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao atualizar paciente: {e}")
        return False

def remover_paciente(conn, id_paciente):
    try:
        conn.execute("DELETE FROM pacientes WHERE id=?", (id_paciente,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao remover paciente: {e}")
        return False

# ==============================================
# FUNÇÕES DE MEDICAMENTOS
# ==============================================
def adicionar_medicamento(conn, paciente_id, medicamento, horario, data, observacoes):
    try:
        if not medicamento.strip():
            st.error("O nome do medicamento não pode estar vazio")
            return False
            
        conn.execute("""
            INSERT INTO medicamentos 
            (paciente_id, medicamento, horario, data, observacoes) 
            VALUES (?, ?, ?, ?, ?)""", 
            (paciente_id, medicamento.strip(), horario, data, observacoes.strip())
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao adicionar medicamento: {e}")
        return False

def listar_medicamentos_hoje(conn):
    try:
        hoje = date.today().strftime("%Y-%m-%d")
        return conn.execute("""
            SELECT m.id, p.nome, m.medicamento, m.horario, m.tomou, m.observacoes 
            FROM medicamentos m
            JOIN pacientes p ON m.paciente_id = p.id
            WHERE m.data = ?
            ORDER BY m.horario""", (hoje,)
        ).fetchall()
    except sqlite3.Error as e:
        st.error(f"Erro ao listar medicamentos: {e}")
        return []

def listar_medicamentos_por_data(conn, data):
    try:
        return conn.execute("""
            SELECT m.id, p.nome, m.medicamento, m.horario, m.tomou, m.observacoes 
            FROM medicamentos m
            JOIN pacientes p ON m.paciente_id = p.id
            WHERE m.data = ?
            ORDER BY m.horario""", (data,)
        ).fetchall()
    except sqlite3.Error as e:
        st.error(f"Erro ao listar medicamentos: {e}")
        return []

def atualizar_status_medicamento(conn, id_medicamento, status):
    try:
        conn.execute("UPDATE medicamentos SET tomou=? WHERE id=?", (status, id_medicamento))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Erro ao atualizar status do medicamento: {e}")
        return False

def contar_medicamentos_por_data(conn, data):
    try:
        result = conn.execute("SELECT COUNT(*) FROM medicamentos WHERE data = ?", (data,)).fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        st.error(f"Erro ao contar medicamentos: {e}")
        return 0

# ==============================================
# COMPONENTES DA INTERFACE
# ==============================================
def exibir_calendario(conn):
    st.subheader("📅 Calendário de Medicamentos")
    hoje = date.today()
    
    # Seletor de mês/ano
    col1, col2 = st.columns(2)
    with col1:
        mes = st.selectbox("Mês", list(calendar.month_name[1:]), index=hoje.month-1)
    with col2:
        ano = st.selectbox("Ano", range(hoje.year-1, hoje.year+3), index=1)
    
    # Gerar calendário
    mes_num = list(calendar.month_name).index(mes)
    cal = calendar.monthcalendar(ano, mes_num)
    
    # Exibir calendário
    st.markdown(f"### {mes} {ano}")
    
    # Cabeçalho dos dias da semana
    dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    cols = st.columns(7)
    for i, dia in enumerate(dias_semana):
        cols[i].write(f"**{dia}**")
    
    # Dias do mês
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            if dia == 0:
                cols[i].write("")
            else:
                data_str = f"{ano}-{mes_num:02d}-{dia:02d}"
                data_completa = date(ano, mes_num, dia)
                
                # Classes CSS
                classes = ["dia-calendario"]
                if data_completa == hoje:
                    classes.append("dia-atual")
                
                num_meds = contar_medicamentos_por_data(conn, data_str)
                if num_meds > 0:
                    classes.append("com-medicamento")
                
                with cols[i]:
                    st.markdown(f"""
                        <div class="{' '.join(classes)}">
                            <strong>{dia}</strong>
                            {f'<br><small>{num_meds} meds</small>' if num_meds > 0 else ''}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Mostrar detalhes ao clicar
                    if num_meds > 0:
                        with st.expander("Ver medicamentos"):
                            medicamentos = listar_medicamentos_por_data(conn, data_str)
                            for med in medicamentos:
                                st.write(f"**{med[1]}** - {med[2]} às {med[3]}")
                                if med[5]:
                                    st.caption(f"Obs: {med[5]}")

def exibir_medicamentos_hoje(conn):
    st.subheader("💊 Medicamentos para Hoje")
    hoje_str = date.today().strftime("%d/%m/%Y")
    st.markdown(f"### {hoje_str}")
    
    medicamentos_hoje = listar_medicamentos_hoje(conn)
    
    if not medicamentos_hoje:
        st.info("Nenhum medicamento agendado para hoje.")
    else:
        for med in medicamentos_hoje:
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                
                cols = st.columns([0.3, 0.3, 0.2, 0.2])
                with cols[0]: st.write(f"**Paciente:** {med[1]}")
                with cols[1]: st.write(f"**Medicamento:** {med[2]}")
                with cols[2]: st.write(f"**Horário:** {med[3]}")
                with cols[3]: 
                    status = "✅ Tomou" if med[4] else "❌ Não tomou"
                    st.write(f"**Status:** {status}")
                
                if med[5]:
                    with st.expander("Observações"):
                        st.write(med[5])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Marcar como tomado - {med[2]}", key=f"tomou_{med[0]}"):
                        if atualizar_status_medicamento(conn, med[0], 1):
                            st.success("Status atualizado!")
                            st.rerun()
                with col2:
                    if st.button(f"Marcar como não tomado - {med[2]}", key=f"nao_tomou_{med[0]}"):
                        if atualizar_status_medicamento(conn, med[0], 0):
                            st.success("Status atualizado!")
                            st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)

def exibir_pacientes(conn):
    st.subheader("👴 Cadastro de Pacientes")
    
    with st.expander("➕ Adicionar Novo Paciente", expanded=True):
        with st.form("form_paciente", clear_on_submit=True):
            nome = st.text_input("Nome completo*", help="Obrigatório")
            idade = st.number_input("Idade*", 0, 120, help="Obrigatório")
            condicao = st.text_area("Condições médicas e observações")
            
            if st.form_submit_button("💾 Salvar Paciente"):
                if nome and idade:
                    if adicionar_paciente(conn, nome, idade, condicao):
                        st.success("Paciente cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.error("Por favor, preencha pelo menos o nome e a idade do paciente.")
    
    st.markdown("---")
    st.subheader("📋 Lista de Pacientes")
    pacientes = listar_pacientes(conn)
    
    if not pacientes:
        st.info("Nenhum paciente cadastrado ainda.")
    else:
        for paciente in pacientes:
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                with col1:
                    st.write(f"**{paciente[1]}**")
                    st.caption(paciente[3] if paciente[3] else "Sem condições registradas")
                with col2:
                    st.write(f"**Idade:** {paciente[2]}")
                
                with col3:
                    with st.popover("⚙️ Ações"):
                        with st.form(f"editar_{paciente[0]}"):
                            novo_nome = st.text_input("Nome", paciente[1])
                            nova_idade = st.number_input("Idade", value=paciente[2])
                            nova_condicao = st.text_area("Condição", paciente[3] if paciente[3] else "")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Atualizar"):
                                    if atualizar_paciente(conn, paciente[0], novo_nome, nova_idade, nova_condicao):
                                        st.success("Paciente atualizado!")
                                        st.rerun()
                            with col2:
                                if st.form_submit_button("❌ Remover"):
                                    if remover_paciente(conn, paciente[0]):
                                        st.success("Paciente removido!")
                                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)

def exibir_novo_medicamento(conn):
    st.subheader("➕ Adicionar Novo Medicamento")
    
    pacientes = listar_pacientes(conn)
    if not pacientes:
        st.warning("Cadastre pacientes antes de adicionar medicamentos.")
    else:
        with st.form("form_medicamento", clear_on_submit=True):
            paciente_id = st.selectbox(
                "Paciente*",
                options=pacientes,
                format_func=lambda x: f"{x[1]} (ID: {x[0]})",
                help="Obrigatório"
            )
            medicamento = st.text_input("Medicamento*", help="Obrigatório")
            
            col1, col2 = st.columns(2)
            with col1:
                horario = st.time_input("Horário*", time(8, 0), help="Obrigatório")
            with col2:
                data = st.date_input("Data*", date.today())
            
            observacoes = st.text_area("Observações")
            
            if st.form_submit_button("💾 Salvar Medicamento"):
                if medicamento and paciente_id:
                    if adicionar_medicamento(
                        conn, 
                        paciente_id[0], 
                        medicamento, 
                        horario.strftime("%H:%M"), 
                        data.strftime("%Y-%m-%d"), 
                        observacoes
                    ):
                        st.success("Medicamento cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.error("Por favor, preencha todos os campos obrigatórios.")

def exibir_relatorios(conn):
    st.subheader("📊 Relatórios")
    
    st.markdown("### Estatísticas")
    col1, col2, col3 = st.columns(3)
    
    try:
        # Total de pacientes
        total_pacientes = conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]
        col1.metric("Total de Pacientes", total_pacientes)
        
        # Total de medicamentos hoje
        hoje = date.today().strftime("%Y-%m-%d")
        meds_hoje = conn.execute("SELECT COUNT(*) FROM medicamentos WHERE data = ?", (hoje,)).fetchone()[0]
        col2.metric("Medicamentos Hoje", meds_hoje)
        
        # Taxa de adesão
        meds_tomados = conn.execute("SELECT COUNT(*) FROM medicamentos WHERE tomou = 1 AND data = ?", (hoje,)).fetchone()[0]
        taxa = (meds_tomados / meds_hoje * 100) if meds_hoje > 0 else 0
        col3.metric("Taxa de Adesão Hoje", f"{taxa:.1f}%")
        
        # Gráfico de medicamentos por dia (últimos 7 dias)
        st.markdown("---")
        st.markdown("### Medicamentos dos Últimos 7 Dias")
        
        datas = []
        counts = []
        for i in range(7):
            data = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            count = conn.execute("SELECT COUNT(*) FROM medicamentos WHERE data = ?", (data,)).fetchone()[0]
            datas.append(data)
            counts.append(count)
        
        # Inverter para mostrar do mais recente para o mais antigo
        datas.reverse()
        counts.reverse()
        
        st.bar_chart(dict(zip([datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m") for d in datas], counts)))
        
    except sqlite3.Error as e:
        st.error(f"Erro ao gerar relatórios: {e}")

# ==============================================
# APLICAÇÃO PRINCIPAL
# ==============================================
def main():
    carregar_estilos()
    
    # Cabeçalho
    st.markdown('<div class="titulo">🏥 Gestão de Medicamentos - Casa de Repouso</div>', unsafe_allow_html=True)
    
    # Seção de Notificações
    with st.container():
        st.markdown('<div class="notificacao-botoes">', unsafe_allow_html=True)
        st.subheader("🔔 Notificações")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Enviar notificação de teste"):
                sucesso = enviar_notificacao_telegram(token, chat_id, mensagem)
                if sucesso:
                    st.success("Notificação enviada!")
                else:
                    st.error("Falha ao enviar notificação.")
        
        with col2:
            if st.button("Enviar notificação com horário atual"):
                hora_agora = datetime.now().strftime('%H:%M:%S')
                mensagem_com_hora = f"Hora de tomar o remédio! Agora são {hora_agora}"
                sucesso = enviar_notificacao_telegram(token, chat_id, mensagem_com_hora)
                if sucesso:
                    st.success(f"Notificação enviada com horário {hora_agora}!")
                else:
                    st.error("Falha ao enviar notificação.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Conexão com o banco de dados
    with DatabaseManager() as db:
        if not db.conn:
            st.error("Não foi possível conectar ao banco de dados. O aplicativo não pode continuar.")
            return
        
        # Abas principais
        abas = st.tabs(["📅 Calendário", "💊 Hoje", "👴 Pacientes", "➕ Novo Medicamento", "📊 Relatórios"])
        
        with abas[0]:  # Aba Calendário
            exibir_calendario(db.conn)
        
        with abas[1]:  # Aba Hoje
            exibir_medicamentos_hoje(db.conn)
        
        with abas[2]:  # Aba Pacientes
            exibir_pacientes(db.conn)
        
        with abas[3]:  # Aba Novo Medicamento
            exibir_novo_medicamento(db.conn)
        
        with abas[4]:  # Aba Relatórios
            exibir_relatorios(db.conn)

if __name__ == "__main__":
    main()