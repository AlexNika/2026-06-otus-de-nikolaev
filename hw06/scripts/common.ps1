#Requires -Version 5.1

$ErrorActionPreference = 'Continue'

$script:SessionContainer = 'broker'
$script:SessionBootstrap = 'localhost:29092'
$script:SessionKafkaBin = '/opt/kafka/bin'
$script:LogDir = Join-Path $PSScriptRoot 'logs'
$script:SessionLogFile = $null
$script:LogTag = 'common'
$script:LogEncoding = New-Object System.Text.UTF8Encoding($false)

try {
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
} catch {
}

function Initialize-ScriptLog {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptName,
        [string]$LogFile,
        [string[]]$Parameters
    )

    $script:LogTag = $ScriptName

    if ($LogFile) {
        $script:SessionLogFile = $LogFile
        $logParent = Split-Path -Path $LogFile -Parent
        if ($logParent -and -not (Test-Path -LiteralPath $logParent)) {
            New-Item -ItemType Directory -Path $logParent -Force | Out-Null
        }
    } else {
        if (-not (Test-Path -LiteralPath $script:LogDir)) {
            New-Item -ItemType Directory -Path $script:LogDir -Force | Out-Null
        }
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $script:SessionLogFile = Join-Path $script:LogDir ('{0}-{1}.log' -f $ScriptName, $stamp)
    }

    Write-Log -Level INFO -Message ('=== {0} started (PID {1}, PowerShell {2}) ===' -f $ScriptName, $PID, $PSVersionTable.PSVersion)
    if ($Parameters -and $Parameters.Count -gt 0) {
        Write-Log -Level INFO -Message ('Parameters: {0}' -f ($Parameters -join '; '))
    }
    Write-Log -Level INFO -Message ('Log file: {0}' -f $script:SessionLogFile)
}

function Write-Log {
    param(
        [Parameter(Mandatory = $true)][ValidateSet('INFO', 'STEP', 'WARN', 'ERROR')][string]$Level,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Message
    )

    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'
    $line = '{0} [{1,-5}] [{2}] {3}' -f $ts, $Level, $script:LogTag, $Message

    $color = 'Gray'
    switch ($Level) {
        'STEP' { $color = 'Cyan' }
        'WARN' { $color = 'Yellow' }
        'ERROR' { $color = 'Red' }
    }

    Write-Host $line -ForegroundColor $color
    if ($script:SessionLogFile) {
        [System.IO.File]::AppendAllText($script:SessionLogFile, $line + [Environment]::NewLine, $script:LogEncoding)
    }
}

function Invoke-KafkaCli {
    param(
        [Parameter(Mandatory = $true)][string]$Tool,
        [string[]]$Arguments = @(),
        [string[]]$StandardInput,
        [string]$ContainerName = $script:SessionContainer,
        [string]$KafkaBin = $script:SessionKafkaBin
    )

    $dockerArgs = @('exec')
    if ($StandardInput -and $StandardInput.Count -gt 0) {
        $dockerArgs += '-i'
    }
    $dockerArgs += $ContainerName
    $dockerArgs += ('{0}/{1}' -f $KafkaBin.TrimEnd('/'), $Tool)
    if ($Arguments -and $Arguments.Count -gt 0) {
        $dockerArgs += $Arguments
    }

    Write-Log -Level STEP -Message ('docker {0}' -f ($dockerArgs -join ' '))

    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $rawOutput = $null
    $exitCode = -1
    try {
        if ($StandardInput -and $StandardInput.Count -gt 0) {
            $stdinText = ($StandardInput -join "`n") + "`n"
            $tmpIn = [System.IO.Path]::GetTempFileName()
            $tmpOut = [System.IO.Path]::GetTempFileName()
            $tmpErr = [System.IO.Path]::GetTempFileName()
            try {
                [System.IO.File]::WriteAllText($tmpIn, $stdinText, (New-Object System.Text.UTF8Encoding($false)))
                $proc = Start-Process -FilePath 'docker' -ArgumentList $dockerArgs -RedirectStandardInput $tmpIn -RedirectStandardOutput $tmpOut -RedirectStandardError $tmpErr -NoNewWindow -Wait -PassThru
                $exitCode = $proc.ExitCode
                $rawOutput = @()
                $rawOutput += [System.IO.File]::ReadAllLines($tmpOut)
                $rawOutput += [System.IO.File]::ReadAllLines($tmpErr)
            } finally {
                Remove-Item -LiteralPath $tmpIn, $tmpOut, $tmpErr -Force -ErrorAction SilentlyContinue
            }
        } else {
            $rawOutput = & docker @dockerArgs 2>&1
            $exitCode = $LASTEXITCODE
        }
    } catch {
        Write-Log -Level ERROR -Message ('Exception while calling docker: {0}' -f $_.Exception.Message)
    } finally {
        $ErrorActionPreference = $prevEap
    }

    $lines = @()
    foreach ($item in @($rawOutput)) {
        if ($null -eq $item) { continue }
        if ($item -is [System.Management.Automation.ErrorRecord]) {
            $lines += $item.Exception.Message
        } else {
            $lines += [string]$item
        }
    }
    foreach ($outLine in $lines) {
        Write-Log -Level INFO -Message $outLine
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Output   = $lines
    }
}

