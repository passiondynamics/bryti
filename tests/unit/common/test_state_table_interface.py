import pytest

from unittest.mock import (
    MagicMock,
    patch,
)

from src.common.state_models import (
    LookupFields,
    State,
)
from src.common.state_table_interface import (
    StateTableInterface,
    ddb_to_dict,
    dict_to_ddb,
)


MOCK_DDB_ITEM = {"user": {"S": "mock-user"}}
MOCK_DICT_ITEM = {"user": "mock-user"}


def test_ddb_to_dict():
    item = MOCK_DDB_ITEM
    expected = MOCK_DICT_ITEM

    actual = ddb_to_dict(item)

    assert actual == expected


def test_dict_to_ddb():
    obj = MOCK_DICT_ITEM
    expected = MOCK_DDB_ITEM

    actual = dict_to_ddb(obj)

    assert actual == expected


@pytest.fixture
def mock_dynamodb_client():
    return MagicMock()


@pytest.fixture
def state_interface(mock_dynamodb_client):
    return StateTableInterface(mock_dynamodb_client, "mock-table-name")


@pytest.mark.parametrize(
    "ddb_items, expected",
    [
        ([], []),
        ([MOCK_DDB_ITEM], [MOCK_DICT_ITEM]),
        ([MOCK_DDB_ITEM, MOCK_DDB_ITEM], [MOCK_DICT_ITEM, MOCK_DICT_ITEM]),
    ],
)
def test_query(mock_dynamodb_client, state_interface, ddb_items, expected):
    mock_dynamodb_client.query.return_value = {"Items": ddb_items}

    actual = state_interface._query("mock-key", "mock-value")

    assert actual == expected
    mock_dynamodb_client.query.assert_called_once_with(
        TableName="mock-table-name",
        KeyConditionExpression="#pk = :pk",
        ExpressionAttributeNames={"#pk": "mock-key"},
        ExpressionAttributeValues={":pk": {"S": "mock-value"}},
        Limit=1,
    )


def test_query_index(mock_dynamodb_client, state_interface):
    mock_dynamodb_client.query.return_value = {"Items": [MOCK_DDB_ITEM]}
    expected = [MOCK_DICT_ITEM]

    actual = state_interface._query("mock-key", "mock-value", index_name="mock-index-name")

    assert actual == expected
    mock_dynamodb_client.query.assert_called_once_with(
        TableName="mock-table-name",
        KeyConditionExpression="#pk = :pk",
        ExpressionAttributeNames={"#pk": "mock-key"},
        ExpressionAttributeValues={":pk": {"S": "mock-value"}},
        Limit=1,
        IndexName="mock-index-name",
    )


@pytest.mark.parametrize(
    "ddb_items, expected",
    [
        ([], None),
        ([MOCK_DDB_ITEM], LookupFields(user="mock-user")),
    ],
)
def test_lookup_by_twitch(mock_dynamodb_client, state_interface, ddb_items, expected):
    mock_dynamodb_client.query.return_value = {"Items": ddb_items}

    actual = state_interface.lookup_by_twitch("mock-twitch-user-id")

    assert actual == expected
    mock_dynamodb_client.query.assert_called_once_with(
        TableName="mock-table-name",
        KeyConditionExpression="#pk = :pk",
        ExpressionAttributeNames={"#pk": "twitch_user_id"},
        ExpressionAttributeValues={":pk": {"S": "mock-twitch-user-id"}},
        Limit=1,
        IndexName="twitch-lookup-index",
    )


@pytest.mark.parametrize(
    "ddb_items, expected",
    [
        ([], None),
        ([MOCK_DDB_ITEM], LookupFields(user="mock-user")),
    ],
)
def test_lookup_by_discord(mock_dynamodb_client, state_interface, ddb_items, expected):
    mock_dynamodb_client.query.return_value = {"Items": ddb_items}

    actual = state_interface.lookup_by_discord("mock-discord-user-id")

    assert actual == expected
    mock_dynamodb_client.query.assert_called_once_with(
        TableName="mock-table-name",
        KeyConditionExpression="#pk = :pk",
        ExpressionAttributeNames={"#pk": "discord_user_id"},
        ExpressionAttributeValues={":pk": {"S": "mock-discord-user-id"}},
        Limit=1,
        IndexName="discord-lookup-index",
    )


@pytest.mark.parametrize(
    "ddb_items, expected",
    [
        ([], None),
        ([MOCK_DDB_ITEM], LookupFields(user="mock-user")),
    ],
)
def test_lookup_by_github(mock_dynamodb_client, state_interface, ddb_items, expected):
    mock_dynamodb_client.query.return_value = {"Items": ddb_items}

    actual = state_interface.lookup_by_github("mock-github-user-id")

    assert actual == expected
    mock_dynamodb_client.query.assert_called_once_with(
        TableName="mock-table-name",
        KeyConditionExpression="#pk = :pk",
        ExpressionAttributeNames={"#pk": "github_user_id"},
        ExpressionAttributeValues={":pk": {"S": "mock-github-user-id"}},
        Limit=1,
        IndexName="github-lookup-index",
    )


@pytest.mark.parametrize(
    "ddb_items, expected",
    [
        ([], None),
        ([MOCK_DDB_ITEM], State(user="mock-user")),
    ],
)
def test_get_state(mock_dynamodb_client, state_interface, ddb_items, expected):
    mock_dynamodb_client.query.return_value = {"Items": ddb_items}

    actual = state_interface.get_state("mock-user")

    assert actual == expected
    mock_dynamodb_client.query.assert_called_once_with(
        TableName="mock-table-name",
        KeyConditionExpression="#pk = :pk",
        ExpressionAttributeNames={"#pk": "user"},
        ExpressionAttributeValues={":pk": {"S": "mock-user"}},
        Limit=1,
    )


def test_update_state(mock_dynamodb_client, state_interface):
    mock_dynamodb_client.update_item.return_value = {"Attributes": {**MOCK_DDB_ITEM, "version": {"N": "2"}}}
    initial_state = State(user="mock-user", version=1)
    final_state = State(user="mock-user", version=2)

    actual = state_interface.update_state(initial_state)
    assert actual == final_state
    mock_dynamodb_client.update_item.assert_called_once_with(
        TableName="mock-table-name",
        Key={"user": {"S": "mock-user"}},
        ExpressionAttributeNames={
            "#ab": "members",
            "#ac": "version",
        },
        ExpressionAttributeValues={
            ":one": {"N": "1"},
            ":ab": {"M": {}},
            ":ac": {"N": "1"},
        },
        UpdateExpression="SET #ab = :ab, #ac = :ac + :one",
        ConditionExpression="#ac = :ac",
        ReturnValues="ALL_NEW",
    )
