<#
.SYNOPSIS
    Produces JSON messages to a Kafka topic via the console producer inside the 'broker' container.
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\02-produce-messages.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\02-produce-messages.ps1 -Topic test -Count 5
.NOTES
    Prints the RunId as the last stdout line; run-all.ps1 uses a shared RunId for produce/consume.
    If the execution policy blocks the script, run first:
    Set-ExecutionPolicy -Scope Process Bypass
#>
param(
    [string]$Topic = 'test',
    [ValidateRange(1, 100000)][int]$Count = 5,
    [string]$RunId = (Get-Date -Format 'yyyyMMddHHmmss'),
    [string[]]$Messages,
    [string]$ContainerName = 'broker',
    [string]$BootstrapServer = 'localhost:29092',
    [string]$KafkaBin = '/opt/kafka/bin',
    [string]$LogFile
)

. "$PSScriptRoot\common.ps1"

Initialize-ScriptLog -ScriptName '02-produce-messages' -LogFile $LogFile -Parameters @(
    "Topic=$Topic",
    "Count=$Count",
    "RunId=$RunId",
    "Messages=$(if ($Messages) { $Messages.Count } else { 0 }) custom",
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

if (-not (Test-TopicExists -Topic $Topic)) {
    Write-Log -Level ERROR -Message ('Topic ''{0}'' does not exist. Run 01-create-topic.ps1 first.' -f $Topic)
    exit 1
}

if ($Messages -and $Messages.Count -gt 0) {
    $payload = $Messages
    Write-Log -Level INFO -Message ('Using {0} custom message(s) from -Messages' -f $payload.Count)
} else {
    $events = @('user_login', 'user_logout', 'page_view', 'purchase', 'search')
    $ts = [DateTime]::UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
    $payload = @()
    for ($i = 1; $i -le $Count; $i++) {
        $msg = [ordered]@{
            id     = $i
            runId  = $RunId
            event  = $events[($i - 1) % $events.Count]
            source = 'ps-script'
            seq    = $i
            ts     = $ts
        }
        $payload += ($msg | ConvertTo-Json -Compress)
    }
}

if (-not $payload -or $payload.Count -eq 0) {
    Write-Log -Level ERROR -Message 'No messages to send (empty payload)'
    exit 1
}

Write-Log -Level INFO -Message ('RunId: {0}' -f $RunId)
Write-Log -Level STEP -Message ('Producing {0} message(s) to topic ''{1}'':' -f $payload.Count, $Topic)
foreach ($line in $payload) {
    Write-Log -Level INFO -Message ('payload> {0}' -f $line)
}

$result = Invoke-KafkaCli -Tool 'kafka-console-producer.sh' -Arguments @(
    '--bootstrap-server', $BootstrapServer,
    '--topic', $Topic
) -StandardInput $payload

$hasErrors = $false
foreach ($line in $result.Output) {
    if ($line -match '(?i)\bERROR\b|Exception') {
        $hasErrors = $true
    }
}

if ($result.ExitCode -ne 0 -or $hasErrors) {
    Write-Log -Level ERROR -Message ('Producer failed (exit code {0}, errors in output: {1})' -f $result.ExitCode, $hasErrors)
    exit 1
}

Write-Log -Level INFO -Message ('Sent {0} message(s) to topic ''{1}'' (runId {2})' -f $payload.Count, $Topic, $RunId)
Write-Log -Level INFO -Message 'DONE: produce step completed successfully'
Write-Output $RunId
exit 0
