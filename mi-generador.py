import sys

def obtener_campo_aleatorio(dni=False, nro=False):
    dnis = ["30904465", "43448326", "23456789", "34567890", "45678901"]
    nros = ["7574", "6531", "9090", "3071", "2106"]
    
    if not hasattr(obtener_campo_aleatorio, "i"):
      obtener_campo_aleatorio.i = 0
    idx = obtener_campo_aleatorio.i % 5 #between 0 y 4 
    obtener_campo_aleatorio.i += 1
    
    if dni:
      return dnis[idx]
    else:
      return nros[idx]


def generar_server(clients):
    """Genera la seccion del servidor en el YAML."""
    return f"""  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - CLIENTS={clients}
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini
"""

def generar_client(i):
    """Genera la seccion de un cliente en el YAML."""
    dni = obtener_campo_aleatorio(True, False)
    nro_apostado = obtener_campo_aleatorio(False, True)

    return f"""  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - CLI_NOMBRE=Santiago Lionel
      - CLI_APELLIDO=Lorca
      - CLI_DNI={dni}
      - CLI_NACIMIENTO=1999-03-17
      - CLI_NUMERO={nro_apostado}
    networks:
      - testing_net
    depends_on:
      - server
    volumes:
      - ./client/config.yaml:/config.yaml
"""

def generar_red():
    """Genera la seccion de redes en el YAML."""
    return """networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

def generar_compose(filename, clients):
    """Genera todo el docker-compose.yaml y lo guarda en archivo."""
    compose = "name: tp0\nservices:\n"
    compose += generar_server(clients)

    for i in range(1, clients + 1):
        compose += generar_client(i)

    compose += generar_red()

    with open(filename, "w") as f:
        f.write(compose)

    print(f"Archivo '{filename}' generado con {clients} clientes.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 mi-generador.py <archivo-salida> <cantidad-clientes>")
        sys.exit(1)

    filename = sys.argv[1]
    clients = int(sys.argv[2])
    generar_compose(filename, clients)
