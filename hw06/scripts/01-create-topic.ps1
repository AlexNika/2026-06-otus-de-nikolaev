<#
.SYNOPSIS
    Creates a Kafka topic inside the 'broker' docker container (idempotent).
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\01-create-topic.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\01-create-topic.ps1 -Topic test -Partitions 3 -ReplicationFactor 1
.NOTES
    If the execution policy blocks the script, run first:
    Set-ExecutionPolicy -Scope Process Bypass
#>
param(
    [string]$Topic = 'test',
    [ValidateRange(1, 1000)][int]$Partitions = 3,
    [ValidateRange(1, 10)][int]$ReplicationFactor = 1,
    [string]$ContainerName = 'broker',
    [string]$BootstrapServer = 'localhost:29092',
    [string]$KafkaBin = '/opt/kafka/bin',
    [string]$LogFile
)

. "$PSScriptRoot\common.ps1"

Initialize-ScriptLog -ScriptName '01-create-topic' -LogFile $LogFile -Parameters @(
    "Topic=$Topic",
    "Partitions=$Partitions",
    "ReplicationFactor=$ReplicationFactor",
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

if (Test-TopicExists -Topic $Topic) {
    Write-Log -Level WARN -Message ('Topic ''{0}'' already exists, skipping creation' -f $Topic)
} else {
    $create = Invoke-KafkaCli -Tool 'kafka-topics.sh' -Arguments @(
        '--create', '--if-not-exists',
        '--topic', $Topic,
        '--partitions', "$Partitions",
        '--replication-factor', "$ReplicationFactor",
        '--bootstrap-server', $BootstrapServer
    )
    if ($create.ExitCode -ne 0) {
        Write-Log -Level ERROR -Message ('Topic ''{0}'' creation failed (exit code {1})' -f $Topic, $create.ExitCode)
        exit 1
    }
    Write-Log -Level INFO -Message ('Topic ''{0}'' created (partitions={1}, replicationFactor={2})' -f $Topic, $Partitions, $ReplicationFactor)
}

$describe = Invoke-KafkaCli -Tool 'kafka-topics.sh' -Arguments @(
    '--describe',
    '--topic', $Topic,
    '--bootstrap-server', $BootstrapServer
)
if ($describe.ExitCode -ne 0) {
    Write-Log -Level ERROR -Message ('Describe for topic ''{0}'' failed (exit code {1})' -f $Topic, $describe.ExitCode)
    exit 1
}

Write-Log -Level INFO -Message 'DONE: topic step completed successfully'
exit 0
