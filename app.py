import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pátio", layout="wide", page_icon="🚛")

URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ9PusBp9wysomNlU82sWHI04xUiZAMLC1-ltv1zOff_pw7gCXcINpOFHwd1Y6w-d54_VPDU4kKui6y/pub?gid=2072393578&single=true&output=csv"

# ==============================================================================
# ⚙️ 1. CONFIGURAÇÃO DE METAS (SLA DE ATENDIMENTO)
# ==============================================================================
META_PUXADA_E_OUTROS = 70  
META_PONTO_APOIO = 30      

# ==============================================================================
# ⚙️ 2. CONFIGURAÇÃO DE TURNOS (HORÁRIOS DE CORTE)
# ==============================================================================
CORTE_TURNO_A_SEMANA = "14:48"  
CORTE_TURNO_B_SEMANA = "20:48"  

CORTE_TURNO_A_SABADO = "11:00"  
CORTE_TURNO_B_SABADO = "15:00"  

# ==============================================================================
# ⚙️ 3. CARGA HORÁRIA LÍQUIDA (BASE PARA TAXA DE OCUPAÇÃO)
# ==============================================================================
MINUTOS_TURNO_SEMANA_A = 468 
MINUTOS_TURNO_SEMANA_B = 468 
MINUTOS_TURNO_SEMANA_C = 450 

MINUTOS_TURNO_SABADO_A = 300 
MINUTOS_TURNO_SABADO_B = 300 
MINUTOS_TURNO_SABADO_C = 240 

# ==============================================================================
# ⚙️ 4. LIMITE DE OCIOSIDADE (GUILHOTINA DE HIATOS)
# ==============================================================================
LIMITE_MAXIMO_HIATO_MINUTOS = 240 
# ==============================================================================

# Escalas de cores customizadas
ESCALA_CORES_TAI = ["#2E7D32", "#66BB6A", "#F9A825", "#EF6C00", "#C62828"] 
ESCALA_CORES_HIATO = ["#E3F2FD", "#90CAF9", "#42A5F5", "#1E88E5", "#0D47A1"] 
CORES_TURNOS = {"Turno A": "#42A5F5", "Turno B": "#26A69A", "Turno C": "#7E57C2"}

# --- FUNÇÃO ANTI-DEFORMAÇÃO ---
def truncar_texto(texto, limite):
    texto = str(texto).strip()
    return texto[:limite] + "..." if len(texto) > limite else texto

