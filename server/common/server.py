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
        """
        Gracefully shuts down the server by stopping the main loop and closing the server socket.
        Sets the _is_running flag to False to exit the main loop, then attempts to close the server socket.
        Logs the result of the socket closure.
        """
        self._is_running = False
        try:
            self._server_socket.close()
            logging.info("action: close_socket | result: success")
        except Exception as e:
            logging.error(f"action: close_socket | result: fail")

    def recv_message(self, client_sock):
        """
        Receives a message from the given client socket.

        This method first reads a fixed-size header to determine the length of the incoming message.
        It then reads the exact number of bytes specified by the header.
        If the connection is closed or an error occurs before the full message is received, it returns None.
        On success, it returns the decoded message as a UTF-8 string.

        Args:
            client_sock (socket.socket): The client socket to read from.

        Returns:
            str or None: The received message as a string, or None if an error or disconnect occurs.
        """
        try:
            header_data = client_sock.recv(HEADER_LENGTH)
            if len(header_data) < HEADER_LENGTH:
                return None

            msg_length = int.from_bytes(header_data, byteorder='big')
            logging.info(f"largo mensaje {msg_length}")
            data = b''
            while len(data) < msg_length:
                chunk = client_sock.recv(msg_length - len(data))
                if not chunk:
                    return None
                data += chunk

            return data.decode('utf-8').strip()
        except OSError as e:
            logging.error(f"action: recv_message | result: fail | error: {e}", exc_info=True)
            return None


    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            
            msg = self.recv_message(client_sock)
            if not msg:
                client_sock.close()
                return
            
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
            #send client a confirmation https://docs.python.org/3/library/socket.html#socket.socket.sendall
            client_sock.sendall(b"ACK\n")


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
