#!/usr/bin/env python3

import struct

def build_packet(data: bytes, ip: str) -> bytes:
    addr = ip.encode("utf8")
    # https://tools.ietf.org/html/rfc1035
    # https://routley.io/tech/2017/12/28/hand-writing-dns-messages.html
    # First two bytes of response header is copied from the request
    header = data[:2]
    # \x81\x80 in binary is 1000 0001 1000 0000
    # this corresponds to the header row
    # +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    # |QR|   Opcode  |AA|TC|RD|RA|   Z    |   RCODE   |
    # +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    # which means that
    # QR = 1
    # Opcode = 0
    # AA = 0
    # TC = 0
    # RD = 1
    # RA = 1
    # Z = 0
    # RCODE = 0
    header += struct.pack("2B", 0x81, 0x80)
    # The number of questions is taken from the request and duplicated
    # as the number of answers
    header += struct.pack("4B", *[i for i in data[4:6]] * 2)
    # No authority records and no additional records
    header += struct.pack(">2H", 0, 0)

    packet = header
    # Include original question
    offset = 12
    packet += data[offset:]
    # This sequence is a pointer to the domain name in the response.
    # \xc0 in binary is 1100 0000
    # The first two bits must be 11 to distinguish pointers from labels.
    packet += struct.pack("2B", 0xc0, offset)
    # type = A, host address
    packet += struct.pack(">H", 1)
    # class = IN, the internet
    packet += struct.pack(">H", 1)
    # cache time interval in seconds
    packet += struct.pack(">i", 60)
    # data length = 4 bytes
    packet += struct.pack(">H", 4)
    packet += struct.pack("4B", *[int(i) for i in ip.split(".")])
    return packet
