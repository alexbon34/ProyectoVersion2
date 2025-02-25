from flask import Flask, get_flashed_messages, jsonify, render_template, redirect, url_for, request, flash
from conexionBD import conectar_bd 
from py2neo import Graph, Node 
import os
import csv

#ALLOWED_EXTENSIONS = {'txt','csv', 'xlsx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

graph = conectar_bd()

#la página principal
@app.route('/')
def menu_principal():
    return render_template('menu_principal.html')


#CARGA DE DATOS
@app.route('/carga_datos')
def carga_datos():
    return render_template('carga_datos.html')

#Borrar base de datos     LISTO
@app.route('/borrar_base_datos', methods=['POST'])
def borrar_base_datos():
    try:
        query = """
        MATCH (n) DETACH DELETE n
        """
        graph.run(query)
        flash('La BASE DE DATOS ha sido eliminada exitosamente.', 'success') #aqui no me esta funcionando el mensaje

    except Exception as e:
        flash(f'Error al agregar evento: {e}', 'danger')

    return redirect(url_for('carga_datos'))

@app.route('/cargar_relaciones', methods=['POST'])
def cargar_relaciones():
    try:
        #relacionar los Creadores con 
        pass
    except Exception as e:
        flash(f'ERROR <Relaciones no creadas>')


#Cargas archivo GEMINI_API_COMPETITION
@app.route('/cargar_Gemini_API', methods=['POST'])
def cargar_Gemini_API():
    if 'Gemini' not in request.files:
        flash('No se ha seleccionado ningún archivo', 'danger')
        return redirect(url_for('carga_datos'))

    archivo = request.files['Gemini']
#   print(archivo)

    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
        archivo.save(file_path)
        print(f'Archivo guardado correctamente en {file_path}') 
    except Exception as e:
        print(f'Error al guardar el archivo: {e}')
        flash(f'Error al guardar el archivo: {e}', 'danger')
        return redirect(url_for('carga_datos'))

    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:            
            reader = csv.DictReader(csvfile)
            for row in reader:
                built_with_raw = row.get('Built With', '') 
                tecnologias_list = [tech.strip() for tech in built_with_raw.split(',')]  # Crear lista de tecnologías sin espacios extra
                print(f"Tecnologías procesadas: {tecnologias_list}")

                for tecnologia in tecnologias_list:
                    if tecnologia:  # Asegurarse de que no sea una cadena vacía
                        # Verificar si el nodo ya existe para esta tecnología individual
                        existe_tecnologia = graph.evaluate("MATCH (t:Tecnologias {Built_With: $tecnologia}) RETURN t", tecnologia=tecnologia)
                        print(f"Verificando tecnología: '{tecnologia}' - Existe: {'Sí' if existe_tecnologia else 'No'}")

                        if not existe_tecnologia:
                            try:
                                # Crear nodo de tecnología individual
                                tecnologias = Node("Tecnologias", Built_With=tecnologia)
                                graph.create(tecnologias)
                                print(f"Tecnología creada: {tecnologia}")
                            except Exception as e:
                                flash(f'Error al crear nodo de Tecnologías: {e}', 'danger')
                        else:
                            print(f"La tecnología '{tecnologia}' ya existe. No se creará un duplicado.")                         
            
        #vuelvo abrir el archivo       
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)      
            #creo el nodito de Aplicaciones            
            for row in reader:
                Title = row.get('Title', '')  # descripcion
                Built_With = row.get('Built With', '')
                By = row.get('By', '')   
                aplicacion_list = [tech.strip() for tech in Title.split(',')]   

                for apps in aplicacion_list:
                    if apps:
                        existe_tecnologia = graph.evaluate("MATCH (a:Aplicaciones {Title: $Title}) RETURN a", Title=Title)

                        if not existe_tecnologia:
                            try:
                                aplicaciones = Node("Aplicaciones", Title=Title, Built_With=Built_With, By=By)
                                graph.create(aplicaciones)
                            except Exception as e:
                                flash(f'Error al crear nodo de Aplicaciones: {e}', 'danger')
                        else:
                            print(f"El nodo de Aplicaciones con Title '{Title}' ya existe. No se creará un duplicado.")


        #vuelvo abror el archivo para procesarlo.                 
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            print("Procesando Creadores")
            reader = csv.DictReader(csvfile)
            #creo el nodito de Creadores
            for row in reader:
                Title = row.get('Title', '')
                By = row.get('By', '')
                Location = row.get('Location', '')

                print(f"Procesando Creadores - Title: {Title}, By: {By}")
                if not graph.evaluate(f"MATCH (c:Creadores {{By: '{By}'}}) RETURN c"):
                    try:
                        creadores = Node("Creadores", Title=Title, By=By, Location=Location)
                        graph.create(creadores)
                    except Exception as e:
                        flash(f'Error al crear nodo de Creadores: {e}', 'danger')
                else:
                    print(f"El nodo con By '{By}' ya existe. No se creará un duplicado.")

        #esto es escencial para simplemente crear los noditos de la region
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            print("Procesando REGIONES")
            for row in reader:
                Location = row.get('Location', '')
                location_list = [tech.strip() for tech in Location.split(',')]   
    
                for locs in location_list:
                    if locs:  # Asegúrate de que no sea una cadena vacía
                        # Verificar si el nodo ya existe para esta región
                        existe_region = graph.evaluate("MATCH (l:Regiones {Location: $Location}) RETURN l", Location=locs)
                        
                        if not existe_region:  # Si la región no existe, crearla
                            try:
                                regiones = Node("Regiones", Location=locs)  # Cambié Location a locs
                                graph.create(regiones)
                                print(f"Nodo de Regiones creado: {locs}")
                            except Exception as e:
                                flash(f'Error al crear nodo de Regiones: {e}', 'danger')
                        else:
                            print(f"El nodo de Regiones con Location '{locs}' ya existe. No se creará un duplicado.")
    
    
            
        flash('Nodos cargados exitosamente en la base de datos.', 'success')
    except Exception as e:
        print("Creo que entro aqui al except")
        flash(f'Error al procesar el archivo: {e}', 'danger')

    return redirect(url_for('carga_datos'))



@app.route('/agregar_nodo_aplicaciones', methods=['POST'])
def agregar_nodo_aplicaciones():
    title = request.form['title']
    What_it_Does = request.form['What_it_Does']
    Built_With = request.form['Built_With']
    try:
        query = """
        CREATE (g:Gemini {
            title: $title, 
            What_it_Does: $What_it_Does,
            Built_With: $Built_With,
        })
        """
        graph.run(query,title=title,What_it_Does=What_it_Does,
                  Built_With=Built_With)
        flash(f'Gemini {title} ha sido agregado exitosamente.', 'success') #aqui no me esta funcionando el mensaje

    except Exception as e:
        flash(f'Error al agregar evento: {e}', 'danger')

    return redirect(url_for('CRUD'))

@app.route('/editar_nodo', methods=['POST'])
def editar_nodo():
    pass


@app.route('/leer_nodo', methods=['POST'])
def leer_nodo():
    pass

@app.route('/borrar_nodo', methods=['POST'])
def borrar_nodo():
    pass



if __name__ == '__main__':
    app.run(debug=True, port=8080)


