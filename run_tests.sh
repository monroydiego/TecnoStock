#!/bin/sh
# Ejecuta todas las pruebas con la biblioteca estándar (sin dependencias).
PYTHONPATH=src python3 -m unittest discover -s tests -t . -v
