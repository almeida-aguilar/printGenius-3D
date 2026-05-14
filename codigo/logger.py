# logger.py — Manejo de logs con fecha y hora para cada ejecución del AG

import os
from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")


def _asegurar_directorio():
    """Crea la carpeta logs/ si no existe."""
    os.makedirs(LOGS_DIR, exist_ok=True)


def _timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _nombre_archivo():
    return datetime.now().strftime("optimizacion_%Y%m%d_%H%M%S.log")


class Logger:
    """
    Maneja un archivo .log por ejecución del AG.
    Uso:
        log = Logger()
        log.inicio(material, perfil, config)
        log.generacion(gen, fitness)
        log.resultado(mejor_individuo, fitness_final)
    """

    def __init__(self):
        _asegurar_directorio()
        self.filepath = os.path.join(LOGS_DIR, _nombre_archivo())
        self._file = open(self.filepath, "w", encoding="utf-8")

    def _escribir(self, mensaje=""):
        ts   = _timestamp()
        line = f"[{ts}] {mensaje}" if mensaje else f"[{_timestamp()}]"
        self._file.write(line + "\n")
        self._file.flush()

    def inicio(self, material, perfil, config):
        self._escribir("=" * 55)
        self._escribir(f"NUEVA EJECUCIÓN")
        self._escribir(f"Material          : {material}")
        self._escribir(f"Perfil            : {perfil}")
        self._escribir(f"Tamaño población  : {config['poblacion']}")
        self._escribir(f"Generaciones      : {config['generaciones']}")
        self._escribir(f"Tasa cruce        : {config['tasa_cruce']}")
        self._escribir(f"Tasa mutación     : {config['tasa_mutacion']}")
        self._escribir(f"Torneo K          : {config['k_torneo']}")
        self._escribir("--- Evolución ---")

    def generacion(self, gen, mejor_fitness, avg_fitness):
        self._escribir(
            f"Gen {gen:04d} | Mejor fitness: {mejor_fitness:.6f} | "
            f"Promedio: {avg_fitness:.6f}"
        )

    def resultado(self, mejor_individuo, fitness_final, desglose):
        self._escribir("--- Resultado final ---")
        self._escribir(f"Fitness final     : {fitness_final:.6f}")
        self._escribir("")
        self._escribir("Parámetros óptimos:")

        etiquetas = {
            "temp_extrucion": "Temp. Extrusión ",
            "temp_cama":      "Temp. Cama      ",
            "velocidad":      "Velocidad       ",
            "altura_capa":    "Altura de Capa  ",
            "relleno":        "Relleno         ",
            "ventilador":     "Ventilador      ",
            "perimetros":     "Perímetros      ",
        }
        unidades = {
            "temp_extrucion": "°C",
            "temp_cama":      "°C",
            "velocidad":      "mm/s",
            "altura_capa":    "mm",
            "relleno":        "%",
            "ventilador":     "%",
            "perimetros":     "u",
        }

        for key, label in etiquetas.items():
            valor  = mejor_individuo[key]
            unidad = unidades[key]
            if key == "perimetros":
                self._escribir(f"  {label}: {int(valor)} {unidad}")
            elif key == "altura_capa":
                self._escribir(f"  {label}: {valor:.3f} {unidad}")
            else:
                self._escribir(f"  {label}: {valor:.1f} {unidad}")

        self._escribir("")
        self._escribir("Desglose fitness:")
        for componente, valor in desglose.items():
            self._escribir(f"  {componente:<14}: {valor:.4f}")

        self._escribir("=" * 55)

    def cerrar(self):
        self._file.close()

    @property
    def nombre_archivo(self):
        return os.path.basename(self.filepath)


def listar_logs():
    """Retorna lista de archivos .log ordenados por fecha descendente."""
    _asegurar_directorio()
    archivos = [f for f in os.listdir(LOGS_DIR) if f.endswith(".log")]
    return sorted(archivos, reverse=True)


def leer_log(nombre_archivo):
    """Retorna el contenido de un archivo .log como string."""
    path = os.path.join(LOGS_DIR, nombre_archivo)
    if not os.path.exists(path):
        return "Archivo no encontrado."
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
