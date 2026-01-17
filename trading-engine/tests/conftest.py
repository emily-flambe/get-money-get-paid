"""
Pytest configuration and fixtures for trading-engine tests.
Mocks Cloudflare Worker APIs (js module, D1 database, fetch).
"""
import pytest
import sys
from unittest.mock import MagicMock, AsyncMock
import json


class MockHeaders:
    """Mock Cloudflare Headers object"""
    def __init__(self):
        self._headers = {}

    @classmethod
    def new(cls, items=None):
        instance = cls()
        if items:
            for key, value in items:
                instance._headers[key] = value
        return instance

    def set(self, key, value):
        self._headers[key] = value

    def get(self, key):
        return self._headers.get(key)

    def items(self):
        return self._headers.items()


class MockResponse:
    """Mock Cloudflare Response object"""
    def __init__(self, body="", status=200, headers=None):
        self._body = body
        self.status = status
        self._headers = headers or MockHeaders.new()

    @classmethod
    def new(cls, body="", status=200, headers=None):
        return cls(body, status, headers)

    async def text(self):
        return self._body

    async def json(self):
        return json.loads(self._body)


class MockRequest:
    """Mock Cloudflare Request object"""
    def __init__(self, url, init=None):
        self.url = url
        self.method = "GET"
        if init:
            self.method = getattr(init, 'method', 'GET') if hasattr(init, 'method') else init.get('method', 'GET')

    @classmethod
    def new(cls, url, init=None):
        return cls(url, init)


class MockJSON:
    """Mock JS JSON object"""
    @staticmethod
    def parse(s):
        data = json.loads(s)
        mock = MagicMock()
        for key, value in data.items():
            setattr(mock, key, value)
        return mock


class MockD1Result:
    """Mock D1 query result"""
    def __init__(self, results=None):
        self.results = results or []


class MockD1Statement:
    """Mock D1 prepared statement"""
    def __init__(self, results=None, first_result=None):
        self._results = results or []
        self._first_result = first_result

    def bind(self, *args):
        return self

    async def all(self):
        return MockD1Result(self._results)

    async def first(self):
        return self._first_result

    async def run(self):
        return MockD1Result()


class MockD1Database:
    """Mock D1 database"""
    def __init__(self):
        self._statements = {}
        self._default_results = []
        self._default_first = None

    def prepare(self, query):
        return MockD1Statement(self._default_results, self._default_first)

    def set_results(self, results):
        self._default_results = results

    def set_first(self, first):
        self._default_first = first


class MockEnv:
    """Mock Cloudflare Worker environment"""
    def __init__(self):
        self.DB = MockD1Database()
        self.ALPACA_API_KEY = "test-api-key"
        self.ALPACA_SECRET_KEY = "test-secret-key"


@pytest.fixture
def mock_env():
    """Provide a mock environment"""
    return MockEnv()


@pytest.fixture
def mock_fetch():
    """Provide a mock fetch function"""
    async def _fetch(request):
        return MockResponse.new('{"is_open": true}')
    return _fetch


@pytest.fixture(autouse=True)
def mock_js_module(monkeypatch):
    """Mock the js module that's only available in Pyodide"""
    mock_js = MagicMock()
    mock_js.fetch = AsyncMock(return_value=MockResponse.new('{}'))
    mock_js.Response = MockResponse
    mock_js.Headers = MockHeaders
    mock_js.Request = MockRequest
    mock_js.JSON = MockJSON
    mock_js.Object = MagicMock()

    sys.modules['js'] = mock_js

    # Also mock pyodide.ffi
    mock_pyodide_ffi = MagicMock()
    mock_pyodide_ffi.to_js = lambda x: x
    mock_pyodide_ffi.create_proxy = lambda x: x
    sys.modules['pyodide'] = MagicMock()
    sys.modules['pyodide.ffi'] = mock_pyodide_ffi


# Helper to create price bars for testing
def create_bars(prices):
    """Create mock OHLCV bars from a list of closing prices"""
    return [{"o": p, "h": p, "l": p, "c": p, "v": 1000} for p in prices]
