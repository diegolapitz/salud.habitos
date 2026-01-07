import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.graph_objects as go

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Journey 2026", page_icon="✨", layout="wide")

# ═══════════════════════════════════════════════════════════════════════════
# ESTILOS CSS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif !important; }
    
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    
    h1, h2, h3 { color: #1a202c !important; }
    
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        border: none !important;
    }
    
    .level-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(245,87,108,0.3);
    }
    
    .xp-bar {
        background: #e2e8f0;
        height: 25px;
        border-radius: 15px;
        overflow: hidden;
        position: relative;
        margin: 1rem 0;
    }
    
    .xp-fill {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 100%;
        transition: width 0.5s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .achievement {
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-weight: 600;
    }
    
    .streak-badge {
        background: #fee2e2;
        color: #dc2626;
        padding: 0.25rem 0.6rem;
        border-radius: 15px;
        font-weight: 700;
        font-size: 0.8rem;
        margin-left: 0.5rem;
    }
    
    div.stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        width: 100%;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4);
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102,126,234,0.5);
    }
    
    .meal-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    
    .meal-table th {
        background: #667eea;
        color: white;
        padding: 0.8rem;
        text-align: center;
        font-weight: 600;
    }
    
    .meal-table td {
        border: 1px solid #e2e8f0;
        padding: 0.5rem;
        text-align: center;
        font-size: 0.9rem;
    }
    
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1.5px solid #e2e8f0 !important;
    }
    
    .stCheckbox > label {
        font-size: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# BASE DE DATOS
# ═══════════════════════════════════════════════════════════════════════════
DB = "journey_v2.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY, fecha TEXT, usuario TEXT, 
                  peso REAL, sueno REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS habitos 
                 (id INTEGER PRIMARY KEY, fecha TEXT, usuario TEXT, 
                  habito TEXT, cumplido INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS comidas 
                 (id INTEGER PRIMARY KEY, fecha TEXT, usuario TEXT, 
                  momento TEXT, detalle TEXT, calidad INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, 
                  nivel INTEGER DEFAULT 1, xp INTEGER DEFAULT 0,
                  peso_objetivo REAL DEFAULT 0, fecha_objetivo TEXT DEFAULT '')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS habitos_config 
                 (id INTEGER PRIMARY KEY, usuario TEXT, habito TEXT, emoji TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS meal_prep 
                 (id INTEGER PRIMARY KEY, usuario TEXT, dia TEXT, 
                  momento TEXT, comida TEXT)''')
    
    # Crear usuarios si no existen
    c.execute("INSERT OR IGNORE INTO usuarios (nombre) VALUES ('Diego')")
    c.execute("INSERT OR IGNORE INTO usuarios (nombre) VALUES ('Manu')")
    
    # Hábitos por defecto si no existen
    c.execute("SELECT COUNT(*) FROM habitos_config WHERE usuario = 'Diego'")
    if c.fetchone()[0] == 0:
        habitos_default = [
            ("Entrenar", "🏋️"),
            ("Agua 2L", "💧"),
            ("Comer Bien", "🥗"),
            ("Dormir Bien", "💤"),
            ("Leer", "📖")
        ]
        for hab, emoji in habitos_default:
            c.execute("INSERT INTO habitos_config (usuario, habito, emoji) VALUES (?, ?, ?)",
                     ('Diego', hab, emoji))
            c.execute("INSERT INTO habitos_config (usuario, habito, emoji) VALUES (?, ?, ?)",
                     ('Manu', hab, emoji))
    
    conn.commit()
    conn.close()

def get_data(query, params=()):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def guardar_dia(fecha, usuario, peso, sueno, habitos, comidas):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Registro básico
    c.execute("DELETE FROM registros WHERE fecha = ? AND usuario = ?", (fecha, usuario))
    c.execute("INSERT INTO registros (fecha, usuario, peso, sueno) VALUES (?, ?, ?, ?)",
              (fecha, usuario, peso, sueno))
    
    # Hábitos
    c.execute("DELETE FROM habitos WHERE fecha = ? AND usuario = ?", (fecha, usuario))
    for hab, val in habitos.items():
        c.execute("INSERT INTO habitos (fecha, usuario, habito, cumplido) VALUES (?, ?, ?, ?)",
                  (fecha, usuario, hab, 1 if val else 0))
    
    # Comidas
    c.execute("DELETE FROM comidas WHERE fecha = ? AND usuario = ?", (fecha, usuario))
    for momento, detalle, calidad in comidas:
        if detalle.strip():  # Solo guardar si hay algo
            c.execute("INSERT INTO comidas (fecha, usuario, momento, detalle, calidad) VALUES (?, ?, ?, ?, ?)",
                     (fecha, usuario, momento, detalle, calidad))
    
    # Calcular XP ganado
    xp_ganado = sum([10 if v else 0 for v in habitos.values()])
    if peso > 0:
        xp_ganado += 5
    if sueno > 0:
        xp_ganado += 5
    if len(comidas) > 0:
        xp_ganado += 5
    
    # Actualizar XP y nivel
    c.execute("SELECT xp, nivel FROM usuarios WHERE nombre = ?", (usuario,))
    row = c.fetchone()
    xp_actual, nivel_actual = row[0], row[1]
    
    nuevo_xp = xp_actual + xp_ganado
    nuevo_nivel = nivel_actual
    
    while nuevo_xp >= 100:
        nuevo_xp -= 100
        nuevo_nivel += 1
    
    c.execute("UPDATE usuarios SET xp = ?, nivel = ? WHERE nombre = ?", 
              (nuevo_xp, nuevo_nivel, usuario))
    
    conn.commit()
    conn.close()
    
    return xp_ganado, nuevo_nivel

def calcular_racha(usuario, habito):
    df = get_data("""SELECT fecha, cumplido FROM habitos 
                     WHERE usuario = ? AND habito = ? 
                     ORDER BY fecha DESC""", (usuario, habito))
    if df.empty:
        return 0, 0
    
    racha_actual = 0
    racha_maxima = 0
    temp_racha = 0
    
    for _, row in df.iterrows():
        if row['cumplido'] == 1:
            temp_racha += 1
            if racha_actual == 0:
                racha_actual = temp_racha
        else:
            if temp_racha > racha_maxima:
                racha_maxima = temp_racha
            temp_racha = 0
    
    if temp_racha > racha_maxima:
        racha_maxima = temp_racha
    
    return racha_actual, racha_maxima

def obtener_achievements(usuario):
    df_reg = get_data("SELECT * FROM registros WHERE usuario = ?", (usuario,))
    df_hab = get_data("SELECT * FROM habitos WHERE usuario = ? AND cumplido = 1", (usuario,))
    
    achievements = []
    
    if len(df_reg) >= 7:
        achievements.append("🏆 Primera Semana")
    if len(df_reg) >= 30:
        achievements.append("🎯 30 Días Registrando")
    if len(df_reg) >= 100:
        achievements.append("👑 100 Días de Journey")
    
    if not df_hab.empty:
        dias_unicos = df_hab['fecha'].nunique()
        if dias_unicos >= 7:
            achievements.append("🔥 Racha de Fuego (7 días)")
    
    return achievements

def check_in_status(usuario, fecha):
    df = get_data("SELECT * FROM registros WHERE usuario = ? AND fecha = ?", (usuario, fecha))
    return not df.empty

# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════
init_db()

# ═══════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-header">
    <h1 style="margin:0; color: white !important;">✨ Journey 2026</h1>
    <p style="margin:0.5rem 0 0 0; color: rgba(255,255,255,0.9) !important;">
        Tu transformación comienza aquí
    </p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SELECTOR USUARIO Y FECHA
# ═══════════════════════════════════════════════════════════════════════════
col1, col2, col3 = st.columns([2, 2, 3])

with col1:
    usuario = st.selectbox("👤 Usuario", ["Diego", "Manu"])

with col2:
    fecha = st.date_input("📅 Fecha", datetime.now())
    fecha_str = str(fecha)

with col3:
    df_user = get_data("SELECT nivel, xp FROM usuarios WHERE nombre = ?", (usuario,))
    nivel = df_user.iloc[0]['nivel']
    xp = df_user.iloc[0]['xp']
    
    st.markdown(f'<span class="level-badge">Nivel {nivel}</span>', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="xp-bar">
        <div class="xp-fill" style="width: {xp}%">
            {xp}/100 XP
        </div>
    </div>
    ''', unsafe_allow_html=True)

check_in = check_in_status(usuario, fecha_str)
status_icon = "✅" if check_in else "⏳"
status_text = "Día registrado" if check_in else "Pendiente de registro"
st.markdown(f"### {status_icon} {status_text}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Registro", "📊 Progreso", "🍽️ Menú semanal", "🏆 Logros", "⚙️ Configuración del usuario"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: REGISTRO DIARIO
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    df_dia = get_data("SELECT * FROM registros WHERE fecha = ? AND usuario = ?", 
                      (fecha_str, usuario))
    df_hab = get_data("SELECT habito FROM habitos WHERE fecha = ? AND usuario = ? AND cumplido = 1",
                      (fecha_str, usuario))
    df_comidas = get_data("SELECT * FROM comidas WHERE fecha = ? AND usuario = ?",
                          (fecha_str, usuario))
    
    peso_def = df_dia.iloc[0]['peso'] if not df_dia.empty else 0.0
    sueno_def = df_dia.iloc[0]['sueno'] if not df_dia.empty else 0.0
    habs_cumplidos = set(df_hab['habito'].tolist())
    
    with st.form("form_registro"):
        col_izq, col_der = st.columns([1, 1])
        
        # ═══════════════════════════════════════════════════════════════════
        # COLUMNA IZQUIERDA: PESO Y SUEÑO
        # ═══════════════════════════════════════════════════════════════════
        with col_izq:
            st.subheader("⚖️ Peso")
            peso = st.number_input("Peso (kg)", 0.0, 300.0, float(peso_def), 0.1)
            
            st.subheader("😴 Sueño")
            sueno = st.number_input("Horas dormidas", 0.0, 24.0, float(sueno_def), 0.5)
        
        # ═══════════════════════════════════════════════════════════════════
        # COLUMNA DERECHA: HÁBITOS
        # ═══════════════════════════════════════════════════════════════════
        with col_der:
            st.subheader("🎯 Hábitos")
            
            # Cargar hábitos personalizados del usuario
            df_habs_config = get_data("SELECT habito, emoji FROM habitos_config WHERE usuario = ?", (usuario,))
            
            habitos_vals = {}
            for _, row in df_habs_config.iterrows():
                habito = row['habito']
                emoji = row['emoji']
                
                racha_act, racha_max = calcular_racha(usuario, habito)
                
                col_check, col_racha = st.columns([3, 1])
                
                with col_check:
                    habitos_vals[habito] = st.checkbox(
                        f"{emoji} {habito}",
                        value=habito in habs_cumplidos,
                        key=f"hab_{habito}"
                    )
                
                with col_racha:
                    if racha_act > 0:
                        st.markdown(f'<span class="streak-badge">🔥 {racha_act}</span>', 
                                   unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ═══════════════════════════════════════════════════════════════════
        # REGISTRO DE COMIDAS
        # ═══════════════════════════════════════════════════════════════════
        st.subheader("🍽️ Comidas del Día")
        
        momentos = ["Desayuno", "Almuerzo", "Merienda", "Cena", "Extra"]
        comidas_data = []
        
        for momento in momentos:
            st.markdown(f"**{momento}**")
            
            # Buscar si existe
            comida_row = df_comidas[df_comidas['momento'] == momento]
            detalle_def = comida_row.iloc[0]['detalle'] if not comida_row.empty else ""
            calidad_def = int(comida_row.iloc[0]['calidad']) if not comida_row.empty else 100
            
            col_detalle, col_calidad = st.columns([3, 1])
            
            with col_detalle:
                detalle = st.text_input(
                    f"Detalle {momento}",
                    value=detalle_def,
                    placeholder=f"¿Qué comiste?",
                    label_visibility="collapsed",
                    key=f"comida_{momento}"
                )
            
            with col_calidad:
                calidad = st.selectbox(
                    f"Calidad {momento}",
                    [0, 25, 50, 75, 100],
                    index=[0, 25, 50, 75, 100].index(calidad_def),
                    format_func=lambda x: f"{x}%",
                    label_visibility="collapsed",
                    key=f"cal_{momento}"
                )
            
            comidas_data.append((momento, detalle, calidad))
        
        st.markdown("---")
        
        # ═══════════════════════════════════════════════════════════════════
        # BOTÓN GUARDAR
        # ═══════════════════════════════════════════════════════════════════
        submitted = st.form_submit_button("💾 Guardar y Ganar XP", use_container_width=True)
        
        if submitted:
            xp_ganado, nivel_nuevo = guardar_dia(fecha_str, usuario, peso, sueno, habitos_vals, comidas_data)
            
            st.success(f"✅ ¡Día guardado! Ganaste **{xp_ganado} XP**")
            
            if nivel_nuevo > nivel:
                st.balloons()
                st.success(f"🎉 ¡SUBISTE DE NIVEL! Ahora eres **Nivel {nivel_nuevo}**")
            
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: PROGRESO
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    df_hist = get_data("SELECT fecha, peso, sueno FROM registros WHERE usuario = ? ORDER BY fecha",
                       (usuario,))
    
    if df_hist.empty:
        st.info("📊 Aún no hay registros para mostrar")
    else:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        peso_actual = df_hist.iloc[-1]['peso']
        peso_inicial = df_hist.iloc[0]['peso']
        diff_peso = peso_actual - peso_inicial
        
        with col_m1:
            st.metric("Peso Actual", f"{peso_actual:.1f} kg", f"{diff_peso:+.1f} kg")
        
        with col_m2:
            sueno_prom = df_hist['sueno'].mean()
            st.metric("Sueño Promedio", f"{sueno_prom:.1f}h")
        
        with col_m3:
            st.metric("Días Registrados", len(df_hist))
        
        with col_m4:
            # Mostrar objetivo si existe
            df_obj = get_data("SELECT peso_objetivo, fecha_objetivo FROM usuarios WHERE nombre = ?", (usuario,))
            if df_obj.iloc[0]['peso_objetivo'] > 0:
                peso_obj = df_obj.iloc[0]['peso_objetivo']
                diff_objetivo = peso_actual - peso_obj
                st.metric("Objetivo", f"{peso_obj:.1f} kg", f"{diff_objetivo:+.1f} kg")
        
        st.markdown("---")
        
        # Gráfico de peso
        st.subheader("📉 Evolución de Peso")
        fig_peso = go.Figure()
        fig_peso.add_trace(go.Scatter(
            x=df_hist['fecha'], y=df_hist['peso'],
            mode='lines+markers',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8),
            name='Peso'
        ))
        
        # Línea de objetivo si existe
        if df_obj.iloc[0]['peso_objetivo'] > 0:
            peso_obj = df_obj.iloc[0]['peso_objetivo']
            fig_peso.add_hline(y=peso_obj, line_dash="dash", line_color="red", 
                              annotation_text="Objetivo")
        
        fig_peso.update_laDiegout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="", yaxis_title="Peso (kg)",
            plot_bgcolor='white',
            showlegend=False
        )
        st.plotly_chart(fig_peso, use_container_width=True)
        
        # Gráfico de sueño
        st.subheader("😴 Evolución de Sueño")
        fig_sueno = go.Figure()
        fig_sueno.add_trace(go.Scatter(
            x=df_hist['fecha'], y=df_hist['sueno'],
            mode='lines+markers',
            line=dict(color='#764ba2', width=3),
            marker=dict(size=8),
            fill='tozeroy'
        ))
        fig_sueno.update_laDiegout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="", yaxis_title="Horas",
            plot_bgcolor='white'
        )
        st.plotly_chart(fig_sueno, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: MEAL PREP
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🗓️ Planificación Semanal de Comidas")
    
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    momentos = ["Desayuno", "Almuerzo", "Merienda", "Cena"]
    
    df_meal = get_data("SELECT * FROM meal_prep WHERE usuario = ?", (usuario,))
    
    with st.form("form_meal_prep"):
        st.caption("Ingresa tus comidas planificadas para la semana")
        
        meal_data = {}
        
        for momento in momentos:
            st.markdown(f"### 🍽️ {momento}")
            cols = st.columns(7)
            
            for i, dia in enumerate(dias):
                with cols[i]:
                    existing = df_meal[(df_meal['dia'] == dia) & (df_meal['momento'] == momento)]
                    default_val = existing.iloc[0]['comida'] if not existing.empty else ""
                    
                    comida = st.text_input(
                        dia, 
                        value=default_val,
                        placeholder="Ej: Tostadas con huevo revuelto",
                        label_visibility="visible",
                        key=f"meal_{momento}_{dia}"
                    )
                    meal_data[f"{dia}_{momento}"] = comida
        
        submitted_meal = st.form_submit_button("💾 Guardar Menú", use_container_width=True)
        
        if submitted_meal:
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            
            c.execute("DELETE FROM meal_prep WHERE usuario = ?", (usuario,))
            
            for key, val in meal_data.items():
                if val.strip():
                    dia, momento = key.rsplit("_", 1)
                    c.execute("INSERT INTO meal_prep (usuario, dia, momento, comida) VALUES (?, ?, ?, ?)",
                              (usuario, dia, momento, val))
            
            conn.commit()
            conn.close()
            
            st.success("✅ Meal Prep guardado exitosamente")
            st.rerun()
    
    if not df_meal.empty:
        st.markdown("---")
        st.subheader("📋 Tu Meal Prep")
        
        html_table = '<table class="meal-table"><thead><tr><th>Comida</th>'
        for dia in dias:
            html_table += f'<th>{dia}</th>'
        html_table += '</tr></thead><tbody>'
        
        for momento in momentos:
            html_table += f'<tr><td><strong>{momento}</strong></td>'
            for dia in dias:
                comida_row = df_meal[(df_meal['dia'] == dia) & (df_meal['momento'] == momento)]
                comida_text = comida_row.iloc[0]['comida'] if not comida_row.empty else "-"
                html_table += f'<td>{comida_text}</td>'
            html_table += '</tr>'
        
        html_table += '</tbody></table>'
        st.markdown(html_table, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: LOGROS
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    achievements = obtener_achievements(usuario)
    
    st.subheader("🏆 Tus Logros Desbloqueados")
    
    if achievements:
        for ach in achievements:
            st.markdown(f'<div class="achievement">{ach}</div>', unsafe_allow_html=True)
    else:
        st.info("Aún no has desbloqueado logros. ¡Sigue registrando!")
    
    st.markdown("---")
    st.subheader("🔥 Rachas Actuales")
    
    df_habs_user = get_data("SELECT habito FROM habitos_config WHERE usuario = ?", (usuario,))
    habitos_list = df_habs_user['habito'].tolist()
    
    if habitos_list:
        cols = st.columns(len(habitos_list))
        for i, hab in enumerate(habitos_list):
            racha_act, racha_max = calcular_racha(usuario, hab)
            with cols[i]:
                st.metric(hab, f"🔥 {racha_act}", f"Máx: {racha_max}")
    
    st.markdown("---")
    st.subheader("📊 Comparación de Usuarios")
    
    col_comp1, col_comp2 = st.columns(2)
    
    for idx, usr in enumerate(["Diego", "Manu"]):
        df_usr = get_data("SELECT nivel, xp FROM usuarios WHERE nombre = ?", (usr,))
        nivel_usr = df_usr.iloc[0]['nivel']
        xp_usr = df_usr.iloc[0]['xp']
        
        df_reg_usr = get_data("SELECT COUNT(*) as total FROM registros WHERE usuario = ?", (usr,))
        total_dias = df_reg_usr.iloc[0]['total']
        
        with col_comp1 if idx == 0 else col_comp2:
            st.markdown(f"### {'👤' if idx == 0 else '👥'} {usr}")
            st.metric("Nivel", nivel_usr)
            st.metric("XP", f"{xp_usr}/100")
            st.metric("Días Totales", total_dias)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5: CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("⚙️ Configuración Personal")
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: OBJETIVOS
    # ═══════════════════════════════════════════════════════════════════════
    with st.container(border=True):
        st.markdown("### 🎯 Objetivos")
        
        df_obj = get_data("SELECT peso_objetivo, fecha_objetivo FROM usuarios WHERE nombre = ?", (usuario,))
        peso_obj_actual = df_obj.iloc[0]['peso_objetivo'] if df_obj.iloc[0]['peso_objetivo'] else 0.0
        fecha_obj_actual = df_obj.iloc[0]['fecha_objetivo'] if df_obj.iloc[0]['fecha_objetivo'] else ""
        
        col_obj1, col_obj2 = st.columns(2)
        
        with col_obj1:
            peso_objetivo = st.number_input(
                "Peso Objetivo (kg)",
                min_value=0.0,
                max_value=300.0,
                value=float(peso_obj_actual),
                step=0.1,
                help="¿A qué peso querés llegar?"
            )
        
        with col_obj2:
            if fecha_obj_actual:
                fecha_obj = datetime.strptime(fecha_obj_actual, '%Y-%m-%d').date()
            else:
                fecha_obj = datetime.now().date()
            
            fecha_objetivo = st.date_input(
                "Fecha Objetivo",
                value=fecha_obj,
                help="¿Para cuándo querés llegar?"
            )
        
        if st.button("💾 Guardar Objetivos"):
            execute_query(
                "UPDATE usuarios SET peso_objetivo = ?, fecha_objetivo = ? WHERE nombre = ?",
                (peso_objetivo, str(fecha_objetivo), usuario)
            )
            st.success("✅ Objetivos guardados")
            st.rerun()
    
    st.write("")
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: HÁBITOS PERSONALIZADOS
    # ═══════════════════════════════════════════════════════════════════════
    with st.container(border=True):
        st.markdown("### 🎯 Tus Hábitos")
        st.caption("Personaliza los hábitos que querés trackear")
        
        df_habs = get_data("SELECT id, habito, emoji FROM habitos_config WHERE usuario = ? ORDER BY id", (usuario,))
        
        # Mostrar hábitos existentes
        if not df_habs.empty:
            st.markdown("**Hábitos actuales:**")
            for _, row in df_habs.iterrows():
                col_h1, col_h2, col_h3 = st.columns([1, 3, 1])
                with col_h1:
                    st.text(row['emoji'])
                with col_h2:
                    st.text(row['habito'])
                with col_h3:
                    if st.button("🗑️", key=f"del_{row['id']}"):
                        execute_query("DELETE FROM habitos_config WHERE id = ?", (row['id'],))
                        st.rerun()
        
        st.markdown("---")
        st.markdown("**Agregar nuevo hábito:**")
        
        col_new1, col_new2, col_new3 = st.columns([1, 3, 1])
        
        with col_new1:
            emoji_nuevo = st.text_input("Emoji", value="✨", max_chars=2, key="emoji_input")
        
        with col_new2:
            habito_nuevo = st.text_input("Nombre del hábito", placeholder="Ej: Meditar 10 min", key="habito_input")
        
        with col_new3:
            if st.button("➕ Agregar"):
                if habito_nuevo.strip():
                    execute_query(
                        "INSERT INTO habitos_config (usuario, habito, emoji) VALUES (?, ?, ?)",
                        (usuario, habito_nuevo, emoji_nuevo)
                    )
                    st.success(f"✅ Hábito '{habito_nuevo}' agregado")
                    st.rerun()
                else:
                    st.error("Ingresa un nombre para el hábito")
    
    st.write("")
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: MEAL PREP PERSONALIZADO
    # ═══════════════════════════════════════════════════════════════════════
    with st.container(border=True):
        st.markdown("### 🍽️ Configurar Meal Prep")
        st.caption("Define tus comidas base para la semana (puedes editarlas en la pestaña Meal Prep)")
        
        st.info("💡 **Tip:** Ve a la pestaña 'Meal Prep' para planificar toda tu semana de comidas")
        
        # Estadísticas de meal prep
        df_meal_stats = get_data("SELECT COUNT(*) as total FROM meal_prep WHERE usuario = ?", (usuario,))
        total_comidas = df_meal_stats.iloc[0]['total']
        
        st.metric("Comidas planificadas", f"{total_comidas}/28")
        
        if total_comidas > 0:
            if st.button("🗑️ Limpiar todo el Meal Prep"):
                execute_query("DELETE FROM meal_prep WHERE usuario = ?", (usuario,))
                st.success("✅ Meal Prep limpiado")
                st.rerun()
    
    st.write("")
    
    # ═══════════════════════════════════════════════════════════════════════
    # SECCIÓN 4: ESTADÍSTICAS GENERALES
    # ═══════════════════════════════════════════════════════════════════════
    with st.container(border=True):
        st.markdown("### 📊 Tus Estadísticas")
        
        df_stats_reg = get_data("SELECT COUNT(*) as total FROM registros WHERE usuario = ?", (usuario,))
        df_stats_hab = get_data("SELECT COUNT(*) as total FROM habitos WHERE usuario = ? AND cumplido = 1", (usuario,))
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("Días registrados", df_stats_reg.iloc[0]['total'])
        
        with col_stat2:
            st.metric("Hábitos cumplidos", df_stats_hab.iloc[0]['total'])
        
        with col_stat3:
            if df_stats_reg.iloc[0]['total'] > 0:
                promedio = df_stats_hab.iloc[0]['total'] / df_stats_reg.iloc[0]['total']
                st.metric("Promedio hábitos/día", f"{promedio:.1f}")
            else:

                st.metric("Promedio hábitos/día", "0.0")

