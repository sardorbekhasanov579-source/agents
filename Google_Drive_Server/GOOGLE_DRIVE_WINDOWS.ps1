$ErrorActionPreference = 'Stop'
if (!(Get-Command rclone -ErrorAction SilentlyContinue)) {
    Write-Host 'PowerShell oynasida winget install --id Rclone.Rclone -e buyrugini bajaring, keyin yangi oynada qayta ishga tushiring.'
    exit 1
}
$cfg = Join-Path $env:LOCALAPPDATA 'shaxsiy-zaxira-google.conf'
if (!(Test-Path -LiteralPath $cfg)) {
    Write-Host 'Brauzerda 4,9 GB joyi bor Google hisobini tanlang.'
    & rclone config create zaxira drive scope drive.file --config $cfg
    if ($LASTEXITCODE -ne 0) { throw 'Google ruxsati yakunlanmadi.' }
}
& rclone lsd zaxira: --max-depth 1 --config $cfg | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Google Drive ulanishi tasdiqlanmadi.' }
[Convert]::ToBase64String([IO.File]::ReadAllBytes($cfg)) | Set-Clipboard
Write-Host 'Google Drive ulandi. Buferdagi qiymatni faqat Render Environment ichidagi ZAXIRA_REMOTE_CONFIG maydoniga joylang.'
