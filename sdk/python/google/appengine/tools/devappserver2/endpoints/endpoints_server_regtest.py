#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Regression tests for Endpoints server in devappserver2."""


import json
import os.path

from google.testing.pybase import googletest

from google.appengine.tools.devappserver2 import regtest_utils
from google.appengine.tools.devappserver2.endpoints import endpoints_server


class EndpointsServerRegtest(regtest_utils.BaseTestCase):
  """Tests that the development server can correctly serve static content."""

  def setUp(self):
    super(EndpointsServerRegtest, self).setUp()
    server_path = os.path.join(self.devappserver2_path,
                               'endpoints/testdata/app.yaml')
    self.start_server([server_path])

  def test_rest_get(self):
    """Test that a GET request to a REST API works."""
    status, content, headers = self.fetch_url('default', 'GET',
                                              '/_ah/api/test_service/v1/test')
    self.assertEqual(200, status)
    self.assertEqual('application/json', headers['Content-Type'])

    response_json = json.loads(content)
    self.assertEqual({'text': 'Test response'}, response_json)

  def test_rest_post(self):
    """Test that a POST request to a REST API works."""
    body = json.dumps({'name': 'MyName', 'number': 23})
    send_headers = {'content-type': 'application/json'}
    status, content, headers = self.fetch_url('default', 'POST',
                                              '/_ah/api/test_service/v1/t2path',
                                              body, send_headers)
    self.assertEqual(200, status)
    self.assertEqual('application/json', headers['Content-Type'])

    response_json = json.loads(content)
    self.assertEqual({'text': 'MyName 23'}, response_json)

  def test_cors(self):
    """Test that CORS headers are handled properly."""
    send_headers = {'Origin': 'test.com',
                    'Access-control-request-method': 'GET',
                    'Access-Control-Request-Headers': 'Date,Expires'}
    status, _, headers = self.fetch_url('default', 'GET',
                                        '/_ah/api/test_service/v1/test',
                                        headers=send_headers)
    self.assertEqual(200, status)
    self.assertEqual(headers[endpoints_server._CORS_HEADER_ALLOW_ORIGIN],
                     'test.com')
    self.assertIn('GET',
                  headers[endpoints_server._CORS_HEADER_ALLOW_METHODS].split(
                      ','))
    self.assertEqual(headers[endpoints_server._CORS_HEADER_ALLOW_HEADERS],
                     'Date,Expires')

  def test_rpc(self):
    """Test that an RPC request works."""
    body = json.dumps([{'jsonrpc': '2.0',
                        'id': 'gapiRpc',
                        'method': 'testservice.t2name',
                        'params': {'name': 'MyName', 'number': 23},
                        'apiVersion': 'v1'}])
    send_headers = {'content-type': 'application-rpc'}
    status, content, headers = self.fetch_url('default', 'POST',
                                              '/_ah/api/rpc',
                                              body, send_headers)
    self.assertEqual(200, status)
    self.assertEqual('application/json', headers['Content-Type'])

    response_json = json.loads(content)
    self.assertEqual([{'result': {'text': 'MyName 23'},
                       'id': 'gapiRpc'}], response_json)

if __name__ == '__main__':
  googletest.main()
