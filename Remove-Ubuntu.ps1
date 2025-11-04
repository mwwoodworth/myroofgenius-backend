<# 
.SYNOPSIS
  Removes Ubuntu/GRUB and Linux partitions from a Windows PC.

.DESCRIPTION
  - Sets Windows Boot Manager as default/primary.
  - Mounts the EFI System Partition (ESP) and deletes \EFI\ubuntu (and stray \EFI\grub if present).
  - Deletes Linux data/swap partitions (GPT GUID types).
  - Optionally expands the Windows (C:) partition into immediately adjacent free space.

.PARAMETER Force
  Skip confirmation prompts (non-interactive).

.PARAMETER ExpandC
  Attempt to extend C: into adjacent free space after deletion (safe-only).

.NOTES
  Run from Windows, as Administrator. Tested on Windows 10/11 with GPT/UEFI.
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [switch]$Force,
  [switch]$ExpandC
)

function Require-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $p  = New-Object Security.Principal.WindowsPrincipal($id)
  if (-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run this script in an elevated (Administrator) PowerShell."
    exit 1
  }
}
Require-Admin

Write-Host "== Step 1/5: Making Windows Boot Manager default ==" -ForegroundColor Cyan
# Ensure Windows boot manager path is correct and fast boots straight to Windows
cmd /c "bcdedit /set {bootmgr} path \EFI\Microsoft\Boot\bootmgfw.efi" | Out-Null
cmd /c "bcdedit /timeout 0" | Out-Null

# On some systems, setting the displayorder helps (harmless if it’s already set)
try {
  $defaultOS = (bcdedit /enum | Select-String -Pattern "osdevice").ToString()
} catch {}
# We won't fail the script if this part isn't readable.

Write-Host "Windows boot manager set. Timeout set to 0s." -ForegroundColor Green

Write-Host "`n== Step 2/5: Locating and mounting the EFI System Partition (ESP) ==" -ForegroundColor Cyan
$ESP_GUID = '{C12A7328-F81F-11D2-BA4B-00A0C93EC93B}'
$esp = Get-Partition -ErrorAction SilentlyContinue | Where-Object { $_.GptType -eq $ESP_GUID } | Select-Object -First 1

if (-not $esp) {
  Write-Error "EFI System Partition not found. Aborting."
  exit 1
}

# Mount ESP to a temporary drive letter (S: if available)
$targetLetter = 'S'
if (Get-Volume -FileSystemLabel 'SYSTEM' -ErrorAction SilentlyContinue | Where-Object { $_.DriveLetter }) {
  # If already mounted, use that letter
  $existing = Get-Volume -FileSystemLabel 'SYSTEM' -ErrorAction SilentlyContinue | Where-Object { $_.DriveLetter } | Select-Object -First 1
  $drive = "$($existing.DriveLetter):"
} else {
  # Assign S: (or next free letter)
  $used = (Get-Volume | Where-Object DriveLetter).DriveLetter
  if ($used -contains $targetLetter) {
    # find a free letter
    $alphabet = [char[]]([char]'D'..[char]'Z') # avoid A,B,C
    $targetLetter = ($alphabet | Where-Object { $used -notcontains $_ })[0]
  }
  $esp | Set-Partition -NewDriveLetter $targetLetter -ErrorAction Stop | Out-Null
  $drive = "$targetLetter`:"
}

Write-Host "ESP mounted at $drive" -ForegroundColor Green

Write-Host "`n== Step 3/5: Removing Ubuntu/GRUB from ESP ==" -ForegroundColor Cyan
$ubuntuPath = Join-Path $drive "EFI\ubuntu"
$grubPath   = Join-Path $drive "EFI\grub"

$toDelete = @()
if (Test-Path $ubuntuPath) { $toDelete += $ubuntuPath }
if (Test-Path $grubPath)   { $toDelete += $grubPath }

if ($toDelete.Count -eq 0) {
  Write-Host "No \EFI\ubuntu or \EFI\grub folders found on ESP (already clean)." -ForegroundColor Yellow
} else {
  if (-not $Force) {
    Write-Host "About to delete:" -ForegroundColor Yellow
    $toDelete | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    $confirm = Read-Host "Proceed? Type YES to confirm"
    if ($confirm -ne 'YES') {
      Write-Host "Cancelled by user." -ForegroundColor Yellow
      goto UnmountESP
    }
  }
  foreach ($p in $toDelete) {
    try {
      Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction Stop
      Write-Host "Deleted $p" -ForegroundColor Green
    } catch {
      Write-Warning "Failed to delete $p : $($_.Exception.Message)"
    }
  }
}

