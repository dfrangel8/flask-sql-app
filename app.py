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
        # Imprimir información de diagnóstico
        print("Intentando conectar a la base de datos...")
        print(f"Server: {os.getenv('DB_SERVER')}")
        print(f"Database: {os.getenv('DB_DATABASE')}")
        
        # Intentar diferentes strings de conexión
        connection_strings = [
            # String de conexión 1
            f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.getenv("DB_SERVER")};DATABASE={os.getenv("DB_DATABASE")};UID={os.getenv("DB_USERNAME")};PWD={os.getenv("DB_PASSWORD")}',
            # String de conexión 2
            f'DRIVER={{/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.so}};SERVER={os.getenv("DB_SERVER")};DATABASE={os.getenv("DB_DATABASE")};UID={os.getenv("DB_USERNAME")};PWD={os.getenv("DB_PASSWORD")}'
        ]
        
        last_error = None
        for conn_str in connection_strings:
            try:
                print(f"Intentando conectar con string: {conn_str}")
                conn = pyodbc.connect(conn_str)
                print("Conexión exitosa!")
                return conn
            except Exception as e:
                print(f"Error con string de conexión: {str(e)}")
                last_error = e
        
        if last_error:
            raise last_error
            
    except Exception as e:
        print(f"Error de conexión a la base de datos: {str(e)}")
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
                return jsonify([])

            query = """
            SELECT TOP 1000
                CodigoCliente,
                RazonSocial,
                CifDni,
                Direccion,
                CodigoPostal,
                Poblacion,
                Provincia,
                Telefono
            FROM dbo.Clientes
            ORDER BY RazonSocial
            """

            cursor = conn.cursor()
            cursor.execute(query)
            
            results = []
            for row in cursor.fetchall():
                result = {
                    "CodigoCliente": str(row[0]).strip(),
                    "RazonSocial": str(row[1]).strip() if row[1] else "",
                    "CifDni": str(row[2]).strip() if row[2] else "",
                    "Direccion": str(row[3]).strip() if row[3] else "",
                    "CodigoPostal": str(row[4]).strip() if row[4] else "",
                    "Poblacion": str(row[5]).strip() if row[5] else "",
                    "Provincia": str(row[6]).strip() if row[6] else "",
                    "Telefono": str(row[7]).strip() if row[7] else ""
                }
                results.append(result)

            cursor.close()
            conn.close()
            return jsonify(results)
        
        return render_template('clientes.html')

    except Exception as e:
        print(f"Error en get_clientes: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify([])

@app.route('/compras')
def get_compras():
    try:
        print("Iniciando consulta de compras")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            conn = get_db_connection()
            if not conn:
                print("Error de conexión a la base de datos")
                return jsonify([])  # Retornamos array vacío en lugar de error 500

            query = """
            SELECT TOP 1000
                cap.SerieAlbaran,
                cap.NumeroAlbaran,
                CONVERT(VARCHAR(10), cap.FechaAlbaran, 120) as FechaAlbaran,
                cap.CodigoProveedor,
                p.RazonSocial,
                p.CifDni,
                ISNULL(cap.ImporteLiquido, 0) as ImporteLiquido
            FROM dbo.CabeceraAlbaranProveedor cap
            LEFT JOIN dbo.Proveedores p ON cap.CodigoProveedor = p.CodigoProveedor
            ORDER BY cap.FechaAlbaran DESC
            """

            cursor = conn.cursor()
            cursor.execute(query)
            
            results = []
            for row in cursor.fetchall():
                result = {
                    "SerieAlbaran": str(row[0]).strip(),
                    "NumeroAlbaran": str(row[1]).strip(),
                    "FechaAlbaran": str(row[2]),
                    "CodigoProveedor": str(row[3]).strip(),
                    "RazonSocial": str(row[4]).strip() if row[4] else "",
                    "CifDni": str(row[5]).strip() if row[5] else "",
                    "ImporteLiquido": float(row[6])
                }
                results.append(result)

            cursor.close()
            conn.close()
            return jsonify(results)
        
        return render_template('compras.html')

    except Exception as e:
        print(f"Error en get_compras: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify([])  # Retornamos array vacío en lugar de error 500

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
