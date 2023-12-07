#--------------------------------------------------------------------
# Instalar con pip install Flask
from flask import Flask, request, jsonify, render_template
#from flask import request

# Instalar con pip install flask-cors
from flask_cors import CORS

# Instalar con pip install mysql-connector-python
import mysql.connector

# Si es necesario, pip install Werkzeug
from werkzeug.utils import secure_filename

# No es necesario instalar, es parte del sistema standard de Python
import os
import time
#--------------------------------------------------------------------



app = Flask(__name__)
CORS(app)  # Esto habilitará CORS para todas las rutas

#--------------------------------------------------------------------
class Kits:
    #----------------------------------------------------------------
    # Constructor de la clase
    def __init__(self, host, user, password, database):
        # Primero, establecemos una conexión sin especificar la base de datos
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()

        # Intentamos seleccionar la base de datos
        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            # Si la base de datos no existe, la creamos
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

        # Una vez que la base de datos está establecida, creamos la tabla si no existe
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            codigo INT,
            titulo VARCHAR(255) NOT NULL,
            descripcion VARCHAR(255) NOT NULL,
            descripcion_detallada VARCHAR(255) NOT NULL,
            precio DECIMAL(10, 2) NOT NULL,
            imagen VARCHAR(255) NOT NULL,
            nivel INT(1) NOT NULL)''')
        self.conn.commit()

        # Cerrar el cursor inicial y abrir uno nuevo con el parámetro dictionary=True
        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)

    #----------------------------------------------------------------
    def consultar_producto(self, codigo):
        # Consultamos un producto a partir de su código
        self.cursor.execute(f"SELECT * FROM productos WHERE codigo = {codigo}")
        return self.cursor.fetchone()

    #----------------------------------------------------------------
    def agregar_producto(self, codigo, titulo, descripcion, descripcion_detallada, precio, imagen, nivel):
        # Verificamos si ya existe un producto con el mismo código

        producto_existe = self.consultar_producto(codigo)
        if producto_existe:
            return False


        sql = "INSERT INTO productos (codigo, titulo, descripcion, descripcion_detallada, precio, imagen, nivel) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        valores = (codigo, titulo, descripcion, descripcion_detallada, precio, imagen, nivel)

        self.cursor.execute(sql, valores)
        self.conn.commit()
        return True



    #----------------------------------------------------------------
    def modificar_producto(self, codigo, new_titulo, new_descripcion, new_descripcion_detallada, new_precio, new_imagen, new_nivel):
        sql = "UPDATE productos SET titulo = %s, descripcion = %s, descripcion_detallada = %s, precio = %s, imagen = %s, nivel = %s WHERE codigo = %s"
        valores = (new_titulo, new_descripcion, new_descripcion_detallada, new_precio, new_imagen, new_nivel, codigo)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0

    #----------------------------------------------------------------
    def listar_productos(self):
        self.cursor.execute("SELECT * FROM productos")
        productos = self.cursor.fetchall()
        return productos

    #----------------------------------------------------------------
    def eliminar_producto(self, codigo):
        # Eliminamos un producto de la tabla a partir de su código
        self.cursor.execute(f"DELETE FROM productos WHERE codigo = {codigo}")
        self.conn.commit()
        return self.cursor.rowcount > 0

    #----------------------------------------------------------------
    def mostrar_producto(self, codigo):
        # Mostramos los datos de un producto a partir de su código
        producto = self.consultar_producto(codigo)
        if producto:
            print("-" * 40)
            print(f"Código.....: {producto['codigo']}")
            print(f"Titulo: {producto['titulo']}")
            print(f"Descripción: {producto['descripcion']}")
            print(f"Descripcion_detallada...: {producto['descripcion_detallada']}")
            print(f"Precio.....: {producto['precio']}")
            print(f"Imagen.....: {producto['imagen']}")
            print(f"Nivel..: {producto['nivel']}")
            print("-" * 40)
        else:
            print("Producto no encontrado.")


#--------------------------------------------------------------------
# Cuerpo del programa
#--------------------------------------------------------------------
# Crear una instancia de la clase Kits
#kits = Kits(host='localhost', user='root', password='root', database='productos')
kits = Kits(host='RogerLopesierra1.mysql.pythonanywhere-services.com', user='RogerLopesierra1', password='root12345@', database='RogerLopesierra1$productos')

# kits.agregar_producto(1, "Televisor 25",11, 340000, "tele.jpg",1)
# kits.agregar_producto(2, "Notebook",11, 740000, "compu.jpg",1)
# kits.agregar_producto(3, "Mouse tres botones",11, 3400, "mouse.jpg",1)


# Carpeta para guardar las imagenes.
#RUTA_DESTINO = './static/imagenes/'

#Al subir al servidor, deberá utilizarse la siguiente ruta. USUARIO debe ser reemplazado por el nombre de usuario de Pythonanywhere
RUTA_DESTINO = '/home/RogerLopesierra1/mysite/static/imagenes'


#--------------------------------------------------------------------
# Listar todos los productos
#--------------------------------------------------------------------
#La ruta Flask /productos con el método HTTP GET está diseñada para proporcionar los detalles de todos los productos almacenados en la base de datos.
#El método devuelve una lista con todos los productos en formato JSON.
@app.route("/productos", methods=["GET"])
def listar_productos():
    productos = kits.listar_productos()
    return jsonify(productos)


#--------------------------------------------------------------------
# Mostrar un sólo producto según su código
#--------------------------------------------------------------------
#La ruta Flask /productos/<int:codigo> con el método HTTP GET está diseñada para proporcionar los detalles de un producto específico basado en su código.
#El método busca en la base de datos el producto con el código especificado y devuelve un JSON con los detalles del producto si lo encuentra, o None si no lo encuentra.
@app.route("/productos/<int:codigo>", methods=["GET"])
def mostrar_producto(codigo):
    producto = kits.consultar_producto(codigo)
    if producto:
        return jsonify(producto), 201
    else:
        return "Producto no encontrado", 404


#--------------------------------------------------------------------
# Agregar un producto
#--------------------------------------------------------------------
@app.route("/productos", methods=["POST"])
#La ruta Flask `/productos` con el método HTTP POST está diseñada para permitir la adición de un nuevo producto a la base de datos.
#La función agregar_producto se asocia con esta URL y es llamada cuando se hace una solicitud POST a /productos.
def agregar_producto():
    #Recojo los datos del form
    codigo = request.form['codigo']
    titulo = request.form['titulo']
    descripcion = request.form['descripcion']
    descripcion_detallada = request.form['descripcion_detallada']
    precio = request.form['precio']
    imagen = request.files['imagen']
    nivel = request.form['nivel']
    nombre_imagen=""

    # Me aseguro que el producto exista
    producto = kits.consultar_producto(codigo)
    if not producto: # Si no existe el producto...
        # Genero el nombre de la imagen
        nombre_imagen = secure_filename(imagen.filename) #Chequea el nombre del archivo de la imagen, asegurándose de que sea seguro para guardar en el sistema de archivos
        nombre_base, extension = os.path.splitext(nombre_imagen) #Separa el nombre del archivo de su extensión.
        nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}" #Genera un nuevo nombre para la imagen usando un timestamp, para evitar sobreescrituras y conflictos de nombres.

        #Se agrega el producto a la base de datos
        if  kits.agregar_producto(codigo, titulo, descripcion, descripcion_detallada, precio, nombre_imagen, nivel):
            imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))

            #Si el producto se agrega con éxito, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 201 (Creado).
            return jsonify({"mensaje": "Producto agregado correctamente.", "imagen": nombre_imagen}), 201
        else:
            #Si el producto no se puede agregar, se devuelve una respuesta JSON con un mensaje de error y un código de estado HTTP 500 (Internal Server Error).
            return jsonify({"mensaje": "Error al agregar el producto."}), 500

    else:
        #Si el producto ya existe (basado en el código), se devuelve una respuesta JSON con un mensaje de error y un código de estado HTTP 400 (Solicitud Incorrecta).
        return jsonify({"mensaje": "Producto ya existe."}), 400


#--------------------------------------------------------------------
# Modificar un producto según su código
#--------------------------------------------------------------------
@app.route("/productos/<int:codigo>", methods=["PUT"])
#La ruta Flask /productos/<int:codigo> con el método HTTP PUT está diseñada para actualizar la información de un producto existente en la base de datos, identificado por su código.
#La función modificar_producto se asocia con esta URL y es invocada cuando se realiza una solicitud PUT a /productos/ seguido de un número (el código del producto).
def modificar_producto(codigo):
    #Se recuperan los nuevos datos del formulario
    #codigo, titulo, descripcion, descripcion_detallada, precio, imagen, nivel
    new_titulo = request.form.get("titulo")
    new_descripcion = request.form.get("descripcion")
    new_descripcion_detallada = request.form.get("descripcion_detallada")
    new_precio = request.form.get("precio")
    new_nivel = request.form.get("nivel")
    imagen = request.files['imagen']

    # Procesamiento de la imagen
    nombre_imagen = secure_filename(imagen.filename) #Chequea el nombre del archivo de la imagen, asegurándose de que sea seguro para guardar en el sistema de archivos
    nombre_base, extension = os.path.splitext(nombre_imagen) #Separa el nombre del archivo de su extensión.
    nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}" #Genera un nuevo nombre para la imagen usando un timestamp, para evitar sobreescrituras y conflictos de nombres.

    # Busco el producto guardado
    producto = producto = kits.consultar_producto(codigo)
    if producto: # Si existe el producto...
        imagen_vieja = producto["imagen"]
        # Armo la ruta a la imagen
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

        # Y si existe la borro.
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)

    # Se llama al método modificar_producto pasando el codigo del producto y los nuevos datos.
    if kits.modificar_producto(codigo, new_titulo, new_descripcion, new_descripcion_detallada, new_precio, nombre_imagen, new_nivel):
        #La imagen se guarda en el servidor.
        imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))

        #Si la actualización es exitosa, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 200 (OK).
        return jsonify({"mensaje": "Producto modificado"}), 200
    else:
        #Si el producto no se encuentra (por ejemplo, si no hay ningún producto con el código dado), se devuelve un mensaje de error con un código de estado HTTP 404 (No Encontrado).
        return jsonify({"mensaje": "Producto no encontrado"}), 403



#--------------------------------------------------------------------
# Eliminar un producto según su código
#--------------------------------------------------------------------
@app.route("/productos/<int:codigo>", methods=["DELETE"])
#La ruta Flask /productos/<int:codigo> con el método HTTP DELETE está diseñada para eliminar un producto específico de la base de datos, utilizando su código como identificador.
#La función eliminar_producto se asocia con esta URL y es llamada cuando se realiza una solicitud DELETE a /productos/ seguido de un número (el código del producto).
def eliminar_producto(codigo):
    # Busco el producto en la base de datos
    producto = kits.consultar_producto(codigo)
    if producto: # Si el producto existe, verifica si hay una imagen asociada en el servidor.
        imagen_vieja = producto["imagen"]
        # Armo la ruta a la imagen
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)

        # Y si existe, la elimina del sistema de archivos.
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)

        # Luego, elimina el producto del catálogo
        if kits.eliminar_producto(codigo):
            #Si el producto se elimina correctamente, se devuelve una respuesta JSON con un mensaje de éxito y un código de estado HTTP 200 (OK).
            return jsonify({"mensaje": "Producto eliminado"}), 200
        else:
            #Si ocurre un error durante la eliminación (por ejemplo, si el producto no se puede eliminar de la base de datos por alguna razón), se devuelve un mensaje de error con un código de estado HTTP 500 (Error Interno del Servidor).
            return jsonify({"mensaje": "Error al eliminar el producto"}), 500
    else:
        #Si el producto no se encuentra (por ejemplo, si no existe un producto con el codigo proporcionado), se devuelve un mensaje de error con un código de estado HTTP 404 (No Encontrado).
        return jsonify({"mensaje": "Producto no encontrado"}), 404

#--------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