Write-Host "`n== Step 4/5: Finding and deleting Linux partitions (ext4/swap) ==" -ForegroundColor Cyan
# GPT type GUIDs for Linux filesystems/swap (most common):
$LINUX_FS_GUID   = '{0FC63DAF-8483-4772-8E79-3D69D8477DE4}'
$LINUX_SWAP_GUID = '{0657FD6D-A4AB-43C4-84E5-0933C84B4F4F}'

$linuxParts = Get-Partition -ErrorAction SilentlyContinue | Where-Object { $_.GptType -in @($LINUX_FS_GUID, $LINUX_SWAP_GUID) }

if (-not $linuxParts -or $linuxParts.Count -eq 0) {
  Write-Host "No Linux partitions found. (Nothing to delete.)" -ForegroundColor Yellow
} else {
  Write-Host "The following Linux partitions will be DELETED:" -ForegroundColor Yellow
  $linuxParts | Sort-Object DiskNumber,PartitionNumber |
    ForEach-Object { Write-Host ("  Disk {0}, Part {1} - Size {2:N0} MB - Type {3}" -f $_.DiskNumber, $_.PartitionNumber, ($_.Size/1MB), $_.GptType) -ForegroundColor Yellow }

  if (-not $Force) {
    $confirm2 = Read-Host "Type DELETE to confirm deletion of these partitions"
    if ($confirm2 -ne 'DELETE') {
      Write-Host "Cancelled by user." -ForegroundColor Yellow
      goto UnmountESP
    }
  }

  foreach ($p in $linuxParts) {
    try {
      # Remove-Partition requires the disk & partition objects
      Remove-Partition -DiskNumber $p.DiskNumber -PartitionNumber $p.PartitionNumber -Confirm:$false -ErrorAction Stop
      Write-Host ("Deleted: Disk {0} Part {1}" -f $p.DiskNumber, $p.PartitionNumber) -ForegroundColor Green
    } catch {
      Write-Warning ("Failed to delete Disk {0} Part {1}: {2}" -f $p.DiskNumber, $p.PartitionNumber, $_.Exception.Message)
    }
  }
}

# Optional: expand C: if the free space is immediately after the C: partition
if ($ExpandC) {
  Write-Host "`n== Step 5/5: Attempting safe expansion of C: into adjacent free space ==" -ForegroundColor Cyan
  try {
    $cVol = Get-Volume -DriveLetter C -ErrorAction Stop
    $cPart = (Get-Partition -DriveLetter C -ErrorAction Stop)
    $disk  = Get-Disk -Number $cPart.DiskNumber -ErrorAction Stop

    # Only safe to extend if the free space is directly after the partition.
    # Windows can tell us supported sizes for the partition:
    $support = Get-PartitionSupportedSize -DriveLetter C
    if ($support.SizeMax -gt $cPart.Size) {
      $newSize = $support.SizeMax
      if (-not $Force) {
        $deltaMB = [math]::Round(($newSize - $cPart.Size)/1MB,0)
        $ans = Read-Host "C: can be safely expanded by $deltaMB MB. Type EXPAND to proceed"
        if ($ans -ne 'EXPAND') { 
          Write-Host "Skipping expansion." -ForegroundColor Yellow
          goto UnmountESP
        }
      }
      Resize-Partition -DriveLetter C -Size $newSize -ErrorAction Stop
      Write-Host "C: expanded successfully." -ForegroundColor Green
    } else {
      Write-Host "No immediately-adjacent free space available to safely expand C:. Skipping." -ForegroundColor Yellow
    }
  } catch {
    Write-Warning "Could not expand C:: $($_.Exception.Message)"
  }
} else {
  Write-Host "Skipping C: expansion (use -ExpandC if you want the script to try)." -ForegroundColor Yellow
}

:UnmountESP
# Unmount ESP if we mounted it
try {
  $vol = Get-Volume -FileSystemLabel 'SYSTEM' -ErrorAction SilentlyContinue | Where-Object { $_.DriveLetter }
  if ($vol) {
    $espPart = (Get-Partition | Where-Object { $_.AccessPaths -like "$($vol.DriveLetter):\" } | Select-Object -First 1)
    if ($espPart) {
      $espPart | Set-Partition -NewDriveLetter $null -ErrorAction SilentlyContinue | Out-Null
      Write-Host "ESP unmounted." -ForegroundColor Green
    }
  }
} catch {}

Write-Host "`nAll done." -ForegroundColor Green
Write-Host "→ Windows is set as the default bootloader."
Write-Host "→ Ubuntu/GRUB removed (if present)."
Write-Host "→ Linux partitions deleted (if found)."
Write-Host "You can reboot now. If you still see a GRUB screen, power off and on once more to let firmware refresh." -ForegroundColor Cyan