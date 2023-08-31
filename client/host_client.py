# the part which connected with Minecraft
import queue
import socket
import threading
import logging

import client

_log = client._log

if client.file_log:
    _format_msg = "[%(levelname)s] [%(asctime)s] [%(funcName)s] %(message)s"
    _format_time = "%H:%M:%S"
    _formatter = logging.Formatter(_format_msg, _format_time)

    _file_handler = logging.FileHandler("HostClientLog.log", mode='a', encoding='utf-8')
    _file_handler.setFormatter(_formatter)
    _file_handler.setLevel(logging.DEBUG)
    _log.addHandler(_file_handler)

    with open("HostClientLog.log", mode='a+', encoding='utf_8') as log_file:
        log_file.write("===================================LOG START===================================\n")


class HostClient(client.Client):

    def __init__(self, server_addr: tuple[str, int], mc_port: int):
        super().__init__(server_addr)

        self._me_port = mc_port
        self._virtual_client: socket.socket
        self._send_func_alive: bool | None = None
        self._get_func_alive: bool | None = None

    def __connect_mc_server(self):
        self._virtual_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._virtual_client.connect((socket.gethostname(), self._me_port))
            _log.info("Mc connected")
        except ConnectionError as error:
            _log.error(f"Error: failed to connect with mc({error})")
            raise

    def __send_java_data(self):
        """send data to java"""
        self._send_func_alive = True

        try:
            while True:
                try:
                    data = self._data_queue_2.get(timeout=2)

                except queue.Empty:
                    if self._get_func_alive is False:
                        self._send_func_alive = False
                        _log.warning("__send_java_data is down for get func(timeout)")
                        break
                    else:
                        if client.ticker(5):
                            pass
                            # self._virtual_client.send(b'\x00')
                        continue

                if self._get_func_alive is False:
                    self._send_func_alive = False
                    _log.warning("__send_java_data is down for get func")
                    break

                self._virtual_client.sendall(data)

                if data:
                    _log.debug(data)

        except ConnectionError as error:
            _log.error(f"{error} from send_java_data")
            self._send_func_alive = False

    def __get_local_data(self):
        """get data from java"""
        self._get_func_alive = True

        try:
            while True:
                try:
                    data = self._virtual_client.recv(client.MAX_LENGTH)
                except TimeoutError:
                    if self._send_func_alive is False:
                        self._get_func_alive = False
                        _log.warning("__get_local_data is down for send func(timeout)")
                        break
                    else:
                        continue

                if self._send_func_alive is False:
                    self._get_func_alive = False
                    _log.warning("__get_local_data is down for send func")
                    break

                self._data_queue_1.put(data)

                if data:
                    _log.debug(data)

        except ConnectionError as error:
            _log.error(f"{error} from send_java_data")
            self._get_func_alive = False

    def virtual_client_main(self):  # FIXME: can not run properly
        functions = [self.__send_java_data, self.__get_local_data]

        while True:
            self.__connect_mc_server()
            self._virtual_client.settimeout(2)

            threads = [threading.Thread(target=func) for func in functions]

            for thd in threads:
                thd.start()

            for thd in threads:
                thd.join()

            self._virtual_client.settimeout(None)

            _log.info("Virtual client is down!")
            input('type [ENTER] to restart> ')
            _log.info("Virtual client restart...")
