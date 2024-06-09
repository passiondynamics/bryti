from boto3.dynamodb.types import (
    TypeDeserializer,
    TypeSerializer,
)

import string
from typing import (
    List,
    Optional,
)

from src.common.state_models import (
    LookupFields,
    State,
)


def ddb_to_dict(item: dict) -> dict:
    """
    Convert DynamoDB-formatted dictionary to normal dictionary.

    :param item: DynamoDB-formatted item.
    :return: A normally-formatted dictionary.
    """
    converter = TypeDeserializer()
    return {k: converter.deserialize(v) for k, v in item.items()}


def dict_to_ddb(obj: dict) -> dict:
    """
    Convert normal dictionary to DynamoDB-formatted dictionary.

    :param obj: A normally-formatted dictionary.
    :return: A DynamoDB-formatted item.
    """
    converter = TypeSerializer()
    return {k: converter.serialize(v) for k, v in obj.items()}


class StateTableInterface:
    ATTRIBUTE_KEYS = [
        l1 + l2 for l1 in string.ascii_lowercase for l2 in string.ascii_lowercase
    ]

    def __init__(self, dynamodb_client, table_name: str):
        self.dynamodb_client = dynamodb_client
        self.table_name = table_name

    def _query(
        self,
        key: str,
        value: str,
        index_name: Optional[str] = None,
    ) -> List[dict]:
        """
        Helper to query the state table on the given primary key (and optionally, on a given index).

        :param key: The primary key column.
        :param value: The value of the primary key.
        :param index_name: If given, the name of the secondary to index to query on instead.
        :return: A list of matching objects from the state table.
        """

        key_condition_expression = "#pk = :pk"
        attribute_names = {"#pk": key}
        attribute_values = {":pk": {"S": value}}

        # Build in dict instead of directly passing as params due to optional IndexName.
        query_args = {
            "TableName": self.table_name,
            "KeyConditionExpression": key_condition_expression,
            "ExpressionAttributeNames": attribute_names,
            "ExpressionAttributeValues": attribute_values,
            "Limit": 1,
        }
        if index_name:
            query_args["IndexName"] = index_name

        response = self.dynamodb_client.query(**query_args)
        return [ddb_to_dict(item) for item in response["Items"]]

    def _lookup(self, index_name: str, key: str, value: str) -> Optional[LookupFields]:
        """
        Helper to query a state table lookup index, to get the corresponding user primary key + IDs for a given platform user ID.
        """

        users = self._query(key, value, index_name=index_name)
        if len(users) == 0:
            return None

        return LookupFields.model_validate(users[0])

    def lookup_by_twitch(self, twitch_user_id: str) -> Optional[LookupFields]:
        """
        Looks up a user by a Twitch user ID.
        """

        return self._lookup("twitch-lookup-index", "twitch_user_id", twitch_user_id)

    def lookup_by_discord(self, discord_user_id: str) -> Optional[LookupFields]:
        """
        Looks up a user by a Discord user ID.
        """

        return self._lookup("discord-lookup-index", "discord_user_id", discord_user_id)

    def lookup_by_github(self, github_user_id: str) -> Optional[LookupFields]:
        """
        Looks up a user by a Discord user ID.
        """

        return self._lookup("github-lookup-index", "github_user_id", github_user_id)

    def get_state(self, user: str) -> Optional[State]:
        """
        Queries for the state of a given user.

        :param user: The primary key/user to query the state table on.
        :return: A State object representing what's in the table.
        """

        states = self._query("user", user)
        return State.model_validate(states[0]) if len(states) > 0 else None

    def update_state(self, state: State):
        """
        Updates the table with the given state, validating/incrementing the version in the table if successful.

        :param state: The corresponding state to put into the table.
        :return: The updated state, with the new version number.
        """

        item = dict_to_ddb(state.model_dump(exclude_none=True))
        zipped_attributes = zip(self.ATTRIBUTE_KEYS, item.items())

        # Dynamically generate attribute-related params for update_item.
        attribute_names = {}
        attribute_values = {":one": {"N": "1"}}
        update_expressions = []
        for k, (n, v) in zipped_attributes:
            an = "#" + k
            av = ":" + k
            attribute_expression = f"{an} = {av}"
            if n != "user":
                # Exclude the primary key from the update.
                attribute_names[an] = n
                attribute_values[av] = v
                if n == "version":
                    # Increment the version of the item.
                    update_expressions.append(attribute_expression + " + :one")
                    condition_expression = (
                        f"attribute_not_exists({an}) OR {attribute_expression}"
                    )
                else:
                    update_expressions.append(attribute_expression)

        update_expression = "SET " + ", ".join(update_expressions)

        response = self.dynamodb_client.update_item(
            TableName=self.table_name,
            Key={"user": item["user"]},
            ExpressionAttributeNames=attribute_names,
            ExpressionAttributeValues=attribute_values,
            UpdateExpression=update_expression,
            ConditionExpression=condition_expression,
            ReturnValues="ALL_NEW",
        )
        updated_item = ddb_to_dict(response["Attributes"])
        return State.model_validate(updated_item)
