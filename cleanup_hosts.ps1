# Personal Liberty - Hosts File Cleanup Script
# This script removes all website blocks added by Personal Liberty
# Run with administrator privileges

param(
    [switch]$Silent
)

$ErrorActionPreference = "Stop"

# Markers used by the application
$MARKER_START = "# === Personal Liberty BLOCK START ==="
$MARKER_END = "# === Personal Liberty BLOCK END ==="

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

# Main execution
Write-Log "=== Personal Liberty Cleanup ==="
Write-Log ""

$hostsClean = Remove-PersonalLibertyBlocks
$dnsClean = Clear-DnsCache

Write-Log ""
if ($hostsClean) {
    Write-Log "Cleanup completed successfully!"
    exit 0
} else {
    Write-Log "Cleanup completed with errors. You may need to manually edit the hosts file."
    exit 1
}
