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

    def recv_all(self, client_sock, n):
        data = b''
        while len(data) < n:
            chunk = client_sock.recv(n-len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def parse_payload(self, payload):
        msg = payload.decode('utf-8').strip().split('\n')
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
                header = self.recv_all(client_sock, HEADER_LENGTH)
                if not header:
                    break
                msg_length = (header[0] << 24) | (header[1] << 16) | (header[2] << 8) | header[3]
                logging.info(f'action: header_received | result: success | msg_length: {msg_length}')

                data = self.recv_all(client_sock, msg_length)
                if not data:
                    break

                bets, has_error, total_bets = self.parse_payload(data)
                if has_error:
                    logging.error(f"action: apuesta_recibida | result: fail | cantidad: {total_bets}")
                    client_sock.sendall(b"ERROR\n")
                else:
                    store_bets(bets)
                    logging.info(f"action: apuesta_recibida | result: success | cantidad: {total_bets}")
                    logging.info(f"action: apuesta_almacenada | result: success")
                    client_sock.sendall(b"success\n")

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
