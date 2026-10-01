<#
.SYNOPSIS
    Runs the full scenario: create topic -> produce messages -> consume messages.
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-all.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-all.ps1 -Topic test -Count 5
.NOTES
    All steps run as child processes and share one log file (scripts\logs\run-all-*.log)
    and one RunId. Stops at the first failed step.
    If the execution policy blocks the script, run first:
    Set-ExecutionPolicy -Scope Process Bypass
#>
param(
    [string]$Topic = 'test',
    [ValidateRange(1, 100000)][int]$Count = 5,
    [string]$RunId = (Get-Date -Format 'yyyyMMddHHmmss'),
    [int]$MaxMessages = 0,
    [ValidateRange(1, 600000)][int]$TimeoutMs = 15000,
    [string]$ContainerName = 'broker',
    [string]$BootstrapServer = 'localhost:29092',
    [string]$KafkaBin = '/opt/kafka/bin',
    [string]$LogFile
)

. "$PSScriptRoot\common.ps1"

Initialize-ScriptLog -ScriptName 'run-all' -LogFile $LogFile -Parameters @(
    "Topic=$Topic",
    "Count=$Count",
    "RunId=$RunId",
    "MaxMessages=$MaxMessages",
    "TimeoutMs=$TimeoutMs",
    "ContainerName=$ContainerName",
    "BootstrapServer=$BootstrapServer",
    "KafkaBin=$KafkaBin",
    "LogFile=$LogFile"
)

if ($MaxMessages -le 0) {
    $MaxMessages = $Count + 500
}

$psExe = (Get-Process -Id $PID).Path
Write-Log -Level INFO -Message ('Shell executable: {0}' -f $psExe)
Write-Log -Level INFO -Message ('Shared RunId: {0}; shared log: {1}' -f $RunId, $script:SessionLogFile)

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$failedStep = $null

$steps = @(
    [pscustomobject]@{
        Name = '01-create-topic'
        File = '01-create-topic.ps1'
        Args = @(
            '-Topic', $Topic,
            '-ContainerName', $ContainerName,
            '-BootstrapServer', $BootstrapServer,
            '-KafkaBin', $KafkaBin,
            '-LogFile', $script:SessionLogFile
        )
    },
    [pscustomobject]@{
        Name = '02-produce-messages'
        File = '02-produce-messages.ps1'
        Args = @(
            '-Topic', $Topic,
            '-Count', "$Count",
            '-RunId', $RunId,
            '-ContainerName', $ContainerName,
            '-BootstrapServer', $BootstrapServer,
            '-KafkaBin', $KafkaBin,
            '-LogFile', $script:SessionLogFile
        )
    },
    [pscustomobject]@{
        Name = '03-consume-messages'
        File = '03-consume-messages.ps1'
        Args = @(
            '-Topic', $Topic,
            '-MaxMessages', "$MaxMessages",
            '-TimeoutMs', "$TimeoutMs",
            '-RunId', $RunId,
            '-ContainerName', $ContainerName,
            '-BootstrapServer', $BootstrapServer,
            '-KafkaBin', $KafkaBin,
            '-LogFile', $script:SessionLogFile
        )
    }
)

foreach ($step in $steps) {
    Write-Log -Level STEP -Message ('=== Step {0} ===' -f $step.Name)
    $scriptPath = Join-Path $PSScriptRoot $step.File
    $stepArgs = $step.Args
    & $psExe -NoProfile -ExecutionPolicy Bypass -File $scriptPath @stepArgs
    $stepExit = $LASTEXITCODE
    if ($stepExit -ne 0) {
        Write-Log -Level ERROR -Message ('Step ''{0}'' failed with exit code {1}' -f $step.Name, $stepExit)
        $failedStep = $step.Name
        break
    }
    Write-Log -Level INFO -Message ('Step ''{0}'' finished with exit code 0' -f $step.Name)
}

$sw.Stop()
$elapsed = '{0:N1}' -f $sw.Elapsed.TotalSeconds

if ($failedStep) {
    Write-Log -Level ERROR -Message ('FAILED at step ''{0}''; elapsed {1}s; log file: {2}' -f $failedStep, $elapsed, $script:SessionLogFile)
    exit 1
}

Write-Log -Level INFO -Message ('SUCCESS: topic ''{0}'', produced {1} message(s), runId {2}; elapsed {3}s; log file: {4}' -f $Topic, $Count, $RunId, $elapsed, $script:SessionLogFile)
exit 0
