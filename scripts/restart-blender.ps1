<#
.SYNOPSIS
  Closes Blender safely, installs the addon from this checkout, starts Blender and waits until the addon's socket is up.

.DESCRIPTION
  1. If Blender is running, the script asks the addon over its socket (localhost:9876 by default) whether the
     open file has unsaved changes (bpy.data.is_dirty). Unsaved changes stop the script. So does a Blender that
     does not answer: the script never closes a Blender it cannot check. -SkipDirtyCheck skips this step, for
     the first install or when the user has confirmed by hand that nothing is unsaved.
  2. Blender is closed with CloseMainWindow, once, and given 60 s to exit. If it does not exit, the script
     stops and reports. It never kills the process (no Stop-Process, no taskkill).
  3. addon.py from the repository is copied to Blender's user addons folder as blender_mcp.py. The SHA-256 of
     the installed copy is compared with the source and the result printed. A missing addons folder is created.
  4. Blender is started with scripts\enable-addon.py, which enables the addon and saves the preferences, and
     the script waits up to 120 s for the socket to answer a ping.

  When Blender is not running, steps 1 and 2 are skipped.
  The BlenderExe environment variable overrides D:\SteamLibrary\steamapps\common\Blender\blender.exe, and
  BlenderAddonsDir overrides %APPDATA%\Blender Foundation\Blender\<version>\scripts\addons, where <version>
  is the newest folder found there.

.PARAMETER SkipDirtyCheck
  Close a running Blender without asking the addon whether the file is saved. Only when the user confirmed it.

.PARAMETER Port
  The addon's socket port. Default 9876.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\restart-blender.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipDirtyCheck,
    [int]$Port = 9876
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$CloseTimeoutSeconds = 60
$StartTimeoutSeconds = 120
$SocketTimeoutMs = 5000

function Stop-Script([string]$Message) {
    Write-Host "restart-blender: STOPPED. $Message" -ForegroundColor Red
    exit 1
}

