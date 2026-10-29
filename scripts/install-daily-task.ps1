# 安装「每日知识库体检」Windows 计划任务（每天 08:00 跑 kb.py doctor）
# 用法：powershell -ExecutionPolicy Bypass -File scripts\install-daily-task.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = (Get-Command python -ErrorAction Stop).Source
$action = New-ScheduledTaskAction -Execute $py -Argument "scripts\kb.py doctor" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00am
Register-ScheduledTask -TaskName 'KB-Daily-Doctor' -Action $action -Trigger $trigger -Description 'AI knowledge base daily quality gate (kb.py doctor)' -Force | Out-Null
Write-Host '已注册计划任务 KB-Daily-Doctor（每天 08:00）。卸载：Unregister-ScheduledTask KB-Daily-Doctor'
