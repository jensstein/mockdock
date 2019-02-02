#!/usr/bin/env python3

import json
import logging
import os
import unittest
import subprocess
import tempfile

import conu

import mockdock

class IntegrationTest(unittest.TestCase):
    def test_blah(self):
        print("building image tls-test")
        conu.DockerImage.build(".", tag="tls-test", dockerfile="Dockerfile-tlstest")
        print("building image mockdock")
        conu.DockerImage.build(".", tag="mockdock", dockerfile="Dockerfile")

        domains = ["google.com", "domain.org"]

        # This dictionary specify the responses given for different queries.
        # All elements all optional.
        config = json.dumps({
            "google.com/": {
                "data": '{"response": "OK"}\n',
                "code": 200,
                "content-type": "application/json"
            },
            "domain.org:1010/path": {
                "data": "Okay response\n",
                "code": 200
            }
        })

        # Generate a certificate with subject alternative names for the
        # specified domains.
        cert_file, key_file = mockdock.generate_certificate(domains)

        image_name = "mockdock"
        image_tag = "latest"
        with conu.DockerBackend() as backend:
            try:
                server_image = backend.ImageClass(image_name, tag=image_tag)
                docker_options = mockdock.get_docker_options(cert_file.name,
                    key_file.name)
                server_container = server_image.run_via_binary(
                    volumes=[(cert_file.name, cert_file.name),
                    (key_file.name, key_file.name)],
                    additional_opts=["-e", "CONFIG_DATA={}".format(config),
                        "-e", "EXTRA_PORTS=[1010]"] +
                        docker_options)
                server_container.wait_for_port(80)
                server_container.wait_for_port(1010)
                container_ips = server_container.get_IPv4s()

                client_image = backend.ImageClass("tls-test")
                # Use the docker --dns argument to specify the server
                # container as dns resolver.
                docker_run = conu.DockerRunBuilder(["bash"], additional_opts=[
                    "-it", "-u", "root", "--dns", container_ips[0]])
                client_container = client_image.run_via_binary(docker_run)
                # Install the generated certificate in the server container.
                # This method is debian-specific.
                mockdock.install_certificate_debian(cert_file.name,
                    client_container)

                result1 = client_container.execute(["curl", "-vi", "google.com"])
                self.assertEqual(b'{"response": "OK"}' in result1[-1], True)
                result2 = client_container.execute(["curl", "-vi", "https://google.com"])
                self.assertEqual(b'{"response": "OK"}' in result2[-1], True)
                result3 = client_container.execute(["curl", "-vi",
                    "domain.org:1010/path"])
                self.assertEqual(b"Okay response" in result3[-1], True)
                result4 = client_container.execute(["curl", "-vi", "https://domain.org"])
                self.assertEqual(b"Not Found" in result4[-1], True)
            finally:
                server_container.kill()
                server_container.delete()
                client_container.kill()
                client_container.delete()

    def test_install_certificate(self):
        with conu.DockerBackend() as backend:
            try:
                image = backend.ImageClass("tls-test")
                container = image.run_via_binary(conu.DockerRunBuilder(["bash"],
                    additional_opts=["-it"]))
                cert_file, key_file = mockdock.generate_certificate(["google.com"])
                mockdock.install_certificate_debian(cert_file.name, container)
                with container.mount() as fs:
                    certificates_conf = fs.read_file("/etc/ca-certificates.conf")
                    self.assertEqual(os.path.basename(cert_file.name) in
                        certificates_conf, True)
                    self.assertEqual(fs.file_is_present(os.path.join(
                        "/usr/share/ca-certificates/", os.path.basename(
                        cert_file.name))), True)
            finally:
                container.kill()
                container.delete()
