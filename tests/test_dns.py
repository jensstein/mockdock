#!/usr/bin/env python3

import unittest

from mockdock import dns

class DNSTest(unittest.TestCase):
    def test_build_packet(self):
        data = b"^4\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01"
        packet = dns.build_packet(data, "192.168.0.1")
        expeced_result = b"^4\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x00<\x00\x04\xc0\xa8\x00\x01"
        self.assertEqual(packet, expeced_result)
