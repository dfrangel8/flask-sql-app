import os
import pyodbc
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

def get_db_connection():
    try:
        print("\n=== Iniciando conexión a la base de datos ===")
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER=SERVIDOR\\SAGE200;'
            f'DATABASE=MMARKET;'
            f'UID=ConsultasMM;'
            f'PWD=Sage2009+;'
            'TrustServerCertificate=yes;'
            'Encrypt=no;'
        )
        
        print("Intentando conexión...")
        conn = pyodbc.connect(conn_str)
        print("¡Conexión exitosa!")
        return conn
    except Exception as e:
        print(f"Error de conexión: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-db')
def test_db():
    conn = get_db_connection()
    if conn:
        return "Conexión exitosa a la base de datos!"
    return "Error de conexión a la base de datos"

@app.route('/clientes')
def get_clientes():
    try:
        if not request.headers.get('X-Requested-With'):
            return render_template('clientes.html')

        print("Obteniendo datos de clientes...")
        conn = get_db_connection()
        if not conn:
            print("No se pudo conectar a la base de datos")
            return jsonify([])

        cursor = conn.cursor()
        query = """
            SELECT TOP 10 
                CodigoCliente,
                CifDni,
                RazonSocial,
                Domicilio,
                Municipio,
                Provincia,
                Telefono
            FROM Clientes
            ORDER BY RazonSocial
        """
        
        print(f"Ejecutando query: {query}")
        cursor.execute(query)
        
        results = []
        for row in cursor:
            result = {
                "CodigoCliente": str(row[0] or '').strip(),
                "CifDni": str(row[1] or '').strip(),
                "RazonSocial": str(row[2] or '').strip(),
                "Domicilio": str(row[3] or '').strip(),
                "Municipio": str(row[4] or '').strip(),
                "Provincia": str(row[5] or '').strip(),
                "Telefono": str(row[6] or '').strip()
            }
            results.append(result)
            print(f"Procesada fila: {result}")

        cursor.close()
        conn.close()
        print(f"Total registros encontrados: {len(results)}")
        return jsonify(results)

    except Exception as e:
        print(f"Error en get_clientes: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify([])

@app.route('/test-clientes')
def test_clientes():
    try:
        print("Probando consulta de clientes...")
        conn = get_db_connection()
        if not conn:
            return "No se pudo conectar a la base de datos"

        cursor = conn.cursor()
        
        # Consulta simple para ver la estructura
        query = "SELECT TOP 1 * FROM dbo.Clientes"
        cursor.execute(query)
        
        # Obtener nombres de columnas
        columns = [column[0] for column in cursor.description]
        print("\nColumnas en la tabla:")
        for col in columns:
            print(f"- {col}")
        
        # Obtener un registro de ejemplo
        row = cursor.fetchone()
        if row:
            print("\nDatos de ejemplo:")
            for i, col in enumerate(columns):
                print(f"{col}: {row[i]}")
        
        cursor.close()
        conn.close()
        
        return "Revisa la consola para ver la estructura de la tabla"

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"

@app.route('/compras')
def get_compras():
    try:
        if not request.headers.get('X-Requested-With'):
            return render_template('compras.html')

        print("Obteniendo datos de compras...")
        conn = get_db_connection()
        if not conn:
            print("No se pudo conectar a la base de datos")
            return jsonify([])

        cursor = conn.cursor()
        query = """
            SELECT TOP 100
                c.SerieAlbaran,
                c.NumeroAlbaran,
                CONVERT(VARCHAR(10), c.FechaAlbaran, 103) as Fecha,
                c.CodigoProveedor,
                p.RazonSocial,
                p.CifDni,
                c.ImporteLiquido
            FROM CabeceraAlbaranProveedor c
            LEFT JOIN Proveedores p ON c.CodigoProveedor = p.CodigoProveedor
            ORDER BY c.FechaAlbaran DESC, c.SerieAlbaran, c.NumeroAlbaran
        """
        
        print(f"Ejecutando query: {query}")
        cursor.execute(query)
        
        results = []
        for row in cursor:
            result = {
                "Serie": str(row[0] or '').strip(),
                "Numero": str(row[1] or '').strip(),
                "Fecha": str(row[2] or ''),
                "CodigoProveedor": str(row[3] or '').strip(),
                "RazonSocial": str(row[4] or '').strip(),
                "CifDni": str(row[5] or '').strip(),
                "Total": float(row[6] or 0)
            }
            results.append(result)

        cursor.close()
        conn.close()
        print(f"Total registros encontrados: {len(results)}")
        return jsonify(results)

    except Exception as e:
        print(f"Error en get_compras: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify([])

@app.route('/test-compras')
def test_compras():
    try:
        print("Probando consulta de compras...")
        conn = get_db_connection()
        if not conn:
            return "No se pudo conectar a la base de datos"

        cursor = conn.cursor()
        
        # Verificar si la tabla existe y su estructura
        print("\nVerificando tablas...")
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND TABLE_NAME LIKE '%Compra%'
        """)
        
        tables = cursor.fetchall()
        print("\nTablas encontradas:")
        for table in tables:
            print(f"- {table[0]}")
            cursor.execute(f"SELECT TOP 1 * FROM {table[0]}")
            columns = [column[0] for column in cursor.description]
            print(f"  Columnas: {', '.join(columns)}")
        
        cursor.close()
        conn.close()
        return "Revisa la consola para ver las tablas y columnas"

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
