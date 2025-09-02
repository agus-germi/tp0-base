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

    def parse_payload(self, payload):
        """
        Parses a payload string containing bet information and returns a list of Bet objects, an error flag, and the total number of bets   
        The payload is expected to be a string where the first line contains comma-separated bets. Each bet is represented as six fields separated by '|':
        first_name|last_name|document|birthdate|number|agency   
        """
        msg = payload.split('\n')
        bets = []
        has_error = False
        total_bets = 0

        for line in msg[0].split(','):
            line = line.strip()
            if not line:
                continue
            total_bets += 1
            bet_info = line.split('|')
            if len(bet_info) != 6:
                has_error = True
                continue
            nombre, apellido, dni, nacimiento, numero, agencia = bet_info
            bet = Bet(
                agency=agencia,
                first_name=nombre,
                last_name=apellido,
                document=dni,
                birthdate=nacimiento,
                number=numero
            )
            bets.append(bet)
        return bets, has_error, total_bets

        

    def __handle_client_connection(self, client_sock):
        """
        Read multiple messages from a specific client socket until the client disconnects.
        """
        try:
            while True:
                msg = self.recv_message(client_sock)
                if not msg:
                    client_sock.close()
                    return

                bets, has_error, total_bets = self.parse_payload(msg)
                if has_error:
                    logging.error(f"action: apuesta_recibida | result: fail | cantidad: {total_bets}")
                    client_sock.sendall(b"ERROR\n")
                else:
                    store_bets(bets)
                    logging.info(f"action: apuesta_recibida | result: success | cantidad: {total_bets}")
                    logging.info(f"action: apuesta_almacenada | result: success")
                    client_sock.sendall(b"ACK\n")

        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
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
