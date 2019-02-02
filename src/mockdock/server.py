#!/usr/bin/env python3

import json
import logging
import os
import multiprocessing
import socket
import ssl
import sys
import typing

from mockdock import dns

CONFIG_PATH = os.getenv("CONFIG_PATH")
CONFIG_DATA = os.getenv("CONFIG_DATA")

TLS_CERTIFICATE = os.getenv("TLS_CERTIFICATE")
TLS_CERTIFICATE_KEY = os.getenv("TLS_CERTIFICATE_KEY")

# This variable is used to indicate if additional ports need to be opened
# and listened to.
EXTRA_PORTS = os.getenv("EXTRA_PORTS")

def setup_logging() -> logging.Logger:
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger

logger = setup_logging()

class ParseRequestError(Exception):
    pass

class HttpResponse(object):
    def __init__(self, data: bytes = bytes(), code: int = 404,
            content_type = "text/plain") -> None:
        # TODO: specify binary data in base64
        self.data = data
        self.code = code
        self.content_type = content_type

    def code_to_status(self, code: int) -> str:
        if code == 200:
            return "OK"
        elif code == 404:
            return "Not Found"
        return "Error"

    def to_message(self) -> bytes:
        status = self.code_to_status(self.code)
        content_length = len(self.data)
        header = "HTTP/1.1 {} {}\nContent-Type: {}\nContent-Length: {}\n\n".format(
            self.code, status, self.content_type, content_length).encode("utf8")
        return header + self.data

class Config(object):
    def __init__(self, data: typing.Optional[str] = None,
            config_path: typing.Optional[str] = None) -> None:
        if data is not None and config_path is not None:
            raise ValueError("cannot supply both data and config path")
        if config_path is not None:
            with open(config_path) as fp:
                self.data = json.load(fp)
        elif data is not None:
            self.data = json.loads(data)
        else:
            self.data = {}
        logger.debug("Using config {}".format(self.data))

    def response_for_path(self, path: str) -> HttpResponse:
        if path in self.data:
            kwargs = {}
            if "data" in self.data[path]:
                kwargs["data"] = self.data[path]["data"].encode("utf8")
            if "code" in self.data[path]:
                kwargs["code"] = self.data[path]["code"]
            if "content-type" in self.data[path]:
                kwargs["content_type"] = self.data[path]["content-type"]
            return HttpResponse(**kwargs)
        return HttpResponse()

class HttpRequest(object):
    def __init__(self, request_bytes: bytes) -> None:
        try:
            request = request_bytes.decode("utf8")
            self.method, self.path, self.headers = self.parse(request)
        except (UnicodeDecodeError, ValueError) as e:
            raise ParseRequestError(e)

    def parse(self, request: str) -> typing.Tuple[str, str, dict]:
        parts = request.split("\r\n")
        method, path, _ = parts[0].split(" ")
        headers = {k.strip(): v.strip() for k, v in [k.split(":", maxsplit=1) for k in
            [p for p in parts[1:] if p]]}
        return method, path, headers

    def __str__(self) -> str:
        return "HttpRequest({}, {}, {})".format(self.method, self.path,
            self.headers)

class DnsResolverProcess(multiprocessing.Process):
    def __init__(self, redirect_ip: str = None, port: int = 53):
        multiprocessing.Process.__init__(self, target=self.start_socket,
            args=(redirect_ip, port))

    def start_socket(self, redirect_ip: str = None, port: int = 53):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("0.0.0.0", port))
        ip = socket.gethostbyname(socket.getfqdn()) if redirect_ip is None \
            else redirect_ip
        logger.info("Resolving dns to {}".format(ip))

        while True:
            data, address = s.recvfrom(1024)
            packet = dns.build_packet(data, ip)
            logger.debug("dns question received from {}: {}. response: {}".format(
                address, data, packet))
            s.sendto(packet, address)

class ServerProcess(multiprocessing.Process):
    def __init__(self, port: int) -> None:
        multiprocessing.Process.__init__(self, target=self.start_socket,
            args=(port,))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.config = Config(CONFIG_DATA, CONFIG_PATH)

    def start_socket(self, port: int) -> None:
        self.socket.bind(("0.0.0.0", port))
        self.socket.listen(1)
        while True:
            try:
                conn, address = self.socket.accept()
                while True:
                    data = conn.recv(1024)
                    logger.debug("conn {} data {} addr {}".format(conn, data, address))
                    if not data:
                        break
                    request = HttpRequest(data)
                    path = request.headers["Host"] + request.path
                    response = self.config.response_for_path(path)
                    message = response.to_message()
                    conn.send(message)
            except (ssl.SSLError, ConnectionResetError, BrokenPipeError, ParseRequestError) as e:
                logger.error("Caught error while handling connection: {}"
                    .format(e))

class TlsServerProcess(ServerProcess):
    def __init__(self, ssl_certificate: str, ssl_key: str, port: int = 443)\
             -> None:
        ServerProcess.__init__(self, port)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(ssl_certificate, ssl_key)
        self.socket = context.wrap_socket(self.socket, server_side=True)

def main():
    dns_resolver = DnsResolverProcess()
    dns_resolver.start()
    server_process = ServerProcess(80)
    server_process.start()

    if TLS_CERTIFICATE is not None and TLS_CERTIFICATE_KEY is not None:
        tls_server_process = TlsServerProcess(TLS_CERTIFICATE,
            TLS_CERTIFICATE_KEY)
        tls_server_process.start()

    if EXTRA_PORTS is not None:
        ports = json.loads(EXTRA_PORTS)
        for port in ports:
            p = ServerProcess(port)
            p.start()

if __name__ == "__main__":
    main()
