# genetic.py — Algoritmo Genético para optimización de impresora 3D

import random
from config import MATERIAL_RANGES, GENE_KEYS, AG_DEFAULTS, RELLENO_MAXIMO
from fitness import calcular_fitness


# ─── Utilidades Educativas ──────────────────────────────────────────────────

def _reparar(valor, minimo, maximo):
    """
    Asegura que un valor no se salga de sus límites (Clamping).
    Si tras una mutación la temperatura sube a 300°C pero el máximo es 220°C,
    esta función la 'devuelve' al rango válido de 220°C.
    """
    return max(minimo, min(maximo, valor))


def _rango_efectivo(key, material, perfil):
    """
    Determina los límites reales (Min, Max) que puede tomar un gen.

    ¿Por qué esta distinción?
    - La mayoría de genes dependen del material (ej: el PLA funde a cierta temperatura).
    - Pero el 'relleno' depende del PERFIL (ej: en un perfil 'Estético' no queremos
      desperdiciar plástico, así que limitamos el máximo aunque la impresora pueda más).
    """
    lo, hi = MATERIAL_RANGES[material][key]
    if key == "relleno":
        hi = RELLENO_MAXIMO[perfil]
    return lo, hi


def _individuo_aleatorio(material, perfil):
    """
    Crea un individuo (configuración de impresión) con valores al azar.
    Es el 'Big Bang' de nuestro experimento evolutivo.
    """
    ind = {}
    for key in GENE_KEYS:
        lo, hi = _rango_efectivo(key, material, perfil)
        # Los perímetros son unidades enteras (1, 2, 3...), los demás son continuos.
        if key == "perimetros":
            ind[key] = float(random.randint(int(lo), int(hi)))
        else:
            ind[key] = random.uniform(lo, hi)
    return ind


def _clonar(individuo):
    """Crea una copia exacta de un individuo para no modificar el original por error."""
    return dict(individuo)


# ─── Selección por Torneo ────────────────────────────────────────────────────

def _seleccion_torneo(poblacion, fitnesses, k):
    """
    Simula una competencia para elegir quién será padre/madre.
    1. Toma 'k' individuos al azar de la población.
    2. Compara sus puntuaciones (fitness).
    3. El ganador (el más apto) es seleccionado para reproducirse.

    Esto asegura que los mejores tengan más hijos, pero da una pequeña
    oportunidad a los menos aptos para mantener la diversidad.
    """
    participantes = random.sample(range(len(poblacion)), k)
    ganador = max(participantes, key=lambda i: fitnesses[i])
    return _clonar(poblacion[ganador])


# ─── Cruce en un Punto (Crossover) ───────────────────────────────────────────

def _cruce(padre1, padre2, tasa_cruce):
    """
    Mezcla el ADN de dos padres para crear dos nuevos hijos.

    Funciona como un corte de tijera:
    - Se elige un punto al azar en la lista de genes.
    - El hijo 1 recibe la parte A del padre y la parte B de la madre.
    - El hijo 2 recibe la parte A de la madre y la parte B del padre.
    """
    # Si la suerte no acompaña (tasa_cruce), los hijos son copias de los padres.
    if random.random() > tasa_cruce:
        return _clonar(padre1), _clonar(padre2)

    punto = random.randint(1, len(GENE_KEYS) - 1)
    hijo1, hijo2 = {}, {}

    for i, key in enumerate(GENE_KEYS):
        if i < punto:
            hijo1[key] = padre1[key]
            hijo2[key] = padre2[key]
        else:
            hijo1[key] = padre2[key]
            hijo2[key] = padre1[key]

    return hijo1, hijo2


# ─── Mutación Gaussiana ──────────────────────────────────────────────────────

