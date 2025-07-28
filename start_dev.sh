#!/bin/bash
python.exe scripts/setup.py
bash scripts/migrations.sh
docker compose up -d