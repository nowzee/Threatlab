<#
    Threatlab Honeypot Agent Installer (Windows / PowerShell)
    Downloads, configures, starts AND registers-at-boot a honeypot agent.

    Quick start (run PowerShell as Administrator). You'll be asked Docker or System:
      & ([scriptblock]::Create((curl.exe -ksSL "https://your-server/api/agent/install/ID?os=windows" | Out-String)))

    Force a method:
      ... | Out-String))) -Method docker
      ... | Out-String))) -Method native
      ... | Out-String))) -Method uninstall
#>
param(
    [ValidateSet('docker', 'native', 'auto', 'uninstall', '')]
    [string]$Method = '',
    [string]$InstallDir = "$env:ProgramData\ThreatlabsAgent"
)

$ErrorActionPreference = 'Stop'

# ====================== CONFIGURATION (injected by server) ======================
$AgentId     = '{{AGENT_ID}}'
$AgentToken  = '{{AGENT_TOKEN}}'
$ServerUrl   = '{{SERVER_URL}}'
$ServiceType = '{{SERVICE_TYPE}}'
$AgentName   = '{{AGENT_NAME}}'
$Banner      = '{{BANNER}}'
# ================================================================================

$ImageName     = "threatlabs-agent-$AgentId"
$ContainerName = "threatlabs-agent-$AgentId"
$TaskName      = "ThreatlabsAgent-$AgentId"

# Accept the server's self-signed certificate for this session (PowerShell 5.1).
try { [Net.ServicePointManager]::ServerCertificateValidationCallback = { $true } } catch {}
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[OK]   $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[ERROR] $m" -ForegroundColor Red; exit 1 }

$script:StepCurrent = 0
$script:StepTotal = 1
function Step($label) {
    $script:StepCurrent++
    $pct = [int]($script:StepCurrent * 100 / $script:StepTotal)
    if ($pct -gt 100) { $pct = 100 }
    Write-Progress -Activity "Threatlab Agent installation" -Status $label -PercentComplete $pct
    Write-Host ("  -> {0}" -f $label) -ForegroundColor DarkGray
}

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

function Have($name) { $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }

# Run a native executable WITHOUT letting its stderr become a terminating error
# (PowerShell 5.1 wraps native stderr as NativeCommandError under -EA Stop, e.g.
# docker/buildkit prints progress to stderr). We only judge success by the exit
# code; output is captured and shown only on failure.
function Invoke-Native {
    param([string]$File, [string[]]$Arguments, [string]$ErrMsg = 'Command failed.')
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $out = & $File @Arguments 2>&1
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prev
    }
    if ($code -ne 0) {
        Write-Host ($out | Out-String)
        Fail $ErrMsg
    }
}

# Best-effort native call: ignore output and exit code (cleanup / optional steps).
function Invoke-NativeQuiet {
    param([string]$File, [string[]]$Arguments)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $File @Arguments 2>&1 | Out-Null } catch {} finally { $ErrorActionPreference = $prev }
}

