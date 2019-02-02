#!/usr/bin/env python3

import os
import subprocess
import tempfile
import typing

import conu

def generate_certificate(domains: typing.List[str]) ->\
        typing.Tuple[typing.IO, typing.IO]:
    with tempfile.NamedTemporaryFile("w") as config_file:
        cert_file = tempfile.NamedTemporaryFile("r", suffix=".pem")
        key_file = tempfile.NamedTemporaryFile("r", suffix=".key")
        conf = """
[req]
default_bits = 2048
prompt = no
default_md = sha256
x509_extensions = v3_req
distinguished_name = dn

[dn]
C = ES
ST = state
L = location
O = organisation

[v3_req]
subjectAltName = @alt_names

[alt_names]
"""
        for i, domain in enumerate(domains):
            conf += f"DNS.{i+1} = {domain}\n"
        config_file.write(conf)
        config_file.flush()

        subprocess.run(["openssl", "req", "-newkey", "rsa:2048", "-nodes",
            "-keyout", key_file.name, "-x509", "-days", "365", "-out",
            cert_file.name, "-config", config_file.name])
        return (cert_file, key_file)

def install_certificate_debian(cert: str, container: conu.DockerContainer)\
        -> None:
    container.copy_to(cert, "/usr/share/ca-certificates/")
    tempdir = tempfile.TemporaryDirectory()
    path = os.path.join(tempdir.name, "ca-certificates.conf")
    container.copy_from("/etc/ca-certificates.conf", path)
    try:
        with open(path, "a") as fp:
            basename = os.path.basename(cert)
            fp.write("{}\n".format(basename))
            fp.flush()
            container.copy_to(path, "/etc/ca-certificates.conf")
            container.execute(["update-ca-certificates"])
    finally:
        tempdir.cleanup()

def get_docker_options(cert_path: str, key_path: str) -> typing.List[str]:
    return ["-e", "TLS_CERTIFICATE={}".format(cert_path),
        "-e", "TLS_CERTIFICATE_KEY={}".format(key_path)]
