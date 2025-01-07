from flask import Flask, jsonify, render_template, request
import pyodbc
import logging
from datetime import datetime
import os

app = Flask(__name__, 
    static_folder='static',    # Asegúrate de que esto coincida con tu estructura de carpetas
    template_folder='templates' # Asegúrate de que esto coincida con tu estructura de carpetas
)

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        print("\n=== Iniciando conexión a la base de datos ===")
        server = os.getenv('DB_SERVER', '').replace('\\', '\\\\')
        database = os.getenv('DB_NAME', '')
        username = os.getenv('DB_USER', '')
        password = os.getenv('DB_PASSWORD', '')

        print(f"""
        Configuración:
        Server: {server}
        Database: {database}
        Username: {username}
        Password: {'*' * len(password) if password else 'No configurado'}
        """)

        if not all([server, database, username, password]):
            print("Error: Faltan variables de entorno")
            return None

        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
            'TrustServerCertificate=yes;'
            'Encrypt=no;'
        )

        print("Intentando conexión...")
        conn = pyodbc.connect(conn_str)
        print("¡Conexión exitosa!")
        
        # Verificar la conexión con una consulta simple
        cursor = conn.cursor()
        cursor.execute("SELECT @@version")
        version = cursor.fetchone()[0]
        print(f"Versión SQL Server: {version}")
        cursor.close()
        
        return conn

    except Exception as e:
        print(f"Error de conexión: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clientes')
def get_clientes():
    try:
        print("Iniciando consulta de clientes")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            conn = get_db_connection()
            if not conn:
                print("Error de conexión a la base de datos")
                return jsonify({"error": "No se pudo conectar a la base de datos"})

            # Consulta de prueba simple
            query = """
            SELECT TOP 10 * FROM dbo.Clientes WITH (NOLOCK)
            """

            print("Ejecutando query de prueba...")
            cursor = conn.cursor()
            
            # Imprimir todas las tablas disponibles
            print("Listando tablas disponibles:")
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """)
            tables = cursor.fetchall()
            for table in tables:
                print(f"Tabla encontrada: {table[0]}")

            # Intentar la consulta original
            print("Ejecutando consulta principal...")
            cursor.execute(query)
            
            # Imprimir información de columnas
            columns = [column[0] for column in cursor.description]
            print("Columnas:", columns)
            
            results = []
            for row in cursor.fetchall():
                result = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    if value is None:
                        result[column] = ""
                    elif isinstance(value, (int, float)):
                        result[column] = float(value)
                    else:
                        result[column] = str(value).strip()
                results.append(result)
                print(f"Fila procesada: {result}")

            cursor.close()
            conn.close()

            print(f"Total registros encontrados: {len(results)}")
            return jsonify(results)
        
        return render_template('clientes.html')

    except Exception as e:
        print(f"Error en get_clientes: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)})

@app.route('/compras')
def get_compras():
    try:
        print("Iniciando consulta de compras")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            conn = get_db_connection()
            if not conn:
                print("Error de conexión a la base de datos")
                return jsonify([])

            # Query simplificada para pruebas
            query = """
            SELECT TOP 100
                cap.SerieAlbaran,
                cap.NumeroAlbaran,
                CONVERT(VARCHAR(10), cap.FechaAlbaran, 120) as FechaAlbaran,
                cap.CodigoProveedor,
                ISNULL(p.RazonSocial, '') as RazonSocial,
                ISNULL(p.CifDni, '') as CifDni,
                ISNULL(cap.ImporteLiquido, 0) as ImporteLiquido
            FROM dbo.CabeceraAlbaranProveedor cap WITH (NOLOCK)
            LEFT JOIN dbo.Proveedores p WITH (NOLOCK) 
                ON cap.CodigoProveedor = p.CodigoProveedor
            WHERE cap.FechaAlbaran >= DATEADD(month, -6, GETDATE())
            ORDER BY cap.FechaAlbaran DESC
            """

            print("Ejecutando query:", query)  # Debug
            cursor = conn.cursor()
            cursor.execute(query)
            
            results = []
            for row in cursor.fetchall():
                try:
                    result = {
                        "SerieAlbaran": str(row[0]).strip(),
                        "NumeroAlbaran": str(row[1]).strip(),
                        "FechaAlbaran": str(row[2]),
                        "CodigoProveedor": str(row[3]).strip(),
                        "RazonSocial": str(row[4]).strip(),
                        "CifDni": str(row[5]).strip(),
                        "ImporteLiquido": float(row[6] or 0)
                    }
                    results.append(result)
                    print(f"Procesado registro: {result}")  # Debug
                except Exception as e:
                    print(f"Error procesando fila: {str(e)}")
                    continue

            print(f"Total de registros encontrados: {len(results)}")  # Debug
            cursor.close()
            return jsonify(results)
        
        return render_template('compras.html')

    except Exception as e:
        print(f"Error en get_compras: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify([])

@app.route('/compras/detalle')
def get_detalle_compra():
    try:
        serie = request.args.get('serie')
        numero = request.args.get('numero')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500

        query = """
        SELECT 
            lap.SerieAlbaran,
            lap.NumeroAlbaran,
            lap.DescripcionArticulo,
            ISNULL(lap.Partida, '') as Partida,
            lap.FechaCaduca,
            ISNULL(lap.Unidades, 0) as Unidades,
            ISNULL(lap.Precio, 0) as Precio,
            ISNULL(lap.ImporteNeto, 0) as ImporteNeto
        FROM dbo.LineasAlbaranProveedor lap
        WHERE lap.SerieAlbaran = ? AND lap.NumeroAlbaran = ?
        ORDER BY lap.NumeroLinea
        """

        cursor = conn.cursor()
        cursor.execute(query, (serie, numero))
        
        results = []
        for row in cursor.fetchall():
            result_dict = {
                "SerieAlbaran": str(row[0]).strip() if row[0] else "",
                "NumeroAlbaran": str(row[1]).strip() if row[1] else "",
                "DescripcionArticulo": str(row[2]).strip() if row[2] else "",
                "Partida": str(row[3]).strip() if row[3] else "",
                "FechaCaduca": row[4].strftime('%Y-%m-%d') if row[4] else "",
                "Unidades": float(row[5]) if row[5] else 0,
                "Precio": float(row[6]) if row[6] else 0,
                "ImporteNeto": float(row[7]) if row[7] else 0
            }
            results.append(result_dict)

        return jsonify(results)

    except Exception as e:
        print(f"Error en get_detalle_compra: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
