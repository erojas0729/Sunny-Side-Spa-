import ast
import json
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from IPython.display import HTML

st.set_page_config(page_title="Sunny Side Luxury Spa", layout="wide")
st.title("Sunny Side Luxury Spa")

ruta = Path(__file__).with_name("SunnySideLuxurySpa_Planificador.ipynb")
if not ruta.is_file():
    st.error(f"Sube {ruta.name} a la misma carpeta que app.py.")
    st.stop()


def mostrar(*resultados, **_):
    for resultado in resultados:
        if isinstance(resultado, HTML):
            st.html(resultado.data)
        elif isinstance(resultado, (pd.DataFrame, pd.Series)):
            st.dataframe(resultado)
        else:
            st.write(resultado)


def mostrar_graficas(*args, **kwargs):
    for numero in plt.get_fignums():
        figura = plt.figure(numero)
        st.pyplot(figura)
        plt.close(figura)


nombre = ruta.name
try:
    notebook = json.loads(ruta.read_text(encoding="utf-8"))
    celdas = []
    for numero, celda in enumerate(notebook["cells"], start=1):
        if celda["cell_type"] == "code":
            nombre = f"{ruta.name}, celda {numero}"
            codigo = "".join(celda["source"])
            celdas.append((nombre, ast.parse(codigo, filename=nombre)))

    asignacion_clientes = None
    for _, arbol in celdas:
        for instruccion in arbol.body:
            if (
                isinstance(instruccion, ast.Assign)
                and len(instruccion.targets) == 1
                and isinstance(instruccion.targets[0], ast.Name)
                and instruccion.targets[0].id == "clientes_esperados"
                and isinstance(instruccion.value, ast.Constant)
                and type(instruccion.value.value) is int
            ):
                asignacion_clientes = instruccion

    if asignacion_clientes is not None:
        clientes = st.number_input(
            "Clientes esperados hoy",
            min_value=0,
            value=asignacion_clientes.value.value,
            step=1,
        )
        asignacion_clientes.value = ast.copy_location(
            ast.Constant(value=int(clientes)), asignacion_clientes.value
        )

    contexto = {"__name__": "__main__", "display": mostrar}
    with patch("IPython.display.display", mostrar), patch.object(
        plt, "show", mostrar_graficas
    ):
        for nombre, arbol in celdas:
            exec(compile(arbol, nombre, "exec"), contexto)

except Exception as error:
    st.error(f"Error al ejecutar {nombre}.")
    st.exception(error)
finally:
    plt.close("all")
