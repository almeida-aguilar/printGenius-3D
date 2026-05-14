# config.py — Rangos, perfiles y benchmark para el AG de impresora 3D

# ─── Rangos válidos por material ────────────────────────────────────────────
#
# "ventilador_logica" define cómo se evalúa el ventilador en la función de fitness:
#   "maximizar" → más ventilador es mejor  (PLA: necesita enfriamiento agresivo)
#   "minimizar" → menos ventilador es mejor (ABS: evita warping por corrientes)
#   "centrar"   → valor medio es mejor     (PETG: equilibrio entre ambos extremos)
#
MATERIAL_RANGES = {
    "PLA": {
        "temp_extrucion": (190, 220),
        "temp_cama": (20, 60),
        "velocidad": (40, 100),
        "altura_capa": (0.08, 0.32),
        "relleno": (10, 100),
        "ventilador": (50, 100),
        "perimetros": (1, 5),
        "ventilador_logica": "maximizar",
    },
    "ABS": {
        "temp_extrucion": (220, 250),
        "temp_cama": (80, 110),
        "velocidad": (30, 80),
        "altura_capa": (0.08, 0.32),
        "relleno": (10, 100),
        "ventilador": (0, 30),
        "perimetros": (1, 5),
        "ventilador_logica": "minimizar",
    },
    "PETG": {
        "temp_extrucion": (230, 245),
        "temp_cama": (70, 90),
        "velocidad": (30, 80),
        "altura_capa": (0.08, 0.32),
        "relleno": (10, 100),
        "ventilador": (20, 50),
        "perimetros": (1, 5),
        "ventilador_logica": "centrar",
    },
}

# Orden y metadatos de los genes
GENE_INFO = [
    {"key": "temp_extrucion", "label": "Temp. Extrusión", "unit": "°C", "decimals": 1},
    {"key": "temp_cama", "label": "Temp. Cama", "unit": "°C", "decimals": 1},
    {"key": "velocidad", "label": "Velocidad", "unit": "mm/s", "decimals": 1},
    {"key": "altura_capa", "label": "Altura de Capa", "unit": "mm", "decimals": 3},
    {"key": "relleno", "label": "Relleno", "unit": "%", "decimals": 1},
    {"key": "ventilador", "label": "Ventilador", "unit": "%", "decimals": 1},
    {"key": "perimetros", "label": "Perímetros", "unit": "u", "decimals": 0},
]

GENE_KEYS = [g["key"] for g in GENE_INFO]

# ─── Relleno máximo por perfil ───────────────────────────────────────────────
# El rango físico de relleno va hasta 100%, pero en la práctica nadie lo usa.
# Este límite acota el espacio de búsqueda del AG según el objetivo real:
#   - Estético:   superficie importa, masa no → máximo 30%
#   - Funcional:  resistencia práctica real   → máximo 60%
#   - Rápido:     menos material = más rápido → máximo 25%
#   - Balanceado: punto medio razonable       → máximo 40%
RELLENO_MAXIMO = {
    "Estético": 30,
    "Funcional": 60,
    "Rápido": 25,
    "Balanceado": 40,
    "Personalizado": 40,
}

# ─── Pesos por perfil ────────────────────────────────────────────────────────
# Orden: [calidad, resistencia, velocidad, ahorro_material]
# Todos los pesos deben sumar 1.0
PROFILES = {
    "Estético": {
        "calidad": 0.50,
        "resistencia": 0.10,
        "velocidad": 0.25,
        "ahorro": 0.15,
    },
    "Funcional": {
        "calidad": 0.20,
        "resistencia": 0.50,
        "velocidad": 0.15,
        "ahorro": 0.15,
    },
    "Rápido": {"calidad": 0.10, "resistencia": 0.10, "velocidad": 0.50, "ahorro": 0.30},
    "Balanceado": {
        "calidad": 0.25,
        "resistencia": 0.25,
        "velocidad": 0.25,
        "ahorro": 0.25,
    },
    "Personalizado": {
        "calidad": 0.25,
        "resistencia": 0.25,
        "velocidad": 0.25,
        "ahorro": 0.25,
    },
}

# ─── Benchmark (perfiles estándar de Cura) ──────────────────────────────────
BENCHMARK = {
    "PLA": {
        "temp_extrucion": 200.0,
        "temp_cama": 60.0,
        "velocidad": 70.0,
        "altura_capa": 0.15,
        "relleno": 20.0,
        "ventilador": 100.0,
        "perimetros": 3.0,
    },
    "ABS": {
        "temp_extrucion": 245.0,
        "temp_cama": 85.0,
        "velocidad": 60.0,
        "altura_capa": 0.15,
        "relleno": 20.0,
        "ventilador": 2.0,
        "perimetros": 4.0,
    },
    "PETG": {
        "temp_extrucion": 240.0,
        "temp_cama": 85.0,
        "velocidad": 60.0,
        "altura_capa": 0.15,
        "relleno": 20.0,
        "ventilador": 20.0,
        "perimetros": 4.0,
    },
}

# ─── Parámetros del AG (valores por defecto) ────────────────────────────────
AG_DEFAULTS = {
    "poblacion": 50,
    "generaciones": 100,
    "tasa_cruce": 0.80,
    "tasa_mutacion": 0.10,
    "k_torneo": 3,
    "sigma_mutacion": 0.05,  # fracción del rango total para la gaussiana
    "n_elites": 1,
}
