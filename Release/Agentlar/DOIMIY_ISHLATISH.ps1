$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot '.zaxira_env\Scripts\python.exe'
if (!(Test-Path -LiteralPath 'config.json') -or !(Test-Path -LiteralPath $python)) {
    throw 'Avval BOSHLASH.bat orqali mavjud sozlamani ishga tushiring.'
}
& $python -c 'import cryptography'
if ($LASTEXITCODE -ne 0) { throw 'Avval BOSHLASH.bat orqali kutubxonalarni tayyorlang.' }
$runner = Join-Path $PSScriptRoot 'zaxira_background.py'
$action = New-ScheduledTaskAction -Execute $python -Argument ('-u "' + $runner + '"') -WorkingDirectory $PSScriptRoot
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 20 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'Shaxsiy Zaxira' -Action $action -Trigger $trigger -Settings $settings `
    -User $user -RunLevel Limited -Force | Out-Null
Write-Host 'Shaxsiy Zaxira Windows hisobiga kirganda avtomatik ochiladi.'
Write-Host 'Eski server oynasini yoping, keyin Task Scheduler > Shaxsiy Zaxira > Run.'
