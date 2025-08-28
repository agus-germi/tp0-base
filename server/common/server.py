import socket
import logging
from common.utils import Bet, store_bets

HEADER_LENGTH = 4

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

    def recv_all(self, client_sock, n):
        data = b''
        while len(data) < n:
            chunk = client_sock.recv(n-len(data))

            if not chunk:
                return None
            data += chunk
        return data


    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            
            header = self.recv_all(client_sock, HEADER_LENGTH)
            if not header:
                client_sock.close()
                return
            
            msg_length = (header[0] << 24) | (header[1] << 16) | (header[2] << 8) | header[3]
            data = self.recv_all(client_sock, msg_length)
            if not data:
                client_sock.close()
                return
            
            msg = data.decode('utf-8').strip()
            addr = client_sock.getpeername()
            campos = msg.split('|')

            if len(campos) != 6:
                logging.error(f'action: receive_message | result: fail | error: formato de mensaje incorrecto')
                client_sock.close()
                return
            nombre, apellido, dni, nacimiento, numero, agencia = campos

            logging.info(f'action: receive_message | result: success | ip: {addr[0]} ')

            bet = Bet(
                agency=agencia,
                first_name=nombre,
                last_name=apellido,
                document=dni,
                birthdate=nacimiento,
                number=numero
            )
            store_bets([bet])
            logging.info(f"action: apuesta_almacenada | result: success | dni: {dni} | numero: {numero}")
            logging.info("SERVER ANTES DEL SENDALL")
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