def _mutar(individuo, material, perfil, tasa_mutacion, sigma_fraccion):
    """
    Introduce pequeños errores aleatorios en el ADN.

    ¿Por qué Gaussiana? Porque es más probable que ocurra un cambio pequeño
    (ej: subir 1 grado la temperatura) que un cambio enorme (ej: subir 50 grados).
    Esto permite al algoritmo 'afinar' la solución poco a poco.
    """
    mutado = _clonar(individuo)

    for key in GENE_KEYS:
        if random.random() < tasa_mutacion:
            lo, hi = _rango_efectivo(key, material, perfil)
            # sigma define qué tan 'brusca' es la mutación.
            sigma = sigma_fraccion * (hi - lo)
            nuevo_valor = mutado[key] + random.gauss(0, sigma)

            if key == "perimetros":
                nuevo_valor = round(nuevo_valor)

            # Tras mutar, 'reparamos' por si nos salimos del rango permitido.
            mutado[key] = _reparar(nuevo_valor, lo, hi)

    return mutado


# ─── Algoritmo Genético Principal (El Ciclo de la Vida) ──────────────────────

def ejecutar_ag(material, perfil, config=None, callback_generacion=None):
    """
    Orquestador principal que ejecuta la evolución generación tras generación.
    """
    # 1. Configurar parámetros (usar por defecto o personalizados)
    cfg = AG_DEFAULTS.copy()
    if config:
        cfg.update(config)

    # 2. INICIALIZACIÓN: Crear la primera generación al azar.
    poblacion = [_individuo_aleatorio(material, perfil) for _ in range(cfg["poblacion"])]

    historial     = []
    historial_avg = []
    mejor_global  = None
    mejor_fitness_global = -1.0

    # 3. EL BUCLE EVOLUTIVO
    for gen in range(1, cfg["generaciones"] + 1):

        # A. EVALUACIÓN: Calcular el fitness de cada individuo.
        fitnesses = [calcular_fitness(ind, material, perfil) for ind in poblacion]

        # B. ESTADÍSTICAS: Ver quién es el mejor hasta ahora.
        mejor_idx     = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        mejor_fitness = fitnesses[mejor_idx]
        avg_fitness   = sum(fitnesses) / len(fitnesses)

        historial.append(mejor_fitness)
        historial_avg.append(avg_fitness)

        # Actualizar el récord histórico
        if mejor_fitness > mejor_fitness_global:
            mejor_fitness_global = mejor_fitness
            mejor_global         = _clonar(poblacion[mejor_idx])

        # Informar al exterior sobre el progreso (para la interfaz gráfica)
        if callback_generacion:
            callback_generacion(gen, mejor_fitness, avg_fitness)

        # C. ELITISMO: Copiamos a los mejores (N elites) directamente a la siguiente generación.
        # ¡Así nunca perdemos la mejor configuración que hayamos encontrado!
        indices_ordenados = sorted(range(len(fitnesses)),
                                   key=lambda i: fitnesses[i],
                                   reverse=True)
        elites = [_clonar(poblacion[i]) for i in indices_ordenados[:cfg["n_elites"]]]

        # D. REPRODUCCIÓN: Creamos nuevos individuos hasta completar la población.
        nueva_poblacion = list(elites)

        while len(nueva_poblacion) < cfg["poblacion"]:
            # SELECCIÓN: Elegimos dos padres mediante torneos.
            padre1 = _seleccion_torneo(poblacion, fitnesses, cfg["k_torneo"])
            padre2 = _seleccion_torneo(poblacion, fitnesses, cfg["k_torneo"])

            # CRUCE: Mezclamos su ADN.
            hijo1, hijo2 = _cruce(padre1, padre2, cfg["tasa_cruce"])

            # MUTACIÓN: Añadimos un toque de azar a los hijos.
            hijo1 = _mutar(hijo1, material, perfil, cfg["tasa_mutacion"], cfg["sigma_mutacion"])
            hijo2 = _mutar(hijo2, material, perfil, cfg["tasa_mutacion"], cfg["sigma_mutacion"])

            nueva_poblacion.append(hijo1)
            if len(nueva_poblacion) < cfg["poblacion"]:
                nueva_poblacion.append(hijo2)

        # La nueva generación se convierte en la población actual para el siguiente ciclo.
        poblacion = nueva_poblacion

    return {
        "mejor":         mejor_global,
        "fitness_final": mejor_fitness_global,
        "historial":     historial,
        "historial_avg": historial_avg,
    }
