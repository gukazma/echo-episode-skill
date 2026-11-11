param([string]$cmd)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="cmd /c `"$here\$cmd`""; CurrentDirectory=$here}
$r.ProcessId
