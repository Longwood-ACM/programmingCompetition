#!/bin/bash
export FLASK_APP=server.py
python3 -m flask run --host=0.0.0.0 -p 7777
