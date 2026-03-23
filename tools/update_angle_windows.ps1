# Builds ANGLE OpenGL ES libraries for Windows via vcpkg and stages the
# artifacts to build/angle-artifacts/ for pickup by the build system.
#
# Invoked remotely via: make update-angle-windows
# Do not run this script directly.

$ErrorActionPreference = 'Stop'

# Repo root is one level up from the tools/ directory containing this script.
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$StagingDir = "$RepoRoot\build\angle-artifacts"

$Triplets = @(
    @{ Name = 'x64-windows';   LibArch = 'x64';   DllArch = 'x64'   },
    @{ Name = 'x86-windows';   LibArch = 'Win32';  DllArch = 'Win32'  },
    @{ Name = 'arm64-windows'; LibArch = 'arm64';  DllArch = 'arm64'  }
)

# Find git.exe - checks standard install locations and VS's bundled copy.
function Find-Git {
    $candidates = @(
        'C:\Program Files\Git\cmd\git.exe',
        'C:\Program Files\Git\bin\git.exe',
        'C:\Program Files (x86)\Git\cmd\git.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\Git\cmd\git.exe')
    )
    foreach ($vsEdition in @('Community', 'Professional', 'Enterprise', 'BuildTools')) {
        $candidates += (
            "C:\Program Files\Microsoft Visual Studio\2022\$vsEdition\" +
            'Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\' +
            'Team Explorer\Git\cmd\git.exe'
        )
    }
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    return $null
}

$gitExe = Find-Git
if (-not $gitExe) {
    throw (
        'git.exe not found. ' +
        'Install Git for Windows from https://git-scm.com/ ' +
        'or include the Git component in your Visual Studio installation.'
    )
}
Write-Host "Using git: $gitExe"
# Add git to PATH so vcpkg can find it internally.
$env:PATH = "$(Split-Path $gitExe);" + $env:PATH

# Clean and recreate staging dir.
if (Test-Path $StagingDir) {
    Remove-Item $StagingDir -Recurse -Force
}
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null

# Use a short root-level base path for the vcpkg temp dir. The cloudshell
# workspace path is already long (~80 chars), and vcpkg's virtualenv pip wheel
# extraction creates deep subdirectories that exceed MAX_PATH (260 chars) for
# the arm64 triplet if rooted inside the workspace. C:\abt (angle build temp)
# keeps the prefix short enough to stay under the limit.
$TempBase = 'C:\abt'
New-Item -ItemType Directory -Path $TempBase -Force -ErrorAction SilentlyContinue | Out-Null

# Clean up any stale vcpkg temp dirs left by previously interrupted runs.
# (The finally block handles normal cleanup, but an external kill can bypass it.)
Get-ChildItem -Path $TempBase -Directory -Filter 'angle-*' -ErrorAction SilentlyContinue |
    ForEach-Object {
        Write-Host "Removing stale vcpkg dir: $($_.FullName)"
        & 'cmd.exe' /c "rd /s /q `"$($_.FullName)`""
    }

$TempDir = "$TempBase\angle-$([System.IO.Path]::GetRandomFileName())"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
$VcpkgDir = Join-Path $TempDir 'vcpkg'

Write-Host ""
Write-Host "Setting up vcpkg in: $VcpkgDir"
Write-Host ""

try {
    # Clone and bootstrap vcpkg.
    & $gitExe clone https://github.com/microsoft/vcpkg.git $VcpkgDir
    if ($LASTEXITCODE -ne 0) { throw "git clone failed." }

    & "$VcpkgDir\bootstrap-vcpkg.bat" -disableMetrics
    if ($LASTEXITCODE -ne 0) { throw "vcpkg bootstrap failed." }

    foreach ($triplet in $Triplets) {
        $name = $triplet.Name
        Write-Host ""
        Write-Host "=== Building ANGLE for $name ==="
        Write-Host ""

        & "$VcpkgDir\vcpkg.exe" install "angle:$name" --no-binarycaching --no-print-usage --clean-after-build
        if ($LASTEXITCODE -ne 0) { throw "ANGLE build failed for $name." }

        $InstallDir = "$VcpkgDir\installed\$name"

        # Copy headers (identical across all triplets; overwriting is fine).
        foreach ($dir in @('EGL', 'GLES2', 'GLES3', 'KHR')) {
            $Src = "$InstallDir\include\$dir"
            $Dst = "$StagingDir\include\$dir"
            if (-not (Test-Path $Src)) { throw "Expected header dir not found: $Src" }
            Write-Host "  Staging headers: $dir"
            Copy-Item $Src $Dst -Recurse -Force
        }

        # Copy .lib files.
        $LibDst = "$StagingDir\lib\$($triplet.LibArch)"
        New-Item -ItemType Directory -Path $LibDst -Force | Out-Null
        foreach ($lib in @('libEGL.lib', 'libGLESv2.lib')) {
            $Src = "$InstallDir\lib\$lib"
            if (-not (Test-Path $Src)) { throw "Expected lib not found: $Src" }
            Write-Host "  Staging $lib -> lib\$($triplet.LibArch)"
            Copy-Item $Src $LibDst -Force
        }

        # Copy .dll and .pdb files.
        $DllDst = "$StagingDir\dll\$($triplet.DllArch)"
        New-Item -ItemType Directory -Path $DllDst -Force | Out-Null
        foreach ($file in @('libEGL.dll', 'libGLESv2.dll', 'libEGL.pdb', 'libGLESv2.pdb')) {
            $Src = "$InstallDir\bin\$file"
            if (-not (Test-Path $Src)) { throw "Expected file not found: $Src" }
            Write-Host "  Staging $file -> dll\$($triplet.DllArch)"
            Copy-Item $Src $DllDst -Force
        }

    }

    # Copy build logs (useful for diagnosing failures).
    $LogSrc = "$VcpkgDir\buildtrees\angle"
    $LogDst = "$StagingDir\logs"
    if (Test-Path $LogSrc) {
        New-Item -ItemType Directory -Path $LogDst -Force | Out-Null
        Get-ChildItem -Path $LogSrc -Filter '*.log' | ForEach-Object {
            Write-Host "  Staging log: $($_.Name)"
            Copy-Item $_.FullName $LogDst -Force
        }
    }

    Write-Host ""
    Write-Host "ANGLE artifacts staged to: $StagingDir"
    Write-Host ""

} finally {
    # Always clean up vcpkg temp dir.
    # Use cmd.exe rd instead of Remove-Item because vcpkg's bundled cmake
    # includes HTML docs with filenames that exceed MAX_PATH (260 chars),
    # which causes Remove-Item to fail with DirectoryNotFoundException.
    if (Test-Path $TempDir) {
        Write-Host "Cleaning up vcpkg temp dir..."
        & 'cmd.exe' /c "rd /s /q `"$TempDir`""
    }
}
