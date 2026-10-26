@echo off
rem Relay group poll task (register with Task Scheduler every N minutes, see docs/setup-windows.md)
rem RULES: keep CRLF endings; keep "call" before the IM CLI (npm .cmd shim) or remaining lines never execute.
rem Layout: scripts live in %USERPROFILE%\.agent-relay\scripts\poll\ ; data in %USERPROFILE%\.agent-relay\
setlocal
if not exist "%USERPROFILE%\.agent-relay\logs" mkdir "%USERPROFILE%\.agent-relay\logs"
set LOG=%USERPROFILE%\.agent-relay\logs\group_poll.log
set LATEST=%USERPROFILE%\.agent-relay\poll_latest.json
>> "%LOG%" echo === %date% %time% poll run ===
for /f "usebackq delims=" %%i in ('node "%~dp0group_poll.js" --print im_cli') do set RELAY_IM_CLI=%%i
for /f "usebackq delims=" %%i in ('node "%~dp0group_poll.js" --print chat_id') do set RELAY_CHAT_ID=%%i
if "%RELAY_IM_CLI%"=="" set RELAY_IM_CLI=lark-cli
if "%RELAY_CHAT_ID%"=="" (
  >> "%LOG%" echo chat_id missing in config, skip this cycle
  exit /b 0
)
call %RELAY_IM_CLI% im +chat-messages-list --as bot --chat-id %RELAY_CHAT_ID% --order desc --limit 50 --format json > "%LATEST%" 2>> "%LOG%"
node "%~dp0group_poll.js" >> "%LOG%" 2>&1
endlocal
