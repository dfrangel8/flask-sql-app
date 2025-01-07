from flask import Flask, jsonify, render_template, request
import pyodbc
import logging
from datetime import datetime

app = Flask(__name__, 
    static_folder='static',    # Asegúrate de que esto coincida con tu estructura de carpetas
    template_folder='templates' # Asegúrate de que esto coincida con tu estructura de carpetas
)

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=SERVIDOR\\SAGE200;'
            'DATABASE=MMARKET;'
            'UID=ConsultasMM;'
            'PWD=Sage2009+;'
            'Trusted_Connection=no;'
        )
        logger.info("Conexión a base de datos exitosa")
        return conn
    except Exception as e:
        logger.error(f"Error de conexión a la base de datos: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clientes')
def get_clientes():
    try:
        # Si es una solicitud AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            conn = get_db_connection()
            if not conn:
                logger.error("No se pudo establecer conexión con la base de datos")
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            query = """
            SELECT 
                c.CodigoCliente,
                c.CifDni,
                c.RazonSocial,
                c.Municipio,
                c.Provincia,
                c.Nacion,
                c.Telefono,
                ca.CodigoEmpresa,
                ca.IdDelegacion,
                ca.EjercicioAlbaran,
                ca.SerieAlbaran,
                ca.NumeroAlbaran,
                ca.FechaAlbaran,
                ca.NumeroLineas,
                ISNULL(ca.ImporteCoste, 0) as ImporteCoste,
                ISNULL(ca.ImporteNetoLineas, 0) as ImporteNetoLineas,
                ISNULL(ca.ImporteDescuento, 0) as ImporteDescuento,
                ISNULL(ca.BaseImponible, 0) as BaseImponible
            FROM dbo.Clientes c
            LEFT JOIN dbo.CabeceraAlbaranCliente ca 
                ON c.CifDni = ca.CifDni
            WHERE c.CodigoCliente IS NOT NULL
            ORDER BY c.RazonSocial
            """

            cursor = conn.cursor()
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result_dict = {}
                for i, value in enumerate(row):
                    if isinstance(value, datetime):
                        result_dict[columns[i]] = value.strftime('%Y-%m-%d')
                    elif isinstance(value, (int, float)):
                        result_dict[columns[i]] = float(value)
                    elif value is None:
                        result_dict[columns[i]] = ""
                    else:
                        result_dict[columns[i]] = str(value).strip()
                results.append(result_dict)

            return jsonify(results)
        
        # Si no es AJAX, renderizar el template HTML
        return render_template('clientes.html')

    except Exception as e:
        logger.error(f"Error al obtener datos: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/compras')
def get_compras():
    try:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "Error de conexión a la base de datos"}), 500

            query = """
            SELECT 
                cap.SerieAlbaran,
                cap.NumeroAlbaran,
                cap.FechaAlbaran,
                cap.CodigoProveedor,
                p.RazonSocial,
                p.CifDni,
                cap.ImporteLiquido
            FROM dbo.CabeceraAlbaranProveedor cap
            LEFT JOIN dbo.Proveedores p ON cap.CodigoProveedor = p.CodigoProveedor
            ORDER BY cap.FechaAlbaran DESC
            """

            cursor = conn.cursor()
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result_dict = {}
                for i, value in enumerate(row):
                    if isinstance(value, datetime):
                        result_dict[columns[i]] = value.strftime('%Y-%m-%d')
                    elif isinstance(value, (int, float)):
                        result_dict[columns[i]] = float(value)
                    elif value is None:
                        result_dict[columns[i]] = ""
                    else:
                        result_dict[columns[i]] = str(value).strip()
                results.append(result_dict)

            return jsonify(results)
        
        return render_template('compras.html')

    except Exception as e:
        logger.error(f"Error al obtener compras: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
