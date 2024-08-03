# the part connected with a server
import sys
import queue
import socket
import logging
import threading
import typing

from . import tool

MAX_LENGTH: int | None = None

#  log config
log_length: bool | None = None
log_content: bool | None = None


class AdvancedSocket(socket.socket):

    def __init__(self, family=-1, stype=-1, log=None):
        super().__init__(family, stype)
        self.log = log

        self.__tcp_data_analyser = tool.TCPDataAnalyser(log=self.log)
        self.__tcp_data_packer = tool.TCPDataPacker(log=self.log)

    def recv_all(self, max_length=None) -> typing.Iterator[bytes]:
        """recv data and divide it into individuals in order"""
        self.settimeout(5)
        while True:
            try:
                if max_length:
                    data = self.recv(max_length)
                else:
                    data = self.recv(MAX_LENGTH)
                break
            except ConnectionError as e:
                self.log.error(e)
                sys.exit(-1)
            except TimeoutError:
                pass
        self.settimeout(None)

        msg = tool.message(data, log_content, log_length, add_msg="Total")
        if msg:
            self.log.debug(msg)

        self.__tcp_data_analyser.put(data)
        for sorted_data in self.__tcp_data_analyser.packages:
            yield sorted_data

    def send_all(self, data: bytes):
        """send data packed with its information"""
        self.__tcp_data_packer.put(data)
        self.settimeout(5)
        for sorted_data in self.__tcp_data_packer.packages:

            try:
                self.sendall(sorted_data)
            except ConnectionError as e:
                self.log.error(e)
                sys.exit(-1)

            msg = tool.message(data, log_content, log_length)
            if msg:
                self.log.debug(msg)
        self.settimeout(None)


class Client(object):
    """the part which connects with a server, provide two queues to pass data"""

    def __init__(self, server_addr: tuple[str, int], is_crypt, logger):
        self.log: logging.Logger = logger

        self.server_addr = server_addr
        self.encoding: str = 'utf_8'
        self.__is_crypt: bool = is_crypt

        self.__server: AdvancedSocket | None = None

        self._queue_to_server = queue.Queue()  # for data from local to server
        self._queue_to_local = queue.Queue()  # for data from server to local

        # for crypt
        self.__rsa: tool.RSA | None = None
        self.__cipher: tool.Cipher | None = None
        self.__got_public_key: threading.Event | None = None

        if self.__is_crypt:
            self.__rsa = tool.RSA()
            self.__cipher = tool.Cipher()
            self.__got_public_key = threading.Event()

        self.__create_socket()

    def __create_socket(self):
        """connect to server"""
        try:
            self.__server = AdvancedSocket(socket.AF_INET, socket.SOCK_STREAM, self.log)
            self.__server.connect(self.server_addr)

            data = self.__server.recv(MAX_LENGTH)
            print(data.decode(self.encoding))

            self.log.info("Connect server")
        except ConnectionError as e:
            self.log.error(e)
            sys.exit(-1)

    def __get_key(self):
        """get decrypt key"""
        # recieve RSA key
        pem = next(self.__server.recv_all())
        self.__rsa.load_key(pem)
        self.log.debug("load public key")
        self.__got_public_key.set()
        # pass key by RSA
        d = next(self.__server.recv_all())
        key = self.__rsa.decrypt(d)
        self.__cipher.load_key(key)
        self.log.debug("load cipher")
        self.log.info("Ready to decrypt")

    def __send_key(self):
        """send decrypt key"""
        # send RSA key
        pem = self.__rsa.get_public_key()
        self.__server.send_all(pem)
        self.log.debug("send public key")
        # pass key by RSA
        self.__got_public_key.wait()
        key = self.__rsa.encrypt(self.__cipher.encrypt_key)
        self.__server.send_all(key)
        self.log.debug("send cipher")

    def get_server_data(self):
        """get data from server"""
        try:
            if self.__is_crypt:
                self.__get_key()

            while True:
                for data in self.__server.recv_all():
                    if self.__cipher:
                        data = self.__cipher.decrypt(data)

                    self._queue_to_local.put(data)
        except SystemExit:
            self.__server.shutdown(socket.SHUT_RDWR)
            self.__server.close()
            self.log.debug("exit and close socket")

    def send_server_data(self):
        """send data to server"""
        try:
            if self.__is_crypt:
                self.__send_key()

            while True:
                try:
                    data = self._queue_to_server.get(timeout=1)
                except queue.Empty:
                    continue

                if data:
                    if self.__cipher:
                        data = self.__cipher.encrypt(data)

                    self.__server.send_all(data)
        except SystemExit:
            self.log.debug("exit")
