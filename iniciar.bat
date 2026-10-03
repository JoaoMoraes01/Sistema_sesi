@echo off
title Sistema SESI - Fila de Matriculas
echo Iniciando o sistema...
echo (Esta janela precisa ficar aberta enquanto o sistema estiver em uso)
echo.
echo IMPORTANTE: NAO aperte Ctrl+C nesta janela, exceto quando quiser
echo desligar o sistema de proposito. Para copiar um texto daqui,
echo selecione o texto com o mouse e clique com o botao direito.
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause