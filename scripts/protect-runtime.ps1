# The upstream Unix mode assertion cannot express Windows NTFS ACLs.
# Agent subprocesses may inherit PowerShell 7 module paths while running 5.1.
# Load this host's own module explicitly; leave global PSModulePath unchanged.
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1') -ErrorAction Stop
$runtimePath = Join-Path $ProjectRoot 'runtime'
$runtimeAcl = Get-Acl -LiteralPath $runtimePath
if (-not $runtimeAcl.AreAccessRulesProtected) {
    $runtimeAcl.SetAccessRuleProtection($true, $false)
    foreach ($rule in @($runtimeAcl.Access)) { $runtimeAcl.RemoveAccessRuleSpecific($rule) }
    $projectUserSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $projectSystemSid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18')
    foreach ($sid in @($projectUserSid, $projectSystemSid)) {
        $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
            $sid, [System.Security.AccessControl.FileSystemRights]::FullControl,
            [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
            [System.Security.AccessControl.PropagationFlags]::None,
            [System.Security.AccessControl.AccessControlType]::Allow)
        $runtimeAcl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $runtimePath -AclObject $runtimeAcl
}
$actualAcl = Get-Acl -LiteralPath $runtimePath
$actualAcl | Select-Object Owner,AreAccessRulesProtected,@{Name='Access';Expression={
    @($_.Access | Select-Object IdentityReference,FileSystemRights,AccessControlType,IsInherited)
}} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$ProjectRoot\evidence\runtime-acl.json" -Encoding UTF8
