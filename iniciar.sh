#!/bin/bash
echo "Iniciando o sistema..."
echo "(Este terminal precisa ficar aberto enquanto o sistema estiver em uso)"
echo ""
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000