import os
import csv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

CSV_FILENAME = 'reconocimientos.csv'

app = FastAPI(
    title="Servidor de Ciberseguridad",
    version="0.1.0"
)

@app.get("/", response_class=HTMLResponse)
def mostrar_csv():
    if not os.path.exists(CSV_FILENAME):
        raise HTTPException(status_code=404, detail="El archivo CSV no se encontró")

    try:
        with open(CSV_FILENAME, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            rows = [row for row in reader]

        table_rows = ''.join([
            '<tr>' + ''.join([f'<td>{row[h]}</td>' for h in headers]) + '</tr>'
            for row in rows
        ])
        table_headers = ''.join([f'<th>{h}</th>' for h in headers])

        html = f"""
        <html>
            <head>
                <style>
                    table {{
                        border-collapse: collapse;
                        width: 80%;
                        margin: 20px auto;
                        font-family: Arial, sans-serif;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: center;
                    }}
                    th {{
                        background-color: #4CAF50;
                        color: white;
                    }}
                    .center {{
                        text-align: center;
                        margin-top: 20px;
                    }}
                    button {{
                        padding: 10px 20px;
                        font-size: 16px;
                        cursor: pointer;
                    }}
                </style>
            </head>
            <body>
                <h2 style="text-align:center">REGISTRO RECONOCIMIENTO FACIAL</h2>
                <table>
                    <thead>
                        <tr>{table_headers}</tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                <div class="center">
                    <button onclick="location.reload()">Refrescar página</button>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=html)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el archivo: {e}")
