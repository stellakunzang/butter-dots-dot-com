#!/bin/sh
# PID 1 must be uvicorn so the process receives stop signals.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
