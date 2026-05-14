# fitness.py — Función de fitness multi-objetivo para configuración de impresora 3D

from config import GENE_KEYS, MATERIAL_RANGES, PROFILES


def _normalizar(valor, minimo, maximo):
    """
    Normaliza un valor al rango [0, 1].

    ¿Por qué? Para poder comparar peras con manzanas (ej: 200°C vs 0.2mm).
    0.0 significa que el valor es el mínimo del rango (peor).
    1.0 significa que el valor es el máximo del rango (mejor).
    """
    if maximo == minimo:
        return 0.0
    return (valor - minimo) / (maximo - minimo)


def _score_ventilador(ventilador, r_ven, logica):
    """
    Calcula el score de enfriamiento según la necesidad de cada material.

    Lógicas:
        "maximizar" (PLA)  → Más ventilador = mejor score.
        "minimizar" (ABS)  → Menos ventilador = mejor score (evita grietas).
        "centrar"   (PETG) → El valor medio es el equilibrio perfecto.
    """
    if logica == "maximizar":
        return _normalizar(ventilador, r_ven[0], r_ven[1])
    elif logica == "minimizar":
        return 1.0 - _normalizar(ventilador, r_ven[0], r_ven[1])
    elif logica == "centrar":
        centro = r_ven[0] + 0.5 * (r_ven[1] - r_ven[0])
        return 1.0 - abs(ventilador - centro) / (r_ven[1] - r_ven[0])
    else:
        raise ValueError(f"ventilador_logica desconocida: '{logica}'.")


def _componentes(individuo, material, perfil):
    """
    Calcula los 4 pilares del fitness: Calidad, Resistencia, Velocidad y Ahorro.
    Esta es la 'fuente de verdad' de cómo se evalúa una configuración.
    """
    rangos = MATERIAL_RANGES[material]

    # ── Extraer genes (los parámetros que el AG está optimizando) ────────────
    temp_ext = individuo["temp_extrucion"]
    temp_cama = individuo["temp_cama"]
    velocidad = individuo["velocidad"]
    altura = individuo["altura_capa"]
    relleno = individuo["relleno"]
    ventilador = individuo["ventilador"]
    perimetros = individuo["perimetros"]

    # ── Rangos de cada gen (límites mínimos y máximos) ───────────────────────
    r_te = rangos["temp_extrucion"]
    r_tc = rangos["temp_cama"]
    r_vel = rangos["velocidad"]
    r_alt = rangos["altura_capa"]
    r_rel = rangos["relleno"]
    r_ven = rangos["ventilador"]
    r_per = rangos["perimetros"]

    # ── 1. CALIDAD Y FIABILIDAD ──────────────────────────────────────────────
    # Buscamos: Capas finas (1.0 - normalizar), velocidad lenta y buena adhesión.
    calidad_capa = 1.0 - _normalizar(altura, r_alt[0], r_alt[1])
    calidad_vel = 1.0 - _normalizar(velocidad, r_vel[0], r_vel[1])
    adhesion = _normalizar(temp_cama, r_tc[0], r_tc[1])
    enfriamiento = _score_ventilador(ventilador, r_ven, rangos["ventilador_logica"])

    # Temperatura para calidad: Se busca un punto medio-bajo (35% del rango)
    # para evitar que el plástico gotee demasiado (stringing).
    centro_q = r_te[0] + 0.35 * (r_te[1] - r_te[0])
    calidad_t = 1.0 - abs(temp_ext - centro_q) / (r_te[1] - r_te[0])

    calidad = (
        0.35 * calidad_capa
        + 0.25 * calidad_vel
        + 0.15 * adhesion
        + 0.15 * enfriamiento
        + 0.10 * calidad_t
    )

    # ── 2. RESISTENCIA MECÁNICA ──────────────────────────────────────────────
    # Buscamos: Mucho relleno y perímetros. Usamos potencia 0.25 para que el
    # beneficio de subir estos valores sea muy alto al principio.
    res_relleno = _normalizar(relleno, r_rel[0], r_rel[1]) ** 0.25
    res_perimetros = _normalizar(perimetros, r_per[0], r_per[1]) ** 0.25

    # Temperatura para resistencia: Se busca un punto medio-alto (65% del rango)
    # para que las capas se fundan con más fuerza entre sí.
    centro_temp = r_te[0] + 0.65 * (r_te[1] - r_te[0])
    res_temp = 1.0 - abs(temp_ext - centro_temp) / (r_te[1] - r_te[0])

    resistencia = 0.45 * res_relleno + 0.35 * res_perimetros + 0.20 * res_temp

    # ── 3. VELOCIDAD DE IMPRESIÓN ────────────────────────────────────────────
    # Para evitar que el AG empuje los valores siempre al máximo (100 mm/s, 0.35 mm)
    # usamos rendimientos decrecientes (** 0.5). Esto genera un "punto dulce"
    # matemático al cruzarse con las penalizaciones lineales de la métrica de Calidad.
    # Damos ligeramente más peso a la altura (60%) que a la velocidad (40%).
    score_v = _normalizar(velocidad, r_vel[0], r_vel[1]) ** 0.5
    score_a = _normalizar(altura, r_alt[0], r_alt[1]) ** 0.5
    velocidad_score = 0.4 * score_v + 0.6 * score_a

    # ── 4. AHORRO DE MATERIAL ────────────────────────────────────────────────
    # Es lo opuesto a la resistencia: premia usar poco relleno y pocos perímetros.
    ahorro_rel = 1.0 - _normalizar(relleno, r_rel[0], r_rel[1])
    ahorro_per = 1.0 - _normalizar(perimetros, r_per[0], r_per[1])
    ahorro = 0.85 * ahorro_rel + 0.15 * ahorro_per

    return {
        "calidad": calidad,
        "resistencia": resistencia,
        "velocidad": velocidad_score,
        "ahorro": ahorro,
    }


def calcular_fitness(individuo, material, perfil):
    """
    Calcula el fitness FINAL multiplicando los componentes por los pesos
    del perfil elegido (Estético, Funcional, etc.).
    """
    comp = _componentes(individuo, material, perfil)
    pesos = PROFILES[perfil]

    # Suma ponderada: (Peso Calidad * Score Calidad) + (Peso Resistencia * Score Resistencia) + ...
    fitness = sum(pesos[k] * comp[k] for k in comp)
    return round(float(fitness), 6)


def desglose_fitness(individuo, material, perfil):
    """
    Retorna el detalle de cada pilar para que el usuario lo vea en la interfaz.
    """
    comp = _componentes(individuo, material, perfil)
    return {
        "Calidad": round(comp["calidad"], 4),
        "Resistencia": round(comp["resistencia"], 4),
        "Velocidad": round(comp["velocidad"], 4),
        "Ahorro": round(comp["ahorro"], 4),
        "Fitness": calcular_fitness(individuo, material, perfil),
    }