# Sends one JSON command to the addon and returns the parsed reply, or $null when nothing answers.
# The addon's protocol is one JSON object per command and one JSON object back, no framing.
function Send-BlenderCommand([string]$Type, [hashtable]$Params) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connect = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $connect.AsyncWaitHandle.WaitOne($SocketTimeoutMs)) { return $null }
        $client.EndConnect($connect)

        $stream = $client.GetStream()
        $stream.ReadTimeout = $SocketTimeoutMs
        $command = @{ type = $Type; params = $Params }
        $bytes = [System.Text.Encoding]::UTF8.GetBytes((ConvertTo-Json $command -Compress -Depth 5))
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush()

        $buffer = New-Object byte[] 65536
        $text = ''
        $deadline = (Get-Date).AddMilliseconds($SocketTimeoutMs)
        while ((Get-Date) -lt $deadline) {
            $read = $stream.Read($buffer, 0, $buffer.Length)
            if ($read -le 0) { break }
            $text += [System.Text.Encoding]::UTF8.GetString($buffer, 0, $read)
            try { return (ConvertFrom-Json $text) } catch { }
        }
        return $null
    }
    catch {
        return $null
    }
    finally {
        $client.Close()
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$blenderExe = if ($env:BlenderExe) { $env:BlenderExe } else { 'D:\SteamLibrary\steamapps\common\Blender\blender.exe' }
$sourceAddon = Join-Path $repoRoot 'addon.py'
$enableScript = Join-Path $repoRoot 'scripts\enable-addon.py'

if (-not (Test-Path -LiteralPath $blenderExe)) {
    Stop-Script "blender.exe was not found at $blenderExe. Set BlenderExe to the Blender executable."
}
if (-not (Test-Path -LiteralPath $sourceAddon)) {
    Stop-Script "addon.py was not found at $sourceAddon."
}

if ($env:BlenderAddonsDir) {
    $addonsDir = $env:BlenderAddonsDir
}
else {
    $base = Join-Path $env:APPDATA 'Blender Foundation\Blender'
    $versionDir = Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\d+\.\d+$' } |
        Sort-Object { [version]$_.Name } -Descending |
        Select-Object -First 1
    if (-not $versionDir) {
        Stop-Script "No Blender version folder under $base. Start Blender once by hand, or set BlenderAddonsDir."
    }
    $addonsDir = Join-Path $versionDir.FullName 'scripts\addons'
}
$installedAddon = Join-Path $addonsDir 'blender_mcp.py'

# 1-2. Close a running Blender, but only when that loses no work.
$running = @(Get-Process -Name 'blender' -ErrorAction SilentlyContinue)

if ($running.Count -gt 1) {
    Stop-Script "$($running.Count) Blender processes are running (ids: $($running.Id -join ', ')). The dirty check covers only one, so close them yourself."
}

if ($running.Count -eq 1) {
    $blender = $running[0]
    Write-Host "restart-blender: Blender is running (process $($blender.Id))."

    if ($SkipDirtyCheck) {
        Write-Host 'restart-blender: -SkipDirtyCheck given, closing without asking the addon.' -ForegroundColor Yellow
    }
    else {
        Write-Host "restart-blender: asking the addon on port $Port whether the file is saved."
        $code = "import bpy, json`nprint('DIRTYCHECK ' + json.dumps({'dirty': bpy.data.is_dirty, 'file': bpy.data.filepath}))"
        $reply = Send-BlenderCommand 'execute_code' @{ code = $code }
        if ($null -eq $reply) {
            Stop-Script "No addon answered on port $Port, so the file state is unknown and Blender was NOT closed. Save your work and close Blender yourself, or run again with -SkipDirtyCheck after confirming nothing is unsaved."
        }
        # execute_code replies {"status": "success", "result": {"executed": true, "result": "<stdout>"}}.
        $output = ''
        try { $output = [string]$reply.result.result } catch { }
        if ($output -notmatch 'DIRTYCHECK (\{.*\})') {
            $replyText = ConvertTo-Json $reply -Compress -Depth 10
            Stop-Script "The addon answered, but not with the file state: $replyText. Blender was NOT closed."
        }
        $state = ConvertFrom-Json $Matches[1]
        $fileLabel = if ($state.file) { $state.file } else { '(unsaved new file)' }
        if ($state.dirty) {
            Stop-Script "Blender has unsaved changes in $fileLabel. Save the file first (Ctrl+S in Blender). Blender was NOT closed."
        }
        Write-Host "restart-blender: no unsaved changes in $fileLabel."
    }

    Write-Host 'restart-blender: closing Blender with CloseMainWindow.'
    if (-not $blender.CloseMainWindow()) {
        Stop-Script 'Blender has no main window that accepts a close request. It was not closed.'
    }
    if (-not $blender.WaitForExit($CloseTimeoutSeconds * 1000)) {
        Stop-Script "Blender did not exit within $CloseTimeoutSeconds s (a dialog may be open). It is still running; the script never kills it. Look at the Blender window."
    }
    Write-Host 'restart-blender: Blender has exited.'
}
else {
    Write-Host 'restart-blender: Blender is not running; skipping the close step.'
}

# 3. Install the addon while Blender does not hold it.
if (-not (Test-Path -LiteralPath $addonsDir)) {
    New-Item -ItemType Directory -Path $addonsDir | Out-Null
    Write-Host "restart-blender: created $addonsDir."
}
$sourceHash = (Get-FileHash -LiteralPath $sourceAddon -Algorithm SHA256).Hash
if (Test-Path -LiteralPath $installedAddon) {
    $installedHash = (Get-FileHash -LiteralPath $installedAddon -Algorithm SHA256).Hash
    if ($installedHash -eq $sourceHash) {
        Write-Host "restart-blender: the installed addon is unchanged (hash starts $($sourceHash.Substring(0, 8)))."
    }
    else {
        Write-Host "restart-blender: replacing the installed addon ($($installedHash.Substring(0, 8))) with the source ($($sourceHash.Substring(0, 8)))."
    }
}
else {
    Write-Host "restart-blender: first install of the addon (hash starts $($sourceHash.Substring(0, 8)))."
}
Copy-Item -LiteralPath $sourceAddon -Destination $installedAddon -Force
Write-Host "restart-blender: addon installed at $installedAddon."

# 4. Start Blender, let enable-addon.py switch the addon on, and wait for the socket.
Write-Host "restart-blender: starting $blenderExe."
$started = Start-Process -FilePath $blenderExe -ArgumentList @('--python', "`"$enableScript`"") -PassThru
$deadline = (Get-Date).AddSeconds($StartTimeoutSeconds)

while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2

    if ($started.HasExited) {
        Stop-Script "The new Blender process $($started.Id) exited with code $($started.ExitCode) before the addon came up."
    }

    $pong = Send-BlenderCommand 'ping' @{}
    if ($null -ne $pong -and $pong.status -eq 'success') {
        Write-Host "restart-blender: DONE. Blender process $($started.Id) is up; the addon answers on port $Port."
        exit 0
    }
}

Stop-Script "No addon answered on port $Port within $StartTimeoutSeconds s. Blender may still be loading, or the addon failed to enable. In Blender open Edit > Preferences > Add-ons and look for 'MCP for Blender'; the console window (Window > Toggle System Console) shows the error."
