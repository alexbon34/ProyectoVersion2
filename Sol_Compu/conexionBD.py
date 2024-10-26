from py2neo import Graph, Node

def conectar_bd():
    try:
        graph = Graph("bolt://localhost:7687", auth=("neo4j", "Verde2014"))

        result = graph.run("USE proyectodb RETURN 'Conexión Exitosa' AS mensaje").data()
        print(result[0]['mensaje'])
        return graph
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

if __name__ == '__main__':
    conectar_bd()
