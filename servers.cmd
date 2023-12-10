@echo off

REM Check if the virtual environment already exists
if not exist venv (
    REM Create a virtual environment
    call %python_executable% -m venv venv
)

REM Activate the python virtual environment
call venv\Scripts\activate

REM Install dependencies
call pip install -r requirements.txt

REM Start the servers on specified ports
start "Server@1225" "venv\Scripts\python.exe" "src\server\Server.py" 1225
start "Server@1226" "venv\Scripts\python.exe" "src\server\Server.py" 1226
start "Server@1227" "venv\Scripts\python.exe" "src\server\Server.py" 1227
start "Server@1228" "venv\Scripts\python.exe" "src\server\Server.py" 1228
start "Server@1229" "venv\Scripts\python.exe" "src\server\Server.py" 1229

call deactivate