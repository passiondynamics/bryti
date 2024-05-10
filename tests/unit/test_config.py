from unittest.mock import (
    MagicMock,
    mock_open,
    patch,
)
import pytest

from src.config import (
    load_env_vars,
    main,
)


class TestConfig:
    @pytest.mark.parametrize(
        "env_var_keys, env_vars_str, expected",
        [
            ([], '{}', {}),
            ([], '{"API_KEY": "MOCK-VALUE"}', {}),
            (["API_KEY"], '{}', {"API_KEY": None}),
            (["API_KEY"], '{"API_KEY": "mock-value"}', {"API_KEY": "mock-value"}),
            (["API_KEY"], '{"API_KEY": "mock-value", "BASE_URL": "mock-value-2"}', {"API_KEY": "mock-value"}),
        ],
    )
    def test_load_env_vars_env(self, env_var_keys, env_vars_str, expected, monkeypatch):
        with patch("src.config.ENV_VAR_KEYS", env_var_keys):
            monkeypatch.setenv("ENV_VARS", env_vars_str)
            actual = load_env_vars()

            assert actual == expected

    @pytest.mark.parametrize(
        "env_var_keys, env_json_contents, expected",
        [
            ([], '{}', {}),
            ([], '{"API_KEY": "MOCK-VALUE"}', {}),
            (["API_KEY"], '{}', {"API_KEY": None}),
            (["API_KEY"], '{"API_KEY": "mock-value"}', {"API_KEY": "mock-value"}),
            (["API_KEY"], '{"API_KEY": "mock-value", "BASE_URL": "mock-value-2"}', {"API_KEY": "mock-value"}),
        ],
    )
    @patch("src.config.open")
    def test_load_env_vars_file(self, mock_open, env_var_keys, env_json_contents, expected, monkeypatch):
        mock_file = MagicMock()
        mock_file.read.return_value = env_json_contents
        mock_open.return_value.__enter__.return_value = mock_file
        with patch("src.config.ENV_VAR_KEYS", env_var_keys):
            actual = load_env_vars()

            assert actual == expected
            assert mock_file.read.call_count == 1

    @pytest.mark.parametrize(
        "args, expected",
        [
            ([""], '{\n    "API_KEY": "mock-value"\n}'),
            (["", "--no-pretty"], '{"API_KEY":"mock-value"}'),
        ],
    )
    @patch("src.config.open")
    @patch("src.config.load_env_vars")
    def test_main(self, mock_load_env_vars, mock_open, args, expected):
        mock_load_env_vars.return_value = {"API_KEY": "mock-value"}
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        with patch("sys.argv", args):
            main()
            mock_file.write.assert_called_with(expected)
