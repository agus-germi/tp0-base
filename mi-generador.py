import sys

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
    return f"""  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - CLI_NOMBRE=Santiago Lionel
      - CLI_APELLIDO=Lorca
      - CLI_DNI=30904465
      - CLI_NACIMIENTO=1999-03-17
      - CLI_NUMERO=7574
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
