param(
    [string]$PythonExe = "python",
    [ValidateSet("real_ide", "in_memory")]
    [string]$Backend = "real_ide",
    [switch]$JsonLogs
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$srcPath = Join-Path $repoRoot "src"
$bridgeScriptPath = Join-Path $srcPath "codesys_mcp_server\core\codesys_bridge.py"

$env:PYTHONPATH = $srcPath
$env:CODESYS_MCP_BACKEND = $Backend
$env:CODESYS_MCP_BRIDGE_SCRIPT_PATH = $bridgeScriptPath

$command = @(
    "-m",
    "codesys_mcp_server.server.cli",
    "--backend",
    $Backend,
    "--bridge-script-path",
    $bridgeScriptPath
)

if ($JsonLogs) {
    $command += "--log-json"
}

$command += "serve-stdio"

& $PythonExe @command
exit $LASTEXITCODE