function Test-DockerPrerequisites {
    param(
        [string]$ContainerName = $script:SessionContainer
    )

    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) {
        Write-Log -Level ERROR -Message 'docker CLI not found in PATH. Install Docker Desktop and retry.'
        exit 1
    }

    $state = ((& docker ps --filter ('name=^{0}$' -f $ContainerName) --format '{{.State}}' 2>&1) | ForEach-Object { [string]$_ }) -join ''
    if ($state.Trim() -ne 'running') {
        Write-Log -Level ERROR -Message ('Container ''{0}'' is not running (state: ''{1}''). Start the infrastructure: docker compose up -d' -f $ContainerName, $state.Trim())
        exit 1
    }

    $health = ((& docker inspect --format '{{.State.Health.Status}}' $ContainerName 2>&1) | ForEach-Object { [string]$_ }) -join ''
    if ($health.Trim() -eq 'healthy') {
        Write-Log -Level INFO -Message ('Container ''{0}'' is running and healthy' -f $ContainerName)
    } else {
        Write-Log -Level WARN -Message ('Container ''{0}'' health status is ''{1}'' (expected ''healthy''), continuing' -f $ContainerName, $health.Trim())
    }
}

function Resolve-KafkaBin {
    param(
        [string]$KafkaBin = $script:SessionKafkaBin,
        [string]$ContainerName = $script:SessionContainer
    )

    $candidate = $KafkaBin.TrimEnd('/')
    & docker exec $ContainerName sh -c ('test -x {0}/kafka-topics.sh' -f $candidate) 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $script:SessionKafkaBin = $candidate
        Write-Log -Level INFO -Message ('Kafka CLI directory: {0}' -f $script:SessionKafkaBin)
        return $script:SessionKafkaBin
    }

    Write-Log -Level WARN -Message ('{0}/kafka-topics.sh not found or not executable, falling back to PATH lookup' -f $candidate)
    $resolved = ((& docker exec $ContainerName sh -c 'command -v kafka-topics.sh' 2>&1) | ForEach-Object { [string]$_ }) -join ''
    $resolved = $resolved.Trim()
    if ($resolved -and $resolved.Contains('/')) {
        $script:SessionKafkaBin = $resolved.Substring(0, $resolved.LastIndexOf('/'))
        Write-Log -Level WARN -Message ('Kafka CLI directory resolved via PATH: {0}' -f $script:SessionKafkaBin)
        return $script:SessionKafkaBin
    }

    Write-Log -Level ERROR -Message ('kafka-topics.sh not found in the container (checked {0} and PATH). Check the broker image.' -f $candidate)
    exit 1
}

function Test-TopicExists {
    param(
        [Parameter(Mandatory = $true)][string]$Topic,
        [string]$ContainerName = $script:SessionContainer,
        [string]$BootstrapServer = $script:SessionBootstrap,
        [string]$KafkaBin = $script:SessionKafkaBin
    )

    $result = Invoke-KafkaCli -Tool 'kafka-topics.sh' -ContainerName $ContainerName -KafkaBin $KafkaBin -Arguments @(
        '--bootstrap-server', $BootstrapServer,
        '--list'
    )
    if ($result.ExitCode -ne 0) {
        return $false
    }
    foreach ($line in $result.Output) {
        if ($line.Trim() -eq $Topic) {
            return $true
        }
    }
    return $false
}