function Get-Python {
    foreach ($c in @('python', 'py')) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

function Banner {
    Write-Host ""
    Write-Host "  +--------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |          Threatlabs Agent Installer              |" -ForegroundColor Cyan
    Write-Host "  |          Honeypot Deployment Tool (Windows)      |" -ForegroundColor Cyan
    Write-Host "  +--------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Agent:    $AgentName"
    Write-Host "  Type:     $ServiceType"
    Write-Host "  Server:   $ServerUrl"
    Write-Host "  Agent ID: $AgentId"
    Write-Host ""
}

function Choose-AutoMethod { if (Have 'docker') { 'docker' } else { 'native' } }

function Prompt-Method {
    Write-Host ""
    Write-Host "Choose the installation type:" -ForegroundColor White
    Write-Host "  1) Docker    - isolated container (recommended)" -ForegroundColor Green
    Write-Host "  2) System    - native (scheduled task at boot)" -ForegroundColor Green
    Write-Host ""
    $choice = Read-Host "Choice [1-2] (default: 1)"
    switch ($choice) { '2' { 'native' } default { 'docker' } }
}

function Download-Agent {
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    $dst = "$InstallDir\agent.py"
    # Prefer the built-in curl.exe: it negotiates the server's self-signed TLS
    # reliably, whereas Invoke-WebRequest (SChannel) often fails on it.
    if (Have 'curl.exe') {
        Invoke-Native 'curl.exe' @('-ksSL', '-o', $dst, "$ServerUrl/api/agent/download/$AgentId") 'Failed to download the agent script.'
    } else {
        Invoke-WebRequest -UseBasicParsing "$ServerUrl/api/agent/download/$AgentId" -OutFile $dst
    }
    if (-not (Test-Path $dst) -or (Get-Item $dst).Length -eq 0) {
        Fail "Failed to download the agent script."
    }
}

function Port-Args {
    if ($ServiceType -eq 'ssh') { @('-p', '22:22') }
    elseif ($ServiceType -eq 'ftp') { @('-p', '21:21') }
    else { @('-p', '22:22', '-p', '21:21') }
}

# ====================== INSTALL METHODS ======================
function Install-Docker {
    $script:StepCurrent = 0; $script:StepTotal = 4
    Write-Host "Installing via Docker..." -ForegroundColor White

    Step "Checking Docker"
    if (-not (Have 'docker')) {
        Fail "Docker was not found. Install Docker Desktop / Docker Engine, then re-run (or use -Method native)."
    }

    Step "Downloading agent"
    Download-Agent

    Step "Building image"
    @'
FROM python:3.11-alpine
RUN apk add --no-cache libffi openssl \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir paramiko requests
WORKDIR /app
COPY agent.py /app/agent.py
EXPOSE 22 21
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "agent.py" >/dev/null 2>&1 || exit 1
CMD ["python3", "-u", "/app/agent.py"]
'@ | Set-Content -Path "$InstallDir\Dockerfile" -Encoding ASCII
    Invoke-Native 'docker' @('build', '-t', $ImageName, $InstallDir) 'Docker build failed.'

    Step "Starting container"
    Invoke-NativeQuiet 'docker' @('rm', '-f', $ContainerName)
    $runArgs = @('run', '-d', '--name', $ContainerName, '--restart', 'unless-stopped') + (Port-Args) + @($ImageName)
    Invoke-Native 'docker' $runArgs 'Docker run failed.'

    Write-Progress -Activity "Threatlab Agent installation" -Completed
    Ok "Container started and set to auto-restart: $ContainerName"
    Info "Logs:    docker logs -f $ContainerName"
    Info "Restart: docker restart $ContainerName"
}

function Install-Native {
    $script:StepCurrent = 0; $script:StepTotal = 4
    Write-Host "Installing natively (scheduled task at boot)..." -ForegroundColor White

    Step "Checking Python"
    $py = Get-Python
    if (-not $py) {
        if (Have 'winget') {
            Info "Python not found - installing via winget..."
            Invoke-NativeQuiet 'winget' @('install', '--id', 'Python.Python.3.11', '-e', '--silent', '--accept-package-agreements', '--accept-source-agreements')
            $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
            $py = Get-Python
        }
    }
    if (-not $py) { Fail "Python 3 is required. Install it (https://python.org) or Docker, then re-run." }

    Step "Downloading agent"
    Download-Agent

    Step "Installing dependencies"
    Invoke-NativeQuiet $py @('-m', 'pip', 'install', '--quiet', '--upgrade', 'pip')
    Invoke-Native $py @('-m', 'pip', 'install', '--quiet', 'paramiko', 'requests') 'Failed to install Python dependencies (paramiko, requests).'

    Step "Registering scheduled task"
    $action    = New-ScheduledTaskAction -Execute $py -Argument "`"$InstallDir\agent.py`"" -WorkingDirectory $InstallDir
    $trigger   = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    $settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
                    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
                    -ExecutionTimeLimit ([TimeSpan]::Zero)
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Start-ScheduledTask -TaskName $TaskName

    Write-Progress -Activity "Threatlab Agent installation" -Completed
    Ok "Scheduled task created, started and enabled at boot: $TaskName"
    Info "Status: Get-ScheduledTask -TaskName $TaskName"
    Info "Stop:   Stop-ScheduledTask -TaskName $TaskName"
}

function Uninstall-Agent {
    Warn "Uninstalling Threatlabs agent..."
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Ok "Scheduled task removed"
    }
    if (Have 'docker') {
        Invoke-NativeQuiet 'docker' @('rm', '-f', $ContainerName)
        Invoke-NativeQuiet 'docker' @('rmi', $ImageName)
        Ok "Docker container/image removed (if any)"
    }
    if (Test-Path $InstallDir) { Remove-Item -Recurse -Force $InstallDir; Ok "Removed $InstallDir" }
    Ok "Uninstall complete"
}

# ====================== MAIN ======================
Banner

if (-not (Test-Admin)) { Fail "This installer must be run as Administrator." }

if ([string]::IsNullOrEmpty($Method)) {
    # Interactive prompt when a real host is available, otherwise auto.
    if ($Host.Name -and [Environment]::UserInteractive) { $Method = Prompt-Method } else { $Method = 'auto' }
}
if ($Method -eq 'auto') { $Method = Choose-AutoMethod; Info "Auto-selected method: $Method" }

Info "Installation method: $Method"

switch ($Method) {
    'docker'    { Install-Docker }
    'native'    { Install-Native }
    'uninstall' { Uninstall-Agent }
    default     { Fail "Unknown method: $Method" }
}

Write-Host ""
Write-Host "  +--------------------------------------------------+" -ForegroundColor Green
Write-Host "  |          Installation Complete!                  |" -ForegroundColor Green
Write-Host "  +--------------------------------------------------+" -ForegroundColor Green
Write-Host ""
Write-Host "  The agent is running and will restart automatically at boot." -ForegroundColor Green
Write-Host ""
