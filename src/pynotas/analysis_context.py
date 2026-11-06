"""Reviewed analytical purpose, principle and interpretation; no runtime values."""
from dataclasses import dataclass
from .lessons import LESSONS


@dataclass(frozen=True)
class AnalysisContext:
    title: str
    purpose: str
    principle: str
    interpretation: str
    formula: str = ''
    source: str = ''


RMS_SOURCE='https://www.ifm.com/ca/en/shared/technologies/real-time-maintenance/technology/time-domain'


def for_model(model,representation):
    keys={t.key for t in model.theories}
    if 'rms' in keys:
        return AnalysisContext('RMS · medir la magnitud de una señal',
            'Resumir la magnitud global de una señal real. En vibraciones ayuda a seguir cambios en el nivel de un registro.',
            'Los signos pueden cancelarse al promediar. Elevar al cuadrado evita esa cancelación; promediar resume y la raíz recupera las unidades.',
            'Un RMS mayor indica mayor magnitud en el registro. Compara iguales unidades, banda y condiciones. Por sí solo no identifica una falla.',
            'RMS = √[(x₁² + … + xₙ²) / N]     x: muestras reales · N: cantidad de muestras',RMS_SOURCE)
    if 'fft' in keys:
        return AnalysisContext('FFT · reconocer componentes de frecuencia',
            'Pasar de cómo cambia una señal en el tiempo a qué componentes de frecuencia contiene.',
            'La transformada expresa la señal muestreada como componentes sinusoidales. La frecuencia de muestreo permite construir el eje en Hz.',
            'Un pico señala una componente destacada. Revisa escalado, ventana y muestreo antes de interpretar amplitudes; un pico no confirma una falla.',
            'Separación entre frecuencias = fs / N · Límite de Nyquist = fs / 2',
            'https://numpy.org/doc/stable/reference/routines.fft.html')
    if model.case:
        vibration=('En vibraciones, ' if model.context=='vibraciones' else 'Si los datos son vibraciones, ')
        return AnalysisContext('Archivo MATLAB · preparar los datos para analizarlos',
            'Identificar qué variables hay y cómo están organizadas antes de elegir los datos del análisis.',
            'Un .mat guarda variables. loadmat las organiza por nombre en un diccionario; type indica su tipo y shape, sus dimensiones.',
            vibration+'identifica canal, eje de muestras, unidades y frecuencia de muestreo. Cargar el archivo todavía no calcula RMS ni FFT.',
            source='https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.loadmat.html')
    if model.theories:
        theory=model.theories[0]
        return AnalysisContext(theory.title,theory.idea,' → '.join(theory.steps)+'.',theory.meaning,source=theory.source)
    lesson=LESSONS.get(representation.lesson_key,LESSONS['generic'])
    return AnalysisContext(lesson.title,lesson.idea,
        (' → '.join(s for s in (lesson.incoming,lesson.action,lesson.outgoing) if s)+'.') if lesson.incoming else 'Importar permite usar herramientas; no realiza todavía el análisis.',
        lesson.meaning,source=lesson.source)
