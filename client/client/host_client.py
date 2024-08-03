# the part connected with Minecraft
import queue
import socket
import sys
import threading

from . import client, tool


class HostClient(client.Client):

    def __init__(self, server_addr: tuple[str, int], local_port: int, is_crypt: bool, logger):
        super().__init__(server_addr, is_crypt, logger)

        self.local_port = local_port
        self.__virtual_client: socket.socket | None = None

    def __connect_local(self):
        """connect with local as a guest"""
        self.__virtual_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.__virtual_client.connect((socket.gethostname(), self.local_port))
            self.log.info("local server connected")

        except ConnectionRefusedError:
            self.log.error(f"failed to connect with local server: connection refused")
            raise

    def __send_local_data(self):
        """send data to local"""
        try:
            while True:
                try:
                    data = self._queue_to_local.get(timeout=1)

                except queue.Empty:
                    continue

                while True:
                    try:
                        self.__virtual_client.sendall(data)
                        break
                    except TimeoutError:
                        pass

                msg = tool.message(data, client.log_content, client.log_length)
                if msg:
                    self.log.debug(msg)

        except ConnectionError as error:
            self.log.error(f"{error}")
        except SystemExit:
            self.log.debug("exit")

    def __get_local_data(self):
        """get data from local"""
        try:
            while True:
                try:
                    data = self.__virtual_client.recv(client.MAX_LENGTH)
                except TimeoutError:
                    continue

                if data:
                    self._queue_to_server.put(data)
                else:
                    raise ConnectionError

                msg = tool.message(data, client.log_content, client.log_length)
                if msg:
                    self.log.debug(msg)

        except ConnectionError as error:
            self.log.error(f"{error}")
        except SystemExit:
            self.__virtual_client.shutdown(socket.SHUT_RDWR)
            self.__virtual_client.close()
            self.log.debug("exit and close socket")

    def local_client_main(self, daemon=False) -> list[threading.Thread]:
        functions = [self.__send_local_data, self.__get_local_data]

        try:
            self.__connect_local()
        except ConnectionRefusedError:
            sys.exit(-1)

        self.__virtual_client.settimeout(3)
        threads = [threading.Thread(target=func, daemon=daemon) for func in functions]

        for thd in threads:
            thd.start()

        return threads
