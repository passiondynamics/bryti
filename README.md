# bryti

[Bryti](https://en.wiktionary.org/wiki/bryti) (pronounced [bree-thee, /bri-thi/](http://ipa-reader.xyz/?text=bri-thi&voice=Karl)) is the title given to stewards (typically royalty, like the king).

A Twitch bot to handle/manage events from different streamers.

## Contributing

All steps prefixed with `(required)` must be done to fully setup your local repository.

### Download

**(required)** Clone the repo and enter it:
```bash
git clone git@github.com:passiondynamics/bryti.git
cd bryti/
```

### Virtual environment

`(required)` Enter(/create) the virtual env:
```bash
pipenv shell
```

*(required)* Install all dependencies listed in `Pipfile.lock`:
```bash
pipenv sync --dev
```

(required) Set up local environment variables:
```bash
python -m src/config.py
```

<details>
<summary>Two notes about the above step ^</summary>

1. This generates an `env.json` file in the root directory of your local repo, you'll need to fill this out as needed if you want to run code using those variables locally.
2. `env.json` is ignored by this repo, meaning that any changes you make to it, will (and should!) stay only on your local machine.

</details>


Add a new dependency:
```bash
pipenv install {package}
```

### Code style

Run the linter:
```bash
black src/
```

### Unit tests

(make sure you're in the virtual env and at root folder of the repo)

Run unit tests:
```bash
pytest tests/unit
```

Run unit tests with coverage information:
```bash
pytest --cov=src --cov-fail-under=90 tests/unit
```

<!--
### Integration tests

(in virtual env, from repo root)

Run integration tests:
```bash
behave tests/integration
```
--!>
