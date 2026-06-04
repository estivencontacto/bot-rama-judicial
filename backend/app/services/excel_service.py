"""Lectura de archivos Excel para carga masiva.

El parser busca la columna `Radicado` aunque no este en la primera fila, lo que
permite usar plantillas con encabezados e instrucciones visibles.
"""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def parse_radicados_excel(content: bytes) -> list[str]:
    """Extrae radicados unicos desde la primera columna llamada `Radicado`."""
    raw = pd.read_excel(BytesIO(content), header=None, dtype=str)
    header_row = None
    radicado_column = None

    for row_index, row in raw.iterrows():
        for column_index, value in row.items():
            if str(value).strip().lower() == "radicado":
                header_row = row_index
                radicado_column = column_index
                break
        if header_row is not None:
            break

    if header_row is None or radicado_column is None:
        raise ValueError("El archivo Excel debe tener una columna llamada 'Radicado'.")

    serie = raw.iloc[header_row + 1 :, radicado_column].dropna().astype(str).str.strip()
    serie = serie[serie.ne("")]
    return serie.drop_duplicates().tolist()
