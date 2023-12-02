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

REM Close the virtual environment
call deactivate

REM Start the load balancer
start "Load Balancer" "venv\Scripts\python.exe" "src\loadbalancer\LoadBalancer.py"

REM Wait for 1 second for sockets to stabilize
call timeout /t 1 /nobreak > NUL

REM Start the servers on specified ports
start "Server" "venv\Scripts\python.exe" "src\server\Server.py" 1111

REM Install client dependencies
::call cd app\client
::call npm install
::call npm rebuild zeromq --runtime=electron --target=27.1.3

REM Start the client
::call npm run start

REM Clear console and leave it ready for input at root directory
::call cd ../..
@echo off
call cmd /k
