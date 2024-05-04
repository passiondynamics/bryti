from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

import json
from typing import (
    Any,
    Dict,
)

from src.config import load_env_vars


logger = Logger(service="bryti")
env_vars = load_env_vars()


@logger.inject_lambda_context()
def lambda_handler(event: Dict[str, Any], context: LambdaContext):
    logger.info("Lambda triggered", event=event, context=context)
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps({}),
        "headers": {
            "Content-Type": "application/json",
        },
        "cookies": [],
    }
