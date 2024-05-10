import argparse
import json
import os
import sys


ENV_VAR_KEYS = []
ENV_VARS_FILEPATH = "env.json"


def load_env_vars():
    """
    Looks for environment variables in three places, in order:
    - a packed JSON value from ENV_VARS environment variable (expected when running in a Lambda or Actions context),
    - an `env.json` file in the root (expected when running locally),
    - a generated default (expected when running locally for the first time).
    and filters out only the matching keys from ENV_VAR_KEYS.

    :return: environment variables to be used during execution.
    """

    env_vars = {}
    env_vars_json = os.getenv("ENV_VARS")
    if env_vars_json:
        env_vars = json.loads(env_vars_json)
    elif os.path.isfile(ENV_VARS_FILEPATH):
        with open(ENV_VARS_FILEPATH, "r") as f:
            env_vars = json.load(f)

    return {k: env_vars.get(k) for k in ENV_VAR_KEYS}


def main():
    env_vars = load_env_vars()
    if sys.argv[1:] == ["--no-pretty"]:
        output = json.dumps(env_vars, separators=(",", ":"))
    else:
        output = json.dumps(env_vars, indent=4)

    with open(ENV_VARS_FILEPATH, "w") as f:
        f.write(output)


if __name__ == "__main__":
    main()
