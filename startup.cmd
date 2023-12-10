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

REM Start the primary load balancer
start "Primary Load Balancer" "venv\Scripts\python.exe" "src\loadbalancer\LoadBalancer.py" p

REM Wait for 1 second for sockets to stabilize
timeout /t 1 /nobreak > NUL

REM Start the backup load balancer
start "Backup Load Balancer" "venv\Scripts\python.exe" "src\loadbalancer\LoadBalancer.py" b

REM Wait for 5 seconds for sockets to stabilize
timeout /t 5 /nobreak > NUL

REM Start the servers on specified ports
start "Server@1225" "venv\Scripts\python.exe" "src\server\Server.py" 1225
timeout /t 1 /nobreak > NUL
start "Server@1226" "venv\Scripts\python.exe" "src\server\Server.py" 1226
timeout /t 1 /nobreak > NUL
start "Server@1227" "venv\Scripts\python.exe" "src\server\Server.py" 1227
timeout /t 1 /nobreak > NUL
start "Server@1228" "venv\Scripts\python.exe" "src\server\Server.py" 1228
timeout /t 1 /nobreak > NUL
start "Server@1229" "venv\Scripts\python.exe" "src\server\Server.py" 1229
timeout /t 1 /nobreak > NUL

REM Close the virtual environment
call deactivate

REM Install client dependencies
::call cd app\client
::call npm install
::call npm rebuild zeromq --runtime=electron --target=27.1.3

REM Start the client
::call npm run start

REM Clear console and leave it ready for input at root directory
::call cd ../..
::@echo off
::call cmd /k
