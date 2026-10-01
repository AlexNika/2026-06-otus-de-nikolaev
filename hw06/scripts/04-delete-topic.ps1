<#
.SYNOPSIS
    Deletes a Kafka topic inside the 'broker' docker container (idempotent).
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\04-delete-topic.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\04-delete-topic.ps1 -Topic test -Force
.NOTES
    Asks for confirmation (type the topic name) unless -Force is given.
    If the execution policy blocks the script, run first:
    Set-ExecutionPolicy -Scope Process Bypass
#>
param(
    [string]$Topic = 'test',
    [switch]$Force,
    [string]$ContainerName = 'broker',
    [string]$BootstrapServer = 'localhost:29092',
    [string]$KafkaBin = '/opt/kafka/bin',
    [string]$LogFile
)

. "$PSScriptRoot\common.ps1"

Initialize-ScriptLog -ScriptName '04-delete-topic' -LogFile $LogFile -Parameters @(
    "Topic=$Topic",
    "Force=$Force",
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
    Write-Log -Level WARN -Message ('Topic ''{0}'' does not exist, nothing to delete' -f $Topic)
    Write-Log -Level INFO -Message 'DONE: delete step completed successfully'
    exit 0
}

if (-not $Force) {
    $answer = Read-Host ('DESTRUCTIVE OPERATION. Type the topic name to confirm deletion of ''{0}''' -f $Topic)
    if ($answer -ne $Topic) {
        Write-Log -Level WARN -Message 'Confirmation not given, deletion aborted'
        exit 1
    }
}

$delete = Invoke-KafkaCli -Tool 'kafka-topics.sh' -Arguments @(
    '--delete',
    '--topic', $Topic,
    '--bootstrap-server', $BootstrapServer
)
if ($delete.ExitCode -ne 0) {
    Write-Log -Level ERROR -Message ('Topic ''{0}'' deletion failed (exit code {1})' -f $Topic, $delete.ExitCode)
    exit 1
}

$gone = $false
for ($i = 0; $i -lt 5; $i++) {
    if (-not (Test-TopicExists -Topic $Topic)) {
        $gone = $true
        break
    }
    Start-Sleep -Seconds 1
}

if ($gone) {
    Write-Log -Level INFO -Message ('Topic ''{0}'' deleted' -f $Topic)
} else {
    Write-Log -Level WARN -Message ('Delete command succeeded but topic ''{0}'' is still listed (marked for deletion); it will disappear shortly' -f $Topic)
}

Write-Log -Level INFO -Message 'DONE: delete step completed successfully'
exit 0
