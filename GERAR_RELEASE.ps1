$ErrorActionPreference="Stop"

python -m pip install -r requirements-dev.txt
python -m pip install -r license_server/requirements.txt
python -m pip install httpx2
python tools/build_release.py
