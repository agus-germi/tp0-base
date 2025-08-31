import socket
import logging
import threading
from common.utils import Bet, store_bets, load_bets, has_won

HEADER_LENGTH = 4

#protejo el acceso al archivo

class Server:
    def __init__(self, port, listen_backlog, num_clients):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._is_running = True

        # -- ej7
        self._num_clients = num_clients
        self._agencies_done = {}
        self._lock = threading.Lock() #protejo estructuras compartidas
        self._all_done = threading.Condition(self._lock)
        self._file_lock = threading.Lock()

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        coordinator = threading.Thread(target=self._wait_for_all, daemon=True) #coordinador espera a que todas las agencias manden END
        coordinator.start()

        while self._is_running:
            try:
                client_sock = self.__accept_new_connection()
                thread = threading.Thread(target=self.__handle_client_connection, args=(client_sock,), daemon=True)
                thread.start()
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

    def _recv_all(self, client_sock, n):
        data = b''
        while len(data) < n:
            chunk = client_sock.recv(n-len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _parse_payload(self, payload):
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

    def _check_end_message(self, payload, client_sock):
        try:
            text = payload.decode("utf-8").strip()
            if text.startswith("END|"):
                agency = int(text.split("|")[1])
                logging.info(f"action: end_message_received | result: success | agency: {agency}")
                with self._all_done:
                    self._agencies_done[agency] = client_sock
                    if len(self._agencies_done) == self._num_clients:
                        self._all_done.notify_all()  # despierta al hilo que espera el sorteo

                return agency
        except Exception as e:
            logging.error(f"action: check_end_message | result: fail | error: {e}")
        return None

    def _calculate_winners(self):
        winners_by_agency = {}

        with self._file_lock:
            for bet in load_bets():
                if has_won(bet):
                    #asumo que puede ganar mas de uno por agencia
                    winners_by_agency.setdefault(bet.agency, []).append(bet.document) 
        return winners_by_agency

    def _send_results(self, winners: dict):
        with self._lock:
            agencies_done = dict(self._agencies_done)

        for agency in agencies_done:
            sock = agencies_done[agency]
            results = winners.get(agency, [])
            msg = "\n".join(results) + "\nWINNERS_END\n"
            try:
                sock.sendall(msg.encode("utf-8"))
            except Exception as e:
                logging.error(f"action: send_winners | result: fail | agency: {agency} | error: {e}")
            finally:
                self._agencies_done.clear()
                sock.close()
    
    def _wait_for_all(self):

        with self._all_done:
            while len(self._agencies_done) < self._num_clients:
                self._all_done.wait()

        #cuando sale del wait ya están todas las agencias
        winners = self._calculate_winners()
        logging.info("action: sorteo | result: success")
        logging.info("action: send_winners | result: in_progress")
        self._send_results(winners)

    def __handle_client_connection(self, client_sock):
        """
        Read multiple messages from a specific client socket until the client disconnects.
        """
        client_addr = client_sock.getpeername()
        try:
            while True:
                header = self._recv_all(client_sock, HEADER_LENGTH)
                if not header:
                    logging.info(f"action: handle_client | result: fail | status: disconnected")
                    break
                msg_length = (header[0] << 24) | (header[1] << 16) | (header[2] << 8) | header[3]
                logging.info(f'action: header_received | result: success | msg_length: {msg_length}')

                data = self._recv_all(client_sock, msg_length)
                if not data:
                    break
                
                client_agency = self._check_end_message(data, client_sock)
                if client_agency:
                    break

                bets, has_error, total_bets = self._parse_payload(data)
                if has_error:
                    logging.error(f"action: apuesta_recibida | result: fail | cantidad: {total_bets}")
                    client_sock.sendall(b"ERROR\n")
                else:
                    with self._file_lock:
                        store_bets(bets)                    
                    logging.info(f"action: apuesta_recibida | result: success | cantidad: {total_bets}")
                    logging.info(f"action: apuesta_almacenada | result: success")
                    client_sock.sendall(b"success\n")

        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            logging.info(f"action: handle_client | result: success | client: {client_addr} | status: finished")


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
