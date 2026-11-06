"""Command-line entry point. User scripts are always read, never executed."""
import argparse
import sys
from .files import explicar_archivo
from ._version import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(description='Explica un archivo Python como lámina HTML sin ejecutarlo.')
    parser.add_argument('--version', action='version', version='PyNotas '+__version__)
    parser.add_argument('archivo', help='Archivo .py que quieres comprender')
    parser.add_argument('-o','--salida', help='Ruta del HTML; por defecto: archivo.pynotas.html')
    parser.add_argument('--formato', choices=['auto','flujo','despiece','decisiones'], default='auto')
    parser.add_argument('--sobrescribir', action='store_true', help='Permite reemplazar el HTML de destino')
    args = parser.parse_args(argv)
    try:
        output = explicar_archivo(args.archivo,args.salida,sobrescribir=args.sobrescribir,formato=args.formato)
    except (OSError,UnicodeError,SyntaxError,ValueError,RecursionError) as error:
        print(f'No se pudo crear la lámina: {error}', file=sys.stderr)
        return 2
    print(f'Lámina guardada en {output}. El archivo Python no se ejecutó.')
    return 0
