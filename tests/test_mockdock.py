#!/usr/bin/env python3

import unittest
import subprocess

import mockdock

class MockDockTest(unittest.TestCase):
    def test_generate_certificate(self):
        domains = ["patrick.star"]
        cert_file, key_file = mockdock.generate_certificate(domains)
        cert_result = subprocess.check_output(["openssl", "x509", "-in",
            cert_file.name, "-text", "-noout"])
        self.assertEqual("patrick.star" in cert_result.decode("utf8"), True)
        key_result = subprocess.check_call(["openssl", "rsa", "-in",
            key_file.name, "-text", "-noout"])
        self.assertEqual(key_result, 0)

    def test_get_docker_options(self):
        result = mockdock.get_docker_options("cert.pem", "cert.key")
        expected = ["-e", "TLS_CERTIFICATE=cert.pem",
            "-e", "TLS_CERTIFICATE_KEY=cert.key"]
        self.assertEqual(result, expected)
