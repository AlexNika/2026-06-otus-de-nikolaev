<#
.SYNOPSIS
    Consumes messages from a Kafka topic via the console consumer inside the 'broker' container.
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\03-consume-messages.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\03-consume-messages.ps1 -Topic test -MaxMessages 10 -TimeoutMs 10000 -RunId 20260927145500
.NOTES
    A consumer timeout (TimeoutException) is not treated as a failure when the
    'Processed a total of N messages' summary is present (WARN, exit 0).
    If the execution policy blocks the script, run first:
    Set-ExecutionPolicy -Scope Process Bypass
#>
param(
    [string]$Topic = 'test',
    [ValidateRange(1, 10000000)][int]$MaxMessages = 100,
    [ValidateRange(1, 600000)][int]$TimeoutMs = 15000,
    [string]$RunId,
    [bool]$FromBeginning = $true,
    [string]$ContainerName = 'broker',
    [string]$BootstrapServer = 'localhost:29092',
    [string]$KafkaBin = '/opt/kafka/bin',
    [string]$LogFile
)

. "$PSScriptRoot\common.ps1"

Initialize-ScriptLog -ScriptName '03-consume-messages' -LogFile $LogFile -Parameters @(
    "Topic=$Topic",
    "MaxMessages=$MaxMessages",
    "TimeoutMs=$TimeoutMs",
    "RunId=$RunId",
    "FromBeginning=$FromBeginning",
    "ContainerName=$ContainerName",
    "BootstrapServer=$BootstrapServer",
    "KafkaBin=$KafkaBin",
    "LogFile=$LogFile"
)

$script:SessionContainer = $ContainerName
$script:SessionBootstrap = $BootstrapServer
$script:SessionKafkaBin = $KafkaBin

Test-DockerPrerequisites
Resolve-KafkaBin | Out-Null

$cliArgs = @('--bootstrap-server', $BootstrapServer, '--topic', $Topic)
if ($FromBeginning) {
    $cliArgs += '--from-beginning'
}
$cliArgs += @('--max-messages', "$MaxMessages", '--timeout-ms', "$TimeoutMs")
$cliArgs += @('--property', 'print.timestamp=true', '--property', 'print.partition=true', '--property', 'print.offset=true')

$result = Invoke-KafkaCli -Tool 'kafka-console-consumer.sh' -Arguments $cliArgs

$totalProcessed = -1
$timedOut = $false
$runMatches = 0
foreach ($line in $result.Output) {
    if ($line -match 'Processed a total of (\d+) messages') {
        $totalProcessed = [int]$Matches[1]
    }
    if ($line -match 'TimeoutException') {
        $timedOut = $true
    }
    if ($RunId -and $line.Contains($RunId)) {
        $runMatches++
    }
}

if ($totalProcessed -lt 0) {
    Write-Log -Level ERROR -Message ('Consumer finished without summary line (exit code {0})' -f $result.ExitCode)
    exit 1
}

Write-Log -Level INFO -Message ('Total messages read: {0}; messages of current run (runId {1}): {2}' -f $totalProcessed, $(if ($RunId) { $RunId } else { 'any' }), $runMatches)

if ($RunId -and $runMatches -eq 0) {
    Write-Log -Level WARN -Message ('No messages matching runId ''{0}'' were read' -f $RunId)
}

if ($timedOut -or $result.ExitCode -ne 0) {
    Write-Log -Level WARN -Message ('Consumer hit the timeout (exit code {0}, TimeoutException: {1}); summary line is present, treating the step as successful' -f $result.ExitCode, $timedOut)
}

Write-Log -Level INFO -Message 'DONE: consume step completed successfully'
exit 0
