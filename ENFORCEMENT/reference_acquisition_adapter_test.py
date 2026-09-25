#!/usr/bin/env python3
import http.server
import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import reference_acquisition_adapter as adapter

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body=b"hello reference"
        self.send_response(200)
        self.send_header("Content-Type","text/plain")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*args): pass

class AcquisitionAdapterTest(unittest.TestCase):
    def test_blocks_private_target(self):
        with self.assertRaises(adapter.AcquisitionError):
            adapter.validate_public_url("http://127.0.0.1/test")

    def test_blocks_file_scheme(self):
        with self.assertRaises(adapter.AcquisitionError):
            adapter.validate_public_url("file:///tmp/a")

    def test_public_validation_with_mocked_dns(self):
        with mock.patch("socket.getaddrinfo",return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,"",("93.184.216.34",80))]):
            out=adapter.validate_public_url("http://example.test/a")
            self.assertEqual(out["host"],"example.test")
            self.assertEqual(out["resolved_ips"],["93.184.216.34"])

    def test_acquire_preserves_bounded_content(self):
        # Local HTTP server is used only as a deterministic transport fixture.
        server=http.server.ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        port=server.server_address[1]
        real_open=adapter.urllib.request.OpenerDirector.open
        def fake_validate(url):
            parsed=adapter.urllib.parse.urlsplit(url)
            return {"url":url,"scheme":parsed.scheme,"host":parsed.hostname,"resolved_ips":["93.184.216.34"]}
        try:
            with tempfile.TemporaryDirectory() as td,                  mock.patch.object(adapter,"validate_public_url",side_effect=fake_validate):
                result=adapter.acquire(f"http://127.0.0.1:{port}/sample.txt",destination_dir=Path(td),max_bytes=1024)
                self.assertTrue(result["pass"])
                self.assertEqual(result["acquisition_state"],"ACQUIRED_AND_PRESERVED")
                self.assertTrue(result["preserved"])
                p=Path(result["preserved_path"])
                self.assertTrue(p.exists())
                self.assertEqual(p.read_bytes(),b"hello reference")
                self.assertFalse(result["canonical_promotion"])
        finally:
            server.shutdown(); server.server_close()

    def test_oversize_becomes_remote_only(self):
        class BigHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body=b"x"*2048
                self.send_response(200)
                self.send_header("Content-Type","application/octet-stream")
                self.send_header("Content-Length",str(len(body)))
                self.end_headers(); self.wfile.write(body)
            def log_message(self,*args): pass
        server=http.server.ThreadingHTTPServer(("127.0.0.1",0),BigHandler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        port=server.server_address[1]
        def fake_validate(url):
            parsed=adapter.urllib.parse.urlsplit(url)
            return {"url":url,"scheme":parsed.scheme,"host":parsed.hostname,"resolved_ips":["93.184.216.34"]}
        try:
            with tempfile.TemporaryDirectory() as td, mock.patch.object(adapter,"validate_public_url",side_effect=fake_validate):
                r=adapter.acquire(f"http://127.0.0.1:{port}/big.bin",destination_dir=Path(td),max_bytes=128)
                self.assertTrue(r["pass"])
                self.assertEqual(r["acquisition_state"],"ACCESSIBLE_REMOTE_SOURCE")
                self.assertFalse(r["preserved"])
        finally:
            server.shutdown(); server.server_close()

if __name__=="__main__":
    unittest.main()