# --- FUNÇÃO VISUAL: CARTÕES DE TURNO COM 4 MÉTRICAS ---
def exibir_card_turno(titulo, icone, volume, tai, ocupacao, conformidade, cor_tema):
    html = f"""
    <div style="
        background-color: white;
        border-left: 6px solid {cor_tema};
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-top: 1px solid #f0f2f6;
        border-right: 1px solid #f0f2f6;
        border-bottom: 1px solid #f0f2f6;
    ">
        <h4 style="margin-top: 0px; margin-bottom: 15px; color: #31333F; display: flex; align-items: center; gap: 8px; font-weight: 600;">
            <span style="font-size: 1.3em;">{icone}</span> {titulo}
        </h4>
        <div style="display: flex; justify-content: space-between; text-align: left;">
            <div style="flex: 0.8; padding-right: 5px;">
                <p style="font-size: 12px; margin-bottom: 0px; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Vol.</p>
                <p style="font-size: 22px; font-weight: bold; margin-top: 2px; color: #111;">{volume}</p>
            </div>
            <div style="flex: 1.2; padding-right: 5px;">
                <p style="font-size: 12px; margin-bottom: 0px; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">TAI Méd.</p>
                <p style="font-size: 22px; font-weight: bold; margin-top: 2px; color: #111;">{tai}</p>
            </div>
            <div style="flex: 1.2; padding-right: 5px;">
                <p style="font-size: 12px; margin-bottom: 0px; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Conform.</p>
                <p style="font-size: 22px; font-weight: bold; margin-top: 2px; color: #111;">{conformidade:.1f}%</p>
            </div>
            <div style="flex: 1;">
                <p style="font-size: 12px; margin-bottom: 0px; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Ocupação</p>
                <p style="font-size: 22px; font-weight: bold; margin-top: 2px; color: {cor_tema};">{ocupacao:.1f}%</p>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- FUNÇÃO MATEMÁTICA DE JUSTIÇA OPERACIONAL ---
def calcular_turno_destaque(df_filtrado, mins_a, mins_b, mins_c):
    turnos_data = []
    
    for t, m_disp in [('Turno A', mins_a), ('Turno B', mins_b), ('Turno C', mins_c)]:
        df_t = df_filtrado[df_filtrado['Turno'] == t]
        if len(df_t) > 0 and m_disp > 0:
            conf = (df_t['Dentro_da_Meta'].sum() / len(df_t)) * 100
            tai = df_t['TAI (Minutos)'].mean()
            ocup = (df_t['TAI (Minutos)'].sum() / m_disp) * 100
            turnos_data.append({'Turno': t, 'Vol': len(df_t), 'Conf': conf, 'TAI': tai, 'Ocup': ocup})

    if not turnos_data: return "Sem dados", "Nenhuma operação realizada."
    if len(turnos_data) == 1: return turnos_data[0]['Turno'], "Foi a única equipa com carretas finalizadas neste período."

    turnos_data.sort(key=lambda x: (round(x['Conf'], 1), -round(x['TAI'], 1), round(x['Ocup'], 1)), reverse=True)
    
    vencedor = turnos_data[0]
    segundo = turnos_data[1]

    if round(vencedor['Conf'], 1) > round(segundo['Conf'], 1):
        motivo = f"Teve o melhor desempenho no cumprimento dos prazos."
    elif round(vencedor['TAI'], 1) < round(segundo['TAI'], 1):
        motivo = f"Empate em conformidade, mas foi o mais ágil do período (TAI médio de {vencedor['TAI']:.0f} min)."
    else:
        motivo = f"Empate técnico em tempo e metas, mas aguentou maior carga de trabalho ({vencedor['Ocup']:.1f}% de ocupação)."

    return vencedor['Turno'], motivo

def padronizar_operacao(op):
    if pd.isna(op): return "NÃO IDENTIFICADA"
    op_str = str(op).upper().strip()
    if "FÁBRICA" in op_str or "FABRICA" in op_str or "PORTARE" in op_str or "TELHA SUL" in op_str:
        return "PUXADA FÁBRICA"
    if "PONTO DE APOIO" in op_str or op_str == "PA":
        return "PONTO DE APOIO"
    return op_str

def formatar_tempo(minutos_totais):
    if pd.isna(minutos_totais): return "0min"
    sinal = "-" if minutos_totais < 0 else ""
    minutos_abs = abs(minutos_totais)
    horas = int(minutos_abs // 60)
    minutos = int(minutos_abs % 60)
    return f"{sinal}{horas}h {minutos:02d}m" if horas > 0 else f"{sinal}{minutos}min"

def limpar_hora(valor):
    if pd.isna(valor) or str(valor).strip() == "": return None
    txt = str(valor).lower().strip().replace('h', ':').replace(' ', '')
    partes = txt.split(':')
    if len(partes) >= 2:
        return f"{partes[0].zfill(2)}:{partes[1].zfill(2)}"
    return txt

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        df_bruto = pd.read_csv(URL_CSV)
        coluna_carimbo = df_bruto.columns[0] 
        coluna_placa = [col for col in df_bruto.columns if 'Placa' in col][0]
        coluna_entrada = [col for col in df_bruto.columns if 'Entrada' in col][0]
        coluna_saida = [col for col in df_bruto.columns if 'Saída' in col or 'Saida' in col][0]
        coluna_operacao = [col for col in df_bruto.columns if 'Operação' in col or 'Operacao' in col][0]
        colunas_motorista = [col for col in df_bruto.columns if 'Motorista' in col or 'Nome' in col]
        coluna_motorista = colunas_motorista[0] if colunas_motorista else None
        
        df = df_bruto.copy()
        df[coluna_operacao] = df[coluna_operacao].apply(padronizar_operacao)
        df['Data_Operacao'] = pd.to_datetime(df[coluna_carimbo], dayfirst=True, errors='coerce').dt.date
        df['Entrada_Texto'] = df[coluna_entrada].apply(limpar_hora)
        df['Saída_Texto'] = df[coluna_saida].apply(limpar_hora)
        df['Entrada'] = pd.to_datetime(df['Entrada_Texto'], format='%H:%M', errors='coerce')
        df['Saída'] = pd.to_datetime(df['Saída_Texto'], format='%H:%M', errors='coerce')
        
        df['TAI (Minutos)'] = (df['Saída'] - df['Entrada']).dt.total_seconds() / 60
        df.loc[df['TAI (Minutos)'] < 0, 'TAI (Minutos)'] += 1440
        
        df_processado = df.dropna(subset=['TAI (Minutos)', 'Data_Operacao']).copy()
        
        if not df_processado.empty:
            df_processado = df_processado.sort_values('Entrada')
            df_processado['Intervalo Chegada (Minutos)'] = df_processado['Entrada'].diff().dt.total_seconds() / 60
            df_processado['Intervalo Chegada (Minutos)'] = df_processado['Intervalo Chegada (Minutos)'].fillna(0)
            df_processado.loc[df_processado['Intervalo Chegada (Minutos)'] < 0, 'Intervalo Chegada (Minutos)'] += 1440
            df_processado['TAI_Formatado'] = df_processado['TAI (Minutos)'].apply(formatar_tempo)
            
            def classificar_turno(row):
                if pd.isna(row['Saída']): return "Indefinido"
                dia_semana = pd.to_datetime(row['Data_Operacao']).dayofweek 
                hora_saida = row['Saída'].time()
                
                hora_corte_madrugada = pd.to_datetime("05:00", format='%H:%M').time()

                if dia_semana == 5: 
                    corte_a = pd.to_datetime(CORTE_TURNO_A_SABADO, format='%H:%M').time()
                    corte_b = pd.to_datetime(CORTE_TURNO_B_SABADO, format='%H:%M').time()
                else: 
                    corte_a = pd.to_datetime(CORTE_TURNO_A_SEMANA, format='%H:%M').time()
                    corte_b = pd.to_datetime(CORTE_TURNO_B_SEMANA, format='%H:%M').time()

                if hora_saida <= hora_corte_madrugada: return "Turno C"
                elif hora_saida <= corte_a: return "Turno A"
                elif hora_saida <= corte_b: return "Turno B"
                else: return "Turno C"

            df_processado['Turno'] = df_processado.apply(classificar_turno, axis=1)

            def definir_meta(row):
                if row['Turno'] == 'Turno C':
                    return META_PUXADA_E_OUTROS 
                else:
                    return META_PONTO_APOIO if row[coluna_operacao] == "PONTO DE APOIO" else META_PUXADA_E_OUTROS

            df_processado['Meta_Alvo'] = df_processado.apply(definir_meta, axis=1)
            df_processado['Dentro_da_Meta'] = df_processado['TAI (Minutos)'] <= df_processado['Meta_Alvo']
            
            df_processado['Mes_Ano'] = pd.to_datetime(df_processado['Data_Operacao']).dt.strftime('%m/%Y')
        
        return df_processado, coluna_placa, coluna_operacao, coluna_motorista, df_bruto
        
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return pd.DataFrame(), "", "", None, pd.DataFrame()

df_completo, col_placa, col_operacao, col_motorista, df_bruto = carregar_dados()

# --- MENU LATERAL ---
st.sidebar.header("📅 Filtros do Painel")

if st.sidebar.button("🔄 Atualizar Dados Agora"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

if not df_completo.empty:
    meses_disponiveis = sorted(df_completo['Mes_Ano'].unique(), reverse=True)
    mes_selecionado = st.sidebar.selectbox("1. Selecione o Mês (Visão Macro):", meses_disponiveis)
    df_mes = df_completo[df_completo['Mes_Ano'] == mes_selecionado].copy()
    
    datas_disponiveis = sorted(df_mes['Data_Operacao'].unique(), reverse=True)
    data_selecionada = st.sidebar.selectbox("2. Selecione o Dia (Visão Diária):", datas_disponiveis)
    df_dia = df_mes[df_mes['Data_Operacao'] == data_selecionada].copy()
    
    if not df_dia.empty:
        df_dia = df_dia.sort_values('Entrada')
        df_dia['Saida_Anterior'] = df_dia['Saída'].shift(1)
        df_dia['Intervalo_Ociosidade'] = (df_dia['Entrada'] - df_dia['Saida_Anterior']).dt.total_seconds() / 60
else:
    df_mes = pd.DataFrame()
    df_dia = pd.DataFrame()

# --- INÍCIO DO PAINEL ---
st.title("📊 Monitoramento de Pátio e Descarga")

with st.expander("🛠️ Depuração: Clique aqui para ver os dados brutos da Planilha"):
    if not df_bruto.empty:
        st.dataframe(df_bruto)

st.markdown("---")

if not df_completo.empty:
    
    # ==========================================
    # VISÃO MACRO: MENSAL
    # ==========================================
    st.subheader(f"📅 Visão Geral do Mês ({mes_selecionado})")
    
    if not df_mes.empty:
        
        # 1. CÁLCULO PRÉVIO DOS MINUTOS DISPONÍVEIS TOTAIS NO MÊS
        datas_unicas_mes = df_mes['Data_Operacao'].unique()
        min_disp_mes_a, min_disp_mes_b, min_disp_mes_c = 0, 0, 0
        
        for d in datas_unicas_mes:
            dia_semana = pd.to_datetime(d).dayofweek
            if dia_semana == 5: 
                min_disp_mes_a += MINUTOS_TURNO_SABADO_A
                min_disp_mes_b += MINUTOS_TURNO_SABADO_B
                min_disp_mes_c += MINUTOS_TURNO_SABADO_C
            elif dia_semana < 5: 
                min_disp_mes_a += MINUTOS_TURNO_SEMANA_A
                min_disp_mes_b += MINUTOS_TURNO_SEMANA_B
                min_disp_mes_c += MINUTOS_TURNO_SEMANA_C
                
        min_disp_total_mes = min_disp_mes_a + min_disp_mes_b + min_disp_mes_c
        
        # 2. CÁLCULOS GERAIS DO MÊS
        vol_mes = len(df_mes)
        tai_medio_mes = df_mes['TAI (Minutos)'].mean() if vol_mes > 0 else 0
        dentro_meta_mes = int(df_mes['Dentro_da_Meta'].sum())
        conf_mes = (dentro_meta_mes / vol_mes) * 100 if vol_mes > 0 else 0
        ocup_mes = (df_mes['TAI (Minutos)'].sum() / min_disp_total_mes) * 100 if min_disp_total_mes > 0 else 0
        
        # 3. EXIBIÇÃO EM 5 COLUNAS (NOVO LAYOUT GERAL)
        cm1, cm2, cm3, cm4, cm5 = st.columns(5)
        cm1.metric("Volume Total", vol_mes)
        cm2.metric("TAI Médio", formatar_tempo(tai_medio_mes).replace('<b>', '').replace('</b>', ''))
        cm3.metric("Dentro da Meta (Qtd)", dentro_meta_mes)
        cm4.metric("Conformidade (%)", f"{conf_mes:.1f}%")
        cm5.metric("Ocupação Geral (%)", f"{ocup_mes:.1f}%")
        
        st.write("") 
        
        df_operacao_mensal = df_mes.groupby(col_operacao)['TAI (Minutos)'].mean().reset_index()
        df_operacao_mensal = df_operacao_mensal.sort_values(by='TAI (Minutos)', ascending=True)
        df_operacao_mensal['TAI_Formatado'] = df_operacao_mensal['TAI (Minutos)'].apply(formatar_tempo)
        df_operacao_mensal['Operacao_Limpa'] = df_operacao_mensal[col_operacao].apply(lambda x: truncar_texto(x, 20))
        
        max_mes = df_operacao_mensal['TAI (Minutos)'].max() if not df_operacao_mensal.empty else 1
        df_operacao_mensal['pos_texto'] = df_operacao_mensal['TAI (Minutos)'].apply(lambda x: 'inside' if x >= max_mes * 0.92 else 'outside')
        
        fig_op_mensal = px.bar(df_operacao_mensal, y='Operacao_Limpa', x='TAI (Minutos)', text='TAI_Formatado', color='TAI (Minutos)', color_continuous_scale=ESCALA_CORES_TAI, orientation='h')
        altura_mensal = max(300, len(df_operacao_mensal) * 60)
        limite_x_mes = max(max_mes, META_PUXADA_E_OUTROS) * 1.15
        
        fig_op_mensal.update_traces(textposition=df_operacao_mensal['pos_texto'].tolist(), textfont_size=15, textfont_color='black', cliponaxis=False, hovertemplate="<b>Operação:</b> %{y}<br><b>Tempo Médio:</b> %{text}<extra></extra>")
        fig_op_mensal.update_layout(height=altura_mensal, yaxis_title="", xaxis=dict(title="Tempo Médio (Minutos)", range=[0, limite_x_mes]), showlegend=False, coloraxis_showscale=False, margin=dict(t=30, r=10, l=160, b=30))
        st.plotly_chart(fig_op_mensal, use_container_width=True)

        # 🏆 PRODUTIVIDADE POR TURNO (MENSAL)
        st.markdown("---")
        st.subheader("🏆 Produtividade por Turno no Mês (A, B e C)")
                
        colA_mes, colB_mes, colC_mes = st.columns(3)
        
        df_turno_a_mes = df_mes[df_mes['Turno'] == 'Turno A']
        vol_a_mes = len(df_turno_a_mes)
        tai_a_mes = df_turno_a_mes['TAI (Minutos)'].mean() if vol_a_mes > 0 else 0
        ocup_a_mes = (df_turno_a_mes['TAI (Minutos)'].sum() / min_disp_mes_a) * 100 if min_disp_mes_a > 0 else 0
        conf_a_mes = (df_turno_a_mes['Dentro_da_Meta'].sum() / vol_a_mes) * 100 if vol_a_mes > 0 else 0
        with colA_mes:
            exibir_card_turno("Turno A", "☀️", vol_a_mes, formatar_tempo(tai_a_mes), ocup_a_mes, conf_a_mes, CORES_TURNOS["Turno A"])
            
        df_turno_b_mes = df_mes[df_mes['Turno'] == 'Turno B']
        vol_b_mes = len(df_turno_b_mes)
        tai_b_mes = df_turno_b_mes['TAI (Minutos)'].mean() if vol_b_mes > 0 else 0
        ocup_b_mes = (df_turno_b_mes['TAI (Minutos)'].sum() / min_disp_mes_b) * 100 if min_disp_mes_b > 0 else 0
        conf_b_mes = (df_turno_b_mes['Dentro_da_Meta'].sum() / vol_b_mes) * 100 if vol_b_mes > 0 else 0
        with colB_mes:
            exibir_card_turno("Turno B", "🌙", vol_b_mes, formatar_tempo(tai_b_mes), ocup_b_mes, conf_b_mes, CORES_TURNOS["Turno B"])

        df_turno_c_mes = df_mes[df_mes['Turno'] == 'Turno C']
        vol_c_mes = len(df_turno_c_mes)
        tai_c_mes = df_turno_c_mes['TAI (Minutos)'].mean() if vol_c_mes > 0 else 0
        ocup_c_mes = (df_turno_c_mes['TAI (Minutos)'].sum() / min_disp_mes_c) * 100 if min_disp_mes_c > 0 else 0
        conf_c_mes = (df_turno_c_mes['Dentro_da_Meta'].sum() / vol_c_mes) * 100 if vol_c_mes > 0 else 0
        with colC_mes:
            exibir_card_turno("Turno C", "🦉", vol_c_mes, formatar_tempo(tai_c_mes), ocup_c_mes, conf_c_mes, CORES_TURNOS["Turno C"])
            
        st.write("")
        vencedor_mes, motivo_mes = calcular_turno_destaque(df_mes, min_disp_mes_a, min_disp_mes_b, min_disp_mes_c)
        if vencedor_mes and vencedor_mes != "Sem dados":
            st.success(f"🥇 **Turno de Destaque no Mês:** {vencedor_mes} — *{motivo_mes}*")

        df_comp_mes = pd.DataFrame({"Turno": ["Turno A", "Turno B", "Turno C"], "Ocupação (%)": [ocup_a_mes, ocup_b_mes, ocup_c_mes]})
        fig_comp_mes = px.bar(df_comp_mes, x="Ocupação (%)", y="Turno", orientation='h', text=df_comp_mes["Ocupação (%)"].apply(lambda x: f"<b>{x:.1f}%</b>"), color="Turno", color_discrete_map=CORES_TURNOS)
        fig_comp_mes.update_traces(textposition='auto', textfont_size=16, textfont_color='black')
        fig_comp_mes.update_layout(height=200, showlegend=False, xaxis_title="Taxa de Ocupação Média Acumulada (%)", yaxis_title="", margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_comp_mes, use_container_width=True)

        st.write("")

        # ==========================================
        # 📋 TABELA: HISTÓRICO MENSAL
        # ==========================================
        st.markdown(f"**📋 Histórico de Atendimentos do Mês ({mes_selecionado})**")
        df_historico_mes = df_mes.sort_values(by=['Data_Operacao', 'Saída'], ascending=[False, False]).copy()
        
        df_historico_mes['Data_Exibicao'] = pd.to_datetime(df_historico_mes['Data_Operacao']).dt.strftime('%d/%m/%Y')
        df_historico_mes['TAI_Formatado_Limpo'] = df_historico_mes['TAI_Formatado'].str.replace('<b>', '').str.replace('</b>', '')
        
        if col_motorista and col_motorista in df_historico_mes.columns:
            df_exib_mes = df_historico_mes[['Data_Exibicao', col_placa, col_motorista, col_operacao, 'Turno', 'Entrada_Texto', 'Saída_Texto', 'TAI_Formatado_Limpo']]
            df_exib_mes.columns = ['Data', 'Placa', 'Motorista', 'Operação', 'Turno Final', 'Hora Entrada', 'Hora Saída', 'Tempo Total (TAI)']
        else:
            df_exib_mes = df_historico_mes[['Data_Exibicao', col_placa, col_operacao, 'Turno', 'Entrada_Texto', 'Saída_Texto', 'TAI_Formatado_Limpo']]
            df_exib_mes.columns = ['Data', 'Placa', 'Operação', 'Turno Final', 'Hora Entrada', 'Hora Saída', 'Tempo Total (TAI)']
            
        st.dataframe(df_exib_mes, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ==========================================
    # VISÃO MICRO: DIÁRIA
    # ==========================================
    st.subheader(f"🔍 Detalhamento Diário ({data_selecionada.strftime('%d/%m/%Y')})")
    
    if not df_dia.empty:
        # CÁLCULOS DO DIA GERAL
        dia_semana_sel = pd.to_datetime(data_selecionada).dayofweek
        if dia_semana_sel == 5:
            min_disp_dia_a, min_disp_dia_b, min_disp_dia_c = MINUTOS_TURNO_SABADO_A, MINUTOS_TURNO_SABADO_B, MINUTOS_TURNO_SABADO_C
        else:
            min_disp_dia_a, min_disp_dia_b, min_disp_dia_c = MINUTOS_TURNO_SEMANA_A, MINUTOS_TURNO_SEMANA_B, MINUTOS_TURNO_SEMANA_C
            
        min_disp_total_dia = min_disp_dia_a + min_disp_dia_b + min_disp_dia_c
        vol_dia = len(df_dia)
        tai_medio_dia = df_dia['TAI (Minutos)'].mean() if vol_dia > 0 else 0
        dentro_meta_dia = int(df_dia['Dentro_da_Meta'].sum())
        conf_dia = (dentro_meta_dia / vol_dia) * 100 if vol_dia > 0 else 0
        ocup_dia = (df_dia['TAI (Minutos)'].sum() / min_disp_total_dia) * 100 if min_disp_total_dia > 0 else 0

        # EXIBIÇÃO EM 5 COLUNAS DIÁRIAS
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Volume do Dia", vol_dia)
        c2.metric("TAI Médio", formatar_tempo(tai_medio_dia).replace('<b>', '').replace('</b>', ''))
        c3.metric("Dentro da Meta (Qtd)", dentro_meta_dia)
        c4.metric("Conformidade (%)", f"{conf_dia:.1f}%")
        c5.metric("Ocupação do Dia (%)", f"{ocup_dia:.1f}%")
        
        st.write("") 
        
        def gerar_grafico_gargalos(df_filtrado, tipo_aba="Geral"):
            if df_filtrado.empty:
                st.info("Nenhuma carreta finalizada para este filtro.")
                return None
            df_plot = df_filtrado.sort_values(by='TAI (Minutos)', ascending=True).copy()
            df_plot['Placa_Limpa'] = df_plot[col_placa].apply(lambda x: truncar_texto(x, 12))
            df_plot['Rotulo_Eixo_Y'] = "<b>" + df_plot['Placa_Limpa'] + "</b><br>(" + df_plot['Entrada_Texto'] + " às " + df_plot['Saída_Texto'] + ")"
            
            max_tai = df_plot['TAI (Minutos)'].max() if not df_plot.empty else 1
            df_plot['pos_texto'] = df_plot['TAI (Minutos)'].apply(lambda x: 'inside' if x >= max_tai * 0.92 else 'outside')
            
            fig = px.bar(df_plot, y='Rotulo_Eixo_Y', x='TAI (Minutos)', text='TAI_Formatado', color='TAI (Minutos)', color_continuous_scale=ESCALA_CORES_TAI, orientation='h')
            
            if tipo_aba == "Puxada Fábrica":
                fig.add_vline(x=META_PUXADA_E_OUTROS, line_dash="dash", line_color="#C62828", annotation_text="Meta (1h 10min)", annotation_position="bottom right")
            elif tipo_aba == "Ponto de Apoio":
                fig.add_vline(x=META_PONTO_APOIO, line_dash="dash", line_color="#C62828", annotation_text="Meta (30min)", annotation_position="bottom right")
            else:
                fig.add_vline(x=META_PONTO_APOIO, line_dash="dash", line_color="#EF6C00", annotation_text="Meta PA (30m)", annotation_position="bottom right")
                fig.add_vline(x=META_PUXADA_E_OUTROS, line_dash="dash", line_color="#C62828", annotation_text="Meta Puxada (1h 10m)", annotation_position="bottom right")
            
            altura_dinamica = max(350, len(df_plot) * 60)
            limite_x_dia = max(max_tai, META_PUXADA_E_OUTROS) * 1.15
            
            fig.update_traces(textposition=df_plot['pos_texto'].tolist(), textfont_size=15, textfont_color='black', cliponaxis=False, hovertemplate="<b>Duração Total:</b> %{text}<extra></extra>")
            fig.update_layout(height=altura_dinamica, yaxis_title="", xaxis=dict(title="Tempo Total (Minutos)", range=[0, limite_x_dia]), showlegend=False, coloraxis_showscale=False, margin=dict(t=30, r=10, l=160, b=30))
            return fig

        st.markdown("**🚛 Tempo de Atendimento por Placas (Gargalos)**")
        aba_geral, aba_fabrica, aba_pa = st.tabs(["🌎 Visão Geral (Todas)", "🏭 Puxada Fábrica", "📦 Ponto de Apoio"])
        with aba_geral:
            fig_geral = gerar_grafico_gargalos(df_dia, "Geral")
            if fig_geral: st.plotly_chart(fig_geral, use_container_width=True)
        with aba_fabrica:
            df_fabrica = df_dia[df_dia[col_operacao] == 'PUXADA FÁBRICA']
            fig_fabrica = gerar_grafico_gargalos(df_fabrica, "Puxada Fábrica")
            if fig_fabrica: st.plotly_chart(fig_fabrica, use_container_width=True)
        with aba_pa:
            df_pa = df_dia[df_dia[col_operacao] == 'PONTO DE APOIO']
            fig_pa = gerar_grafico_gargalos(df_pa, "Ponto de Apoio")
            if fig_pa: st.plotly_chart(fig_pa, use_container_width=True)

        st.write("") 

        # --- GRÁFICO 2: HIATO DE ATENDIMENTO ---
        st.markdown("### ⏳ Hiato de Atendimento entre Carretas de Puxada")
        
        df_ociosidade = df_dia.dropna(subset=['Intervalo_Ociosidade']).copy()
        df_ociosidade = df_ociosidade[df_ociosidade['Intervalo_Ociosidade'] > 0].copy()
        df_ociosidade = df_ociosidade[df_ociosidade['Intervalo_Ociosidade'] <= LIMITE_MAXIMO_HIATO_MINUTOS].copy()
        
        if not df_ociosidade.empty:
            df_ociosidade['Hora_Saida_Ant'] = df_ociosidade['Saida_Anterior'].dt.strftime('%H:%M')
            df_ociosidade['Hora_Ent_Nova'] = df_ociosidade['Entrada'].dt.strftime('%H:%M')
            df_ociosidade['Periodo_Ocioso'] = df_ociosidade['Hora_Saida_Ant'] + " às " + df_ociosidade['Hora_Ent_Nova']
            df_ociosidade['Ociosidade_Formatada'] = df_ociosidade['Intervalo_Ociosidade'].apply(formatar_tempo)
            df_ociosidade = df_ociosidade.sort_values(by='Intervalo_Ociosidade', ascending=True)
            
            max_oci = df_ociosidade['Intervalo_Ociosidade'].max() if not df_ociosidade.empty else 1
            df_ociosidade['pos_texto'] = df_ociosidade['Intervalo_Ociosidade'].apply(lambda x: 'inside' if x >= max_oci * 0.92 else 'outside')
            
            fig_ociosidade = px.bar(df_ociosidade, y='Periodo_Ocioso', x='Intervalo_Ociosidade', text='Ociosidade_Formatada', color='Intervalo_Ociosidade', color_continuous_scale=ESCALA_CORES_HIATO, orientation='h')
            altura_dinamica_oci = max(300, len(df_ociosidade) * 50)
            limite_x_oci = max_oci * 1.15
            
            fig_ociosidade.update_traces(textposition=df_ociosidade['pos_texto'].tolist(), textfont_size=15, textfont_color='black', cliponaxis=False, hovertemplate="<b>Hiato Sem Carreta:</b> %{y}<br><b>Tempo decorrido:</b> %{text}<extra></extra>")
            if max_oci <= 30: passo_eixo = 5
            elif max_oci <= 60: passo_eixo = 10
            elif max_oci <= 120: passo_eixo = 15
            else: passo_eixo = 30
            
            fig_ociosidade.update_layout(height=altura_dinamica_oci, yaxis_title="Janela de Horário do Hiato", xaxis=dict(title="Minutos Sem Recebimento", range=[0, limite_x_oci], dtick=passo_eixo), showlegend=False, coloraxis_showscale=False, margin=dict(t=30, r=10, l=120, b=30), plot_bgcolor='rgba(0,0,0,0)')
            fig_ociosidade.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E0E0E0')
            st.plotly_chart(fig_ociosidade, use_container_width=True)
        else:
            st.info(f"Sem hiatos operacionais no período. (Nota: Hiatos maiores que {LIMITE_MAXIMO_HIATO_MINUTOS} minutos são ignorados por serem considerados fim de expediente).")

        # ==========================================
        # 🏆 PRODUTIVIDADE POR TURNO (DIÁRIA)
        # ==========================================
        st.markdown("---")
        st.subheader(f"🏆 Produtividade por Turno no Dia ({data_selecionada.strftime('%d/%m/%Y')})")
        
        colA, colB, colC = st.columns(3)
        
        df_turno_a = df_dia[df_dia['Turno'] == 'Turno A']
        vol_a = len(df_turno_a)
        tai_a = df_turno_a['TAI (Minutos)'].mean() if vol_a > 0 else 0
        ocup_a = (df_turno_a['TAI (Minutos)'].sum() / min_disp_dia_a) * 100 if min_disp_dia_a > 0 else 0
        conf_a = (df_turno_a['Dentro_da_Meta'].sum() / vol_a) * 100 if vol_a > 0 else 0
        with colA:
            exibir_card_turno("Turno A", "☀️", vol_a, formatar_tempo(tai_a), ocup_a, conf_a, CORES_TURNOS["Turno A"])
            
        df_turno_b = df_dia[df_dia['Turno'] == 'Turno B']
        vol_b = len(df_turno_b)
        tai_b = df_turno_b['TAI (Minutos)'].mean() if vol_b > 0 else 0
        ocup_b = (df_turno_b['TAI (Minutos)'].sum() / min_disp_dia_b) * 100 if min_disp_dia_b > 0 else 0
        conf_b = (df_turno_b['Dentro_da_Meta'].sum() / vol_b) * 100 if vol_b > 0 else 0
        with colB:
            exibir_card_turno("Turno B", "🌙", vol_b, formatar_tempo(tai_b), ocup_b, conf_b, CORES_TURNOS["Turno B"])

        df_turno_c = df_dia[df_dia['Turno'] == 'Turno C']
        vol_c = len(df_turno_c)
        tai_c = df_turno_c['TAI (Minutos)'].mean() if vol_c > 0 else 0
        ocup_c = (df_turno_c['TAI (Minutos)'].sum() / min_disp_dia_c) * 100 if min_disp_dia_c > 0 else 0
        conf_c = (df_turno_c['Dentro_da_Meta'].sum() / vol_c) * 100 if vol_c > 0 else 0
        with colC:
            exibir_card_turno("Turno C", "🦉", vol_c, formatar_tempo(tai_c), ocup_c, conf_c, CORES_TURNOS["Turno C"])
            
        st.write("")
        vencedor_dia, motivo_dia = calcular_turno_destaque(df_dia, min_disp_dia_a, min_disp_dia_b, min_disp_dia_c)
        if vencedor_dia and vencedor_dia != "Sem dados":
            st.success(f"🥇 **Turno de Destaque de Hoje:** {vencedor_dia} — *{motivo_dia}*")

        df_comp = pd.DataFrame({"Turno": ["Turno A", "Turno B", "Turno C"], "Ocupação (%)": [ocup_a, ocup_b, ocup_c]})
        fig_comp = px.bar(df_comp, x="Ocupação (%)", y="Turno", orientation='h', text=df_comp["Ocupação (%)"].apply(lambda x: f"<b>{x:.1f}%</b>"), color="Turno", color_discrete_map=CORES_TURNOS)
        fig_comp.update_traces(textposition='auto', textfont_size=16, textfont_color='black')
        fig_comp.update_layout(height=200, showlegend=False, xaxis_title="Taxa de Ocupação da Equipe (%)", yaxis_title="", margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_comp, use_container_width=True)

        st.write("")
        
        # --- TABELA HISTÓRICO DO DIA ---
        st.markdown("**📋 Histórico de Atendimentos do Dia**")
        df_historico = df_dia.sort_values(by='Saída', ascending=False).copy()
        df_historico['TAI_Formatado_Limpo'] = df_historico['TAI_Formatado'].str.replace('<b>', '').str.replace('</b>', '')
        
        if col_motorista and col_motorista in df_historico.columns:
            df_exibicao = df_historico[[col_placa, col_motorista, col_operacao, 'Turno', 'Entrada_Texto', 'Saída_Texto', 'TAI_Formatado_Limpo']]
            df_exibicao.columns = ['Placa', 'Motorista', 'Operação', 'Turno Final', 'Hora Entrada', 'Hora Saída', 'Tempo Total (TAI)']
        else:
            df_exibicao = df_historico[[col_placa, col_operacao, 'Turno', 'Entrada_Texto', 'Saída_Texto', 'TAI_Formatado_Limpo']]
            df_exibicao.columns = ['Placa', 'Operação', 'Turno Final', 'Hora Entrada', 'Hora Saída', 'Tempo Total (TAI)']
            
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma carreta finalizada no dia selecionado.")
else:
    st.info("Nenhum dado encontrado na base.")