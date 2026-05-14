# main.py — Aplicación Streamlit: Optimización de impresora 3D con AG

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st
from config import (
    AG_DEFAULTS,
    BENCHMARK,
    GENE_INFO,
    MATERIAL_RANGES,
    PROFILES,
    RELLENO_MAXIMO,
)
from fitness import desglose_fitness
from genetic import ejecutar_ag
from logger import Logger, leer_log, listar_logs

# ─── Configuración de página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="PrintGenius 3D — AG",
    page_icon="🖨️",
    layout="wide",
)

# ─── Estilos ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    /* Fondo general */
    .stApp { background-color: #0f1117; color: #e0e0e0; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a1d27;
        border-right: 1px solid #2d3148;
    }

    /* Tarjetas de resultado */
    .card {
        background: #1e2130;
        border: 1px solid #2d3148;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 14px;
    }
    .card-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #7b8ab8;
        margin-bottom: 6px;
    }
    .card-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #a78bfa;
    }
    .card-unit {
        font-size: 0.9rem;
        color: #7b8ab8;
        margin-left: 4px;
    }

    /* Badges de material */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .badge-pla  { background:#1a3a2a; color:#4ade80; border:1px solid #4ade80; }
    .badge-abs  { background:#3a1a1a; color:#f87171; border:1px solid #f87171; }
    .badge-petg { background:#1a2a3a; color:#60a5fa; border:1px solid #60a5fa; }

    /* Tabla comparación */
    .comp-table { width:100%; border-collapse:collapse; }
    .comp-table th {
        background:#2d3148;
        color:#a78bfa;
        padding: 8px 12px;
        text-align:left;
        font-size:0.8rem;
        letter-spacing:0.08em;
        text-transform:uppercase;
    }
    .comp-table td {
        padding: 7px 12px;
        border-bottom: 1px solid #2d3148;
        font-size: 0.92rem;
    }
    .comp-table tr:hover td { background: #252840; }
    .diff-pos { color: #4ade80; }
    .diff-neg { color: #f87171; }
    .diff-neu { color: #94a3b8; }

    /* Título principal */
    h1 { color: #a78bfa !important; letter-spacing: -0.02em; }
    h2 { color: #c4b5fd !important; }
    h3 { color: #ddd6fe !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🖨️ Configuración")
    st.markdown("---")

    material = st.selectbox("Material", ["PLA", "ABS", "PETG"])
    perfil = st.selectbox(
        "Perfil de impresión",
        ["Balanceado", "Estético", "Funcional", "Rápido", "Personalizado"],
    )

    if perfil == "Personalizado":
        st.markdown("#### 🛠️ Configuración Perfil")
        rel_max = st.slider("Relleno Máximo (%)", 10, 100, 40)
        w_cal = st.slider("Peso Calidad", 0.0, 1.0, 0.25, 0.05)
        w_res = st.slider("Peso Resistencia", 0.0, 1.0, 0.25, 0.05)
        w_vel = st.slider("Peso Velocidad", 0.0, 1.0, 0.25, 0.05)
        w_aho = st.slider("Peso Ahorro", 0.0, 1.0, 0.25, 0.05)

        total_w = w_cal + w_res + w_vel + w_aho
        if total_w > 0:
            PROFILES["Personalizado"] = {
                "calidad": w_cal / total_w,
                "resistencia": w_res / total_w,
                "velocidad": w_vel / total_w,
                "ahorro": w_aho / total_w,
            }
        RELLENO_MAXIMO["Personalizado"] = rel_max

    st.markdown("---")
    st.markdown("#### ⚙️ Parámetros del AG")

    tam_poblacion = st.slider(
        "Tamaño de población",
        min_value=20,
        max_value=400,
        value=AG_DEFAULTS["poblacion"],
        step=10,
    )
    n_generaciones = st.slider(
        "Generaciones",
        min_value=50,
        max_value=1000,
        value=AG_DEFAULTS["generaciones"],
        step=50,
    )

    with st.expander("🛠️ Avanzado"):
        tasa_cruce = st.slider(
            "Tasa de cruce", 0.0, 1.0, AG_DEFAULTS["tasa_cruce"], 0.05
        )
        tasa_mutacion = st.slider(
            "Tasa de mutación", 0.0, 1.0, AG_DEFAULTS["tasa_mutacion"], 0.01
        )
        k_torneo = st.slider("Toner (K-torneo)", 2, 10, AG_DEFAULTS["k_torneo"], 1)

    st.markdown("---")
    ejecutar = st.button("🚀 Optimizar", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("#### 📋 Historial de logs")
    logs_disponibles = listar_logs()
    if logs_disponibles:
        log_seleccionado = st.selectbox("Ver log", logs_disponibles)
        ver_log = st.button("Ver log", use_container_width=True)
    else:
        st.caption("Sin ejecuciones previas.")
        ver_log = False


# ─── Encabezado ──────────────────────────────────────────────────────────────
st.markdown("# 🖨️ PrintGenius 3D")
st.markdown(
    "Optimización de parámetros de impresión 3D mediante **Algoritmo Genético**."
)

badge_class = {"PLA": "badge-pla", "ABS": "badge-abs", "PETG": "badge-petg"}[material]
st.markdown(
    f'Material seleccionado: <span class="badge {badge_class}">{material}</span> &nbsp;'
    f'Perfil: <span class="badge" style="background:#2d3148;color:#c4b5fd;'
    f'border:1px solid #a78bfa;">{perfil}</span>',
    unsafe_allow_html=True,
)
st.markdown("")


# ─── Ver log histórico ───────────────────────────────────────────────────────
if ver_log and logs_disponibles:
    st.markdown("---")
    st.markdown(f"### 📄 {log_seleccionado}")
    contenido = leer_log(log_seleccionado)
    st.code(contenido, language="text")
    st.stop()


# ─── Ejecución del AG ────────────────────────────────────────────────────────
if ejecutar:
    config_ag = {
        "poblacion": tam_poblacion,
        "generaciones": n_generaciones,
        "tasa_cruce": tasa_cruce,
        "tasa_mutacion": tasa_mutacion,
        "k_torneo": k_torneo,
        "sigma_mutacion": AG_DEFAULTS["sigma_mutacion"],
        "n_elites": AG_DEFAULTS["n_elites"],
    }

    logger = Logger()
    logger.inicio(material, perfil, config_ag)

    # Barra de progreso
    progreso_bar = st.progress(0, text="Iniciando algoritmo genético…")
    estado_texto = st.empty()

    historial_fitness = []
    historial_avg = []

    def on_generacion(gen, mejor_fitness, avg_fitness):
        logger.generacion(gen, mejor_fitness, avg_fitness)
        pct = int(gen / n_generaciones * 100)
        progreso_bar.progress(
            pct,
            text=f"Generación {gen}/{n_generaciones} — Mejor fitness: {mejor_fitness:.4f}",
        )

    # Ejecutar AG
    resultado = ejecutar_ag(
        material=material,
        perfil=perfil,
        config=config_ag,
        callback_generacion=on_generacion,
    )

    progreso_bar.progress(100, text="✅ Optimización completa")
    estado_texto.empty()

    mejor = resultado["mejor"]
    fitness_f = resultado["fitness_final"]
    hist = resultado["historial"]
    hist_avg = resultado["historial_avg"]
    desglose = desglose_fitness(mejor, material, perfil)

    logger.resultado(mejor, fitness_f, desglose)
    logger.cerrar()

    st.success(f"Optimización completada · Log guardado: `{logger.nombre_archivo}`")
    st.markdown("---")

    # ── Sección 1: métricas rápidas ─────────────────────────────────────────
    st.markdown("## 📊 Resultado óptimo")

    cols = st.columns(4)
    metricas = [
        ("Fitness final", f"{fitness_f:.4f}", ""),
        ("Calidad", f"{desglose['Calidad']:.4f}", ""),
        ("Resistencia", f"{desglose['Resistencia']:.4f}", ""),
        ("Velocidad", f"{desglose['Velocidad']:.4f}", ""),
    ]
    for col, (titulo, valor, unidad) in zip(cols, metricas):
        col.markdown(
            f'<div class="card">'
            f'<div class="card-title">{titulo}</div>'
            f'<div class="card-value">{valor}<span class="card-unit">{unidad}</span></div>'
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Sección 2: parámetros detallados ────────────────────────────────────
    st.markdown("### 🔧 Parámetros de configuración")

    rangos = MATERIAL_RANGES[material]
    cols_p = st.columns(len(GENE_INFO))

    for col, gen in zip(cols_p, GENE_INFO):
        key = gen["key"]
        val = mejor[key]
        lo, hi = rangos[key]
        dec = gen["decimals"]
        fmt = f"{{:.{dec}f}}" if dec > 0 else "{:.0f}"
        col.markdown(
            f'<div class="card">'
            f'<div class="card-title">{gen["label"]}</div>'
            f'<div class="card-value">{fmt.format(val)}'
            f'<span class="card-unit">{gen["unit"]}</span></div>'
            f'<div style="font-size:0.72rem;color:#7b8ab8;margin-top:4px;">'
            f"Rango: {fmt.format(lo)} – {fmt.format(hi)}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Sección 3: gráfica de convergencia ──────────────────────────────────
    st.markdown("### 📈 Convergencia del AG")

    fig, ax = plt.subplots(figsize=(10, 3.5))
    fig.patch.set_facecolor("#1e2130")
    ax.set_facecolor("#1e2130")

    generaciones_eje = list(range(1, len(hist) + 1))
    ax.plot(generaciones_eje, hist, color="#a78bfa", lw=2, label="Mejor fitness")
    ax.plot(
        generaciones_eje,
        hist_avg,
        color="#60a5fa",
        lw=1.2,
        linestyle="--",
        alpha=0.7,
        label="Fitness promedio",
    )

    ax.set_xlabel("Generación", color="#7b8ab8", fontsize=10)
    ax.set_ylabel("Fitness", color="#7b8ab8", fontsize=10)
    ax.tick_params(colors="#7b8ab8")
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3148")
    ax.legend(
        facecolor="#252840", edgecolor="#2d3148", labelcolor="#e0e0e0", fontsize=9
    )
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f"))
    ax.grid(True, color="#2d3148", linestyle="--", alpha=0.5)

    st.pyplot(fig)
    plt.close(fig)

    # ── Sección 4: comparación con benchmark ────────────────────────────────
    st.markdown("### ⚖️ Comparación con perfil estándar (Cura)")

    bench = BENCHMARK[material]

    filas_html = ""
    for gen in GENE_INFO:
        key = gen["key"]
        dec = gen["decimals"]
        fmt = f"{{:.{dec}f}}" if dec > 0 else "{:.0f}"
        v_ag = mejor[key]
        v_ben = bench[key]
        diff = v_ag - v_ben

        if abs(diff) < 0.01 * (
            MATERIAL_RANGES[material][key][1] - MATERIAL_RANGES[material][key][0]
        ):
            cls_diff = "diff-neu"
            s_diff = "≈ 0"
        elif diff > 0:
            cls_diff = "diff-pos"
            s_diff = f"+{fmt.format(diff)}"
        else:
            cls_diff = "diff-neg"
            s_diff = fmt.format(diff)

        filas_html += (
            f"<tr>"
            f"<td>{gen['label']}</td>"
            f"<td>{fmt.format(v_ag)} {gen['unit']}</td>"
            f"<td>{fmt.format(v_ben)} {gen['unit']}</td>"
            f"<td class='{cls_diff}'>{s_diff} {gen['unit']}</td>"
            f"</tr>"
        )

    st.markdown(
        f"""
        <table class="comp-table">
          <thead>
            <tr>
              <th>Parámetro</th>
              <th>AG (óptimo)</th>
              <th>Benchmark Cura</th>
              <th>Diferencia</th>
            </tr>
          </thead>
          <tbody>
            {filas_html}
          </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    st.caption(
        "Verde = AG supera al benchmark en esa dirección · "
        "Rojo = AG difiere negativamente · "
        "Gris = prácticamente igual"
    )

# ─── Estado inicial (sin ejecución) ──────────────────────────────────────────
else:
    st.info(
        "👈 Selecciona el **material**, el **perfil** y los parámetros del AG "
        "en el panel lateral, luego pulsa **Optimizar**."
    )

    # Mostrar rangos del material seleccionado
    st.markdown(f"### Rangos válidos para **{material}**")
    rangos = MATERIAL_RANGES[material]
    filas = ""
    for gen in GENE_INFO:
        key = gen["key"]
        lo, hi = rangos[key]
        dec = gen["decimals"]
        fmt = f"{{:.{dec}f}}" if dec > 0 else "{:.0f}"
        filas += (
            f"<tr><td>{gen['label']}</td>"
            f"<td>{fmt.format(lo)} – {fmt.format(hi)} {gen['unit']}</td></tr>"
        )

    st.markdown(
        f"""
        <table class="comp-table">
          <thead><tr><th>Parámetro</th><th>Rango válido</th></tr></thead>
          <tbody>{filas}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )
