#!/usr/bin/env python3

import json
import unittest
import unittest.mock

from mockdock import server

class HttpResponseTest(unittest.TestCase):
    def test_code_to_status_OK(self):
        http_response = server.HttpResponse()
        status = http_response.code_to_status(200)
        self.assertEqual(status, "OK")

    def test_code_to_status_not_found(self):
        http_response = server.HttpResponse()
        status = http_response.code_to_status(404)
        self.assertEqual(status, "Not Found")

    def test_code_to_status_default(self):
        http_response = server.HttpResponse()
        # The default for unknown http status codes is to report error
        status = http_response.code_to_status(302)
        self.assertEqual(status, "Error")

    def test_to_message(self):
        http_response = server.HttpResponse("Patrick Star".encode("utf8"), 200)
        message = http_response.to_message()
        expected = ("HTTP/1.1 200 OK\nContent-Type: text/plain\n"
            "Content-Length: 12\n\nPatrick Star".encode("utf8"))
        self.assertEqual(message, expected)

class ConfigTest(unittest.TestCase):
    def test_init_data(self):
        config = server.Config(data='{"path": {"code": 200}}')
        self.assertEqual(config.data, {"path": {"code": 200}})

    def test_init_path(self):
        try:
            original_open = server.__builtins__["open"]
            mock_open = unittest.mock.MagicMock()
            mock_file = unittest.mock.MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_file.read = lambda: '{"path": {"code": 200}}'
            server.__builtins__["open"] = mock_open

            config = server.Config(config_path="path")
            self.assertEqual(config.data, {"path": {"code": 200}})
        finally:
            server.__builtins__["open"] = original_open

    def test_init_data_and_path(self):
        with self.assertRaises(ValueError):
            server.Config(data='{"path": {"code": 200}}', config_path="config_path")

    def test_init_no_data(self):
        config = server.Config()
        self.assertEqual(config.data, {})

    def test_response_for_path(self):
        data = json.dumps({
            "path": {
                "code": 200,
                "data": "data",
                "content-type": "application/json"
            }
        })
        config = server.Config(data=data)
        response = config.response_for_path("path")
        self.assertEqual(response.code, 200)
        self.assertEqual(response.data, b"data")
        self.assertEqual(response.content_type, "application/json")
    def test_response_for_path_not_found(self):
        config = server.Config()
        response = config.response_for_path("path")
        self.assertEqual(response.code, 404)

class HttpRequestTest(unittest.TestCase):
    def test_parse(self):
        r = b"POST / HTTP/1.1\r\nHost: google.com\r\nUser-Agent: Wget\r\nConnection: close\r\n\r\n"
        request = server.HttpRequest(r)
        self.assertEqual(request.path, "/")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.headers["User-Agent"], "Wget")
        self.assertEqual(request.headers["Connection"], "close")

    def test_parse_host_with_port(self):
        r = b"GET /path HTTP/1.1\r\nHost: sponge.bob:8080\r\nUser-Agent: curl/7.59.0\r\nAccept: */*\r\n\r\n"
        request = server.HttpRequest(r)
        self.assertEqual(request.path, "/path")
        self.assertEqual(request.headers["Host"], "sponge.bob:8080")
        self.assertEqual(request.headers["User-Agent"], "curl/7.59.0")
        self.assertEqual(request.headers["Accept"], "*/*")

    def test_parse_invalid_unicode(self):
        r = b"\xa0"
        with self.assertRaises(server.ParseRequestError):
            server.HttpRequest(r)

    def test_parse_malformed_request_string(self):
        r = b"/path HTTP/1.1\r\nHost: sponge.bob:8080\r\nUser-Agent: curl/7.59.0\r\nAccept: */*\r\n\r\n"
        with self.assertRaises(server.ParseRequestError):
            server.HttpRequest(r)
