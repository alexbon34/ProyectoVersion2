from flask import Flask, get_flashed_messages, jsonify, render_template, redirect, url_for, request, flash
from conexionBD import conectar_bd 
from py2neo import Graph, Node, Relationship
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
        #aqui creo los noditos de tecnologia
        # Aquí creo los noditos de tecnología
        with open(file_path, newline='', encoding='utf-8') as csvfile:            
            reader = csv.DictReader(csvfile)
            for row in reader:
                built_with_raw = row.get('Built With', '') 
                tecnologias_list = [tech.strip() for tech in built_with_raw.split(',')]  # Crear lista de tecnologías sin espacios extra
                By = row.get('By', '').strip()  # Obtener el creador de la fila
                for tecnologia in tecnologias_list:
                    if tecnologia:  # Asegurarse de que no sea una cadena vacía
                        existe_tecnologia = graph.evaluate("MATCH (t:Tecnologias {Built_With: $tecnologia}) RETURN t", tecnologia=tecnologia)
                        if not existe_tecnologia:
                            try:
                                # Crear el nodo de tecnología con el campo 'By'
                                tecnologias = Node("Tecnologias", Built_With=tecnologia, By=By)
                                graph.create(tecnologias)
                            except Exception as e:
                                flash(f'Error al crear nodo de Tecnologías: {e}', 'danger')
                        else:
                            print(f"La tecnología '{tecnologia}' ya existe. No se creará un duplicado.")

        #vuelvo abrir el archivo y creo los noditos de aplicacion      
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

        # Procesando Creadores
        with open(file_path, newline='', encoding='utf-8') as csvfile:
           print("Procesando Creadores")
           reader = csv.DictReader(csvfile)

           for row in reader:
               Title = row.get('Title', '')
               By = row.get('By', '')  # Obtener el campo de creadores
               Location = row.get('Location', '')

               # Separar los creadores por comas
               if By:
                   creadores = [creator.strip() for creator in By.split(',')]  # Lista de creadores

                   for creator in creadores:
                       if creator:  # Asegúrate de que no esté vacío
                           print(f"Procesando Creador - Title: {Title}, By: {creator}")
                           if not graph.evaluate(f"MATCH (c:Creadores {{By: '{creator}'}}) RETURN c"):
                               try:
                                   creadores_node = Node("Creadores", Title=Title, By=creator, Location=Location)
                                   graph.create(creadores_node)
                               except Exception as e:
                                   flash(f'Error al crear nodo de Creadores: {e}', 'danger')
                       else:
                           print(f"Creador vacío encontrado para la aplicación '{Title}'.")

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
    
        # Crear relaciones entre Creadores y Regiones
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                By = row.get('By', '').strip()
                Location = row.get('Location', '').strip()
                if not By or not Location:  # Verificar que tanto el creador como la ubicación no estén vacíos
                    continue
                location_list = [loc.strip() for loc in Location.split(',')]
                creadores_list = [creator.strip() for creator in By.split(',')] if By else []
                for creador_name in creadores_list:
                    creador = graph.evaluate("MATCH (c:Creadores {By: $by}) RETURN c", by=creador_name)
                    if creador:
                        for loc in location_list:
                            region = graph.evaluate("MATCH (r:Regiones {Location: $loc}) RETURN r", loc=loc)
                            if region:
                                if not graph.evaluate("""
                                    MATCH (c:Creadores {By: $by})-[rel:LOCATED_IN]->(r:Regiones {Location: $loc}) RETURN rel
                                """, by=creador_name, loc=loc):
                                    graph.create(Relationship(creador, "LOCATED_IN", region))
                                    print(f"Relación 'LOCATED_IN' creada entre el creador '{creador_name}' y la región '{loc}'.")
                            else:
                                print(f"No se encontró la región para '{loc}', por lo que no se puede crear la relación.")
                    else:
                        print(f"No se encontró el creador '{creador_name}'.")
        
        # Crear relación entre Aplicaciones y Creadores
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            print("Creando relaciones entre Aplicaciones y Creadores")
            reader = csv.DictReader(csvfile)
            for row in reader:
                Title = row.get('Title', '')
                By = row.get('By', '')
                creadores_list = [creator.strip() for creator in By.split(',')] if By else [None]

                for creator in creadores_list:
                    if creator is None:
                        print(f"No se ha proporcionado creador para la aplicación '{Title}'. No se creará relación.")
                    else:
                        aplicacion = graph.evaluate("MATCH (a:Aplicaciones {Title: $Title}) RETURN a", Title=Title)
                        creador_node = graph.evaluate("MATCH (c:Creadores {By: $creator}) RETURN c", creator=creator)
                        if aplicacion and creador_node:
                            if not graph.evaluate("""
                                MATCH (a:Aplicaciones {Title: $Title})-[rel:TIENE]->(c:Creadores {By: $creator}) RETURN rel
                            """, Title=Title, creator=creator):
                                graph.create(Relationship(aplicacion, "TIENE", creador_node))
                                print(f"Relación 'TIENE' creada entre la aplicación '{Title}' y el creador '{creator}'.")
                        else:
                            if not aplicacion:
                                print(f"No se encontró la aplicación '{Title}'.")
                            if not creador_node:
                                print(f"No se encontró el creador '{creator}'.")


        # Crear relaciones entre Creadores y Tecnologías
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                built_with_raw = row.get('Built With', '').strip()  # Obtener la columna "Built With"
                By = row.get('By', '').strip()  # Obtener el nombre del creador
                # Crear una lista de creadores eliminando espacios en blanco
                creadores_list = [creator.strip() for creator in By.split(',')] if By else []

                # Crear una lista de tecnologías eliminando espacios en blanco
                tecnologias_list = [tech.strip() for tech in built_with_raw.split(',')] if built_with_raw else []

                # Iterar sobre la lista de tecnologías
                for tecnologia in tecnologias_list:
                    if tecnologia:  # Asegurarse de que no sea una cadena vacía
                        tecnologia_node = graph.evaluate("MATCH (t:Tecnologias {Built_With: $tecnologia}) RETURN t", tecnologia=tecnologia)

                        # Verificar si la tecnología existe
                        if tecnologia_node:
                            # Iterar sobre los creadores y crear relaciones
                            for creador_name in creadores_list:
                                creador = graph.evaluate("MATCH (c:Creadores {By: $by}) RETURN c", by=creador_name)

                                if creador:
                                    # Verificar que la relación no exista
                                    if not graph.evaluate("""
                                        MATCH (c:Creadores {By: $by})-[rel:TRABAJA_CON]->(t:Tecnologias {Built_With: $tecnologia}) 
                                        RETURN rel
                                    """, by=creador_name, tecnologia=tecnologia):
                                        # Crear la relación TRABAJA_CON
                                        graph.create(Relationship(creador, "TRABAJA_CON", tecnologia_node))
                                        print(f"Relación 'TRABAJA_CON' creada entre el creador '{creador_name}' y la tecnología '{tecnologia}'.")
                                else:
                                    print(f"No se encontró el creador '{creador_name}'.")
                        else:
                            print(f"No se encontró la tecnología '{tecnologia}'.")

        # Crear relaciones entre Aplicaciones y Tecnologías
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Title = row.get('Title', '').strip()
                built_with_raw = row.get('Built With', '').strip()
                tecnologias_list = [tech.strip() for tech in built_with_raw.split(',')] if built_with_raw else []

                aplicacion = graph.evaluate("MATCH (a:Aplicaciones {Title: $title}) RETURN a", title=Title)

                for tecnologia in tecnologias_list:
                    if tecnologia:
                        tecnologia_node = graph.evaluate("MATCH (t:Tecnologias {Built_With: $tecnologia}) RETURN t", tecnologia=tecnologia)
                        if aplicacion and tecnologia_node:
                            if not graph.evaluate("""
                                MATCH (a:Aplicaciones {Title: $title})-[rel:UTILIZA]->(t:Tecnologias {Built_With: $tecnologia}) RETURN rel
                            """, title=Title, tecnologia=tecnologia):
                                graph.create(Relationship(aplicacion, "UTILIZA", tecnologia_node))
                                print(f"Relación 'UTILIZA' creada entre la aplicación '{Title}' y la tecnología '{tecnologia}'.")
                        else:
                            if not aplicacion:
                                print(f"No se encontró la aplicación '{Title}'.")
                            if not tecnologia_node:
                                print(f"No se encontró la tecnología '{tecnologia}'.")




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


