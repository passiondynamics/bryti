from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from typing import (
    Any,
    Dict,
)


logger = Logger(service="bryti")


@logger.inject_lambda_context()
def handler(event: Dict[str, Any], context: LambdaContext):
    logger.info("Lambda triggered", event=event, context=context)
    return {}
