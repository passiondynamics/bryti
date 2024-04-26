# bryti

[Bryti](https://en.wiktionary.org/wiki/bryti) is the title given to stewards (typically royalty, like the king).

A Twitch bot to handle/manage events from different streamers.

## Contributing

### Download

```bash
git clone git@github.com:passiondynamics/bryti.git
cd bryti/
```

### Virtual environment

Enter(/create) the virtual env:
```bash
pipenv shell
```

Install all dependencies listed in `Pipfile.lock`:
```bash
pipenv sync --dev
```

Add a new dependency:
```bash
pipenv install {package}
```

### Unit tests

(make sure you're in the virtual env and at root folder of the repo)

Run unit tests:
```bash
pytest tests/unit
```

Run unit tests with coverage information:
```bash
pytest --cov=src tests/unit
```

<!--
### Integration tests

(in virtual env, from repo root)

Run integration tests:
```bash
behave tests/integration
```
--!>
