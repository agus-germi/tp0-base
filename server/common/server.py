import socket
import logging
from common.utils import Bet, store_bets


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._is_running = True

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self._is_running:
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
            except OSError as e:
                logging.error(f"action: accept_connections | result: fail | error: {e}")
                break
    
    def shutdown(self):
        self._is_running = False
        try:
            self._server_socket.close()
            logging.info("action: close_socket | result: success")
        except Exception as e:
            logging.error(f"action: close_socket | result: fail")

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            data = b''
            while True: #[ ] look for another better way 
                chunk = client_sock.recv(1024) #[ ]1024 enough ?.
                #recv non blocking
                if not chunk:
                    break
                data += chunk
                if b'\n' in chunk: #indicates the end of the message
                    break 

            msg = data.decode('utf-8').strip()
            addr = client_sock.getpeername()

            #deserialize
            try:
                logging.info(f'MENSAJEEEE {msg}')
                nombre, apellido, dni, nacimiento, numero, agencia = msg.split('|')
            except ValueError:
                logging.error(f'action: receive_message | result: fail')

            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')

            bet = Bet(
                agency=agencia, #[ ] check what has to go in nro agency 
                first_name=nombre,
                last_name=apellido,
                document=dni,
                birthdate=nacimiento,
                number=numero
            )
            store_bets([bet])
            logging.info(f"action: apuesta_almacenada | result: success | dni: {dni} | numero: {numero}")

            #send client a confirmation https://docs.python.org/3/library/socket.html#socket.socket.sendall
            client_sock.sendall(b"success\n")


        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
