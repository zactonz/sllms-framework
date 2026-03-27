# Contributing

## Development Flow

```bash
git clone https://github.com/zactonz/sllms-framework.git sllms-framework
cd sllms-framework
python -m pip install -e .
python scripts/bootstrap.py --all
python main.py --doctor
python scripts/smoke_test.py
```

## Pull Request Expectations

- keep the framework cross-platform
- avoid adding GPU-only assumptions
- prefer small, composable tools and plugins
- document any new config keys and examples
- keep system actions behind clear allowlists or safe defaults
- keep `sllms-framework` independent from optional child tool repos
- move reusable niche tool families into separate repos instead of bundling them into core when possible

## Testing

- run `PYTHONPYCACHEPREFIX=.pycache_local python -m compileall main.py llm stt tools tts utils sllms_framework tests`
- run `python scripts/smoke_test.py`
- run `python -m unittest discover -s tests -v`
- test at least one text command locally

## Large Runtime Assets

- do not commit downloaded models
- do not commit local runtime caches or logs
- use `scripts/bootstrap.py` for reproducible setup
