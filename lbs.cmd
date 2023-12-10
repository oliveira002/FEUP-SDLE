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

REM Start the load balancers
start "Primary Load Balancer" "venv\Scripts\python.exe" "src\loadbalancer\LoadBalancer.py" p

call timeout /t 3 /nobreak > NUL

start "Backup Load Balancer" "venv\Scripts\python.exe" "src\loadbalancer\LoadBalancer.py" b

REM Wait for 3 second for sockets to stabilize
::call timeout /t 3 /nobreak > NUL

call deactivate