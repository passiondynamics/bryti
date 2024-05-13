import pytest

from types import SimpleNamespace

from src.main import lambda_handler


MOCK_CONTEXT = SimpleNamespace(**{
    "function_name": "mock-function-name",
    "memory_limit_in_mb": "mock-limit",
    "invoked_function_arn": "mock-arn",
    "aws_request_id": "mock-request-id",
})


class TestMain:
    def test_main(self):
        event = {}
        expected = {}

        actual = lambda_handler(event, MOCK_CONTEXT)

        assert actual == {}

