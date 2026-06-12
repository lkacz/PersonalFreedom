# Personal Liberty - Hosts File Cleanup Script
# This script removes all website blocks added by Personal Liberty
# Run with administrator privileges

param(
    [switch]$Silent,
    [switch]$ClearEdgeNetworkState,
    [switch]$ForceCloseEdge
)

$ErrorActionPreference = "Stop"

# Markers used by the application
$MARKER_START = "# === Personal Liberty BLOCK START ==="
$MARKER_END = "# === Personal Liberty BLOCK END ==="
$script:EdgeCleanupBlockedByRunningEdge = $false

# Hosts file path
$hostsPath = Join-Path $env:SystemRoot "System32\drivers\etc\hosts"

function Write-Log {
    param([string]$Message)
    if (-not $Silent) {
        Write-Host $Message
    }
}

function Remove-PersonalLibertyBlocks {
    try {
        # Check if hosts file exists
        if (-not (Test-Path $hostsPath)) {
            Write-Log "Hosts file not found at: $hostsPath"
            return $true
        }

        # Read the current hosts file
        $content = Get-Content $hostsPath -Raw -ErrorAction Stop

        # Check if our markers exist
        if ($content -notmatch [regex]::Escape($MARKER_START)) {
            Write-Log "No Personal Liberty blocks found in hosts file."
            return $true
        }

        Write-Log "Found Personal Liberty blocks. Removing..."

        # Create backup
        $backupPath = "$hostsPath.pf_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $hostsPath $backupPath -Force
        Write-Log "Backup created at: $backupPath"

        # Remove the block section using regex
        # This handles the case where the markers span multiple lines
        $pattern = [regex]::Escape($MARKER_START) + "[\s\S]*?" + [regex]::Escape($MARKER_END)
        $newContent = $content -replace $pattern, ""

        # Clean up extra blank lines (more than 2 consecutive)
        $newContent = $newContent -replace "(\r?\n){3,}", "`r`n`r`n"
        
        # Trim and ensure file ends with newline
        $newContent = $newContent.Trim() + "`r`n"

        # Write the cleaned content back
        Set-Content -Path $hostsPath -Value $newContent -Encoding UTF8 -Force
        Write-Log "Successfully removed Personal Liberty blocks from hosts file."

        return $true
    }
    catch {
        Write-Log "Error cleaning hosts file: $_"
        return $false
    }
}

function Clear-DnsCache {
    try {
        Write-Log "Flushing DNS cache..."
        $null = ipconfig /flushdns 2>&1
        Write-Log "DNS cache flushed successfully."
        return $true
    }
    catch {
        Write-Log "Warning: Could not flush DNS cache: $_"
        return $false
    }
}

function Clear-EdgeNetworkState {
    if (-not $ClearEdgeNetworkState) {
        return $true
    }

    try {
        Write-Log "Clearing Microsoft Edge network state..."

        $edgeProcesses = Get-Process -Name "msedge" -ErrorAction SilentlyContinue
        if ($edgeProcesses) {
            if ($ForceCloseEdge) {
                Write-Log "Closing Microsoft Edge..."
                $edgeProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
            } else {
                Write-Log "Microsoft Edge is still running."
                Write-Log "Close Edge and run again, or add -ForceCloseEdge to close it automatically."
                $script:EdgeCleanupBlockedByRunningEdge = $true
                return $false
            }
        }

        $edgeRoot = Join-Path $env:LOCALAPPDATA "Microsoft\Edge\User Data"
        if (-not (Test-Path $edgeRoot)) {
            Write-Log "Edge user data folder not found."
            return $true
        }

        $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $backupRoot = Join-Path $env:TEMP "PersonalLiberty_EdgeNetworkBackup_$timestamp"
        $patterns = @(
            "Network Persistent State",
            "Network Persistent State*.TMP",
            "Reporting and NEL",
            "Reporting and NEL-journal",
            "SCT Auditing Pending Reports"
        )

        $movedCount = 0
        $profiles = Get-ChildItem -LiteralPath $edgeRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { Test-Path (Join-Path $_.FullName "Network") }

        foreach ($profile in $profiles) {
            $networkDir = Join-Path $profile.FullName "Network"
            $profileBackup = Join-Path $backupRoot $profile.Name

            foreach ($pattern in $patterns) {
                $files = Get-ChildItem -LiteralPath $networkDir -Filter $pattern -File -Force -ErrorAction SilentlyContinue
                foreach ($file in $files) {
                    if (-not (Test-Path $profileBackup)) {
                        New-Item -ItemType Directory -Path $profileBackup -Force | Out-Null
                    }
                    $destination = Join-Path $profileBackup $file.Name
                    Move-Item -LiteralPath $file.FullName -Destination $destination -Force
                    $movedCount++
                }
            }
        }

        if ($movedCount -gt 0) {
            Write-Log "Moved $movedCount Edge network state file(s) to: $backupRoot"
            Write-Log "Edge will recreate these files on next launch."
        } else {
            Write-Log "No Edge network state files needed cleanup."
        }

        return $true
    }
    catch {
        Write-Log "Warning: Could not clear Edge network state: $_"
        return $false
    }
}

function Remove-StartupShortcut {
    try {
        # Remove startup folder shortcut
        $startupPath = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\PersonalLiberty.lnk"
        if (Test-Path $startupPath) {
            Remove-Item $startupPath -Force
            Write-Log "Removed startup shortcut."
        }
        
        # Remove No-UAC desktop shortcut
        $desktopPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Personal Liberty (No UAC).lnk"
        if (Test-Path $desktopPath) {
            Remove-Item $desktopPath -Force
            Write-Log "Removed No-UAC desktop shortcut."
        }
        
        return $true
    }
    catch {
        Write-Log "Warning: Could not remove shortcuts: $_"
        return $false
    }
}

function Stop-RunningProcesses {
    try {
        Write-Log "Stopping any running Personal Liberty processes..."
        Get-Process -Name "PersonalLiberty*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Log "Processes stopped."
        return $true
    }
    catch {
        Write-Log "Warning: Could not stop processes: $_"
        return $false
    }
}

# Main execution
Write-Log "=== Personal Liberty Cleanup ==="
Write-Log ""

$processesClean = Stop-RunningProcesses
$hostsClean = Remove-PersonalLibertyBlocks
$startupClean = Remove-StartupShortcut
$dnsClean = Clear-DnsCache
$edgeClean = Clear-EdgeNetworkState

Write-Log ""
if ($hostsClean -and $edgeClean) {
    Write-Log "Cleanup completed successfully!"
    exit 0
} elseif ($hostsClean -and $script:EdgeCleanupBlockedByRunningEdge) {
    Write-Log "Hosts/DNS cleanup completed. Edge network cleanup was skipped because Edge is still running."
    Write-Log "Close Edge fully and rerun with -ClearEdgeNetworkState, or rerun with -ClearEdgeNetworkState -ForceCloseEdge."
    exit 2
} else {
    Write-Log "Cleanup completed with errors. You may need to manually edit the hosts file."
    exit 1
}
