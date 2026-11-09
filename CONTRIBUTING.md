# Contributing

```bash
git clone https://github.com/Ehsas317/zombicheck.git
cd zombicheck
pip install -r requirements.txt
export TINYFISH_API_KEY=...   # https://agent.tinyfish.ai/api-keys
make test                     # 16 offline tests (no key needed)
zombiecheck source --out rows.csv --limit 600
zombiecheck check rows.csv -o out.csv --limit 600 --resume
```

- Verdict thresholds live in `zombicheck/states.py` with tests.
- New signals need a mocked `check_row` case in `tests/test_check.py`.
- Don't commit API keys or `__pycache__/`.
