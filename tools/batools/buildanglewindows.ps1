# Builds ANGLE OpenGL ES libraries for Windows via vcpkg and stages the
# artifacts to build/angle-windows-artifacts/ for pickup by the build system.
#
# PowerShell (rather than a Python pcommand) because it must run natively on
# the windows host, across the WSL boundary from our make/python tooling.
# Invoked remotely via 'make _update-angle-windows'; do not run directly.

$ErrorActionPreference = 'Stop'

# Repo root is two levels up from the tools/batools/ dir holding this script.
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$StagingDir = "$RepoRoot\build\angle-windows-artifacts"

$Triplets = @(
    @{ Name = 'x64-windows';   LibArch = 'x64';   DllArch = 'x64'   },
    @{ Name = 'x86-windows';   LibArch = 'Win32';  DllArch = 'Win32'  },
    @{ Name = 'arm64-windows'; LibArch = 'arm64';  DllArch = 'arm64'  }
)

# Our own patches to the ANGLE source, applied through vcpkg's angle port
# (each is dropped into ports/angle and added to its PATCHES list). Kept
# inline so this script stays the one file synced to the build host. Each
# must apply cleanly to the ANGLE commit the port pins; a port update that
# breaks one fails the build loudly, which is the prompt to rebase or drop
# it. See docs/design/angle-windows.md ("Local patches").
$AnglePatches = @(
    @{
        # D3D11: the input-layout cache key (PackedAttributeLayout) is
        # hashed as raw bytes but had 4 uninitialized padding bytes, so
        # equal keys could hash differently; the cache's index and list
        # drifted apart and a lookup could return a destroyed entry. In the
        # field: access violation in libGLESv2.dll,
        # StateManager11::syncVertexBuffersAndInputLayout, any GPU vendor.
        # Not fixed upstream as of 2026-10.
        Name = 'ba-001-input-layout-key-padding.patch'
        Body = @'
--- a/src/libANGLE/renderer/d3d/d3d11/InputLayoutCache.h
+++ b/src/libANGLE/renderer/d3d/d3d11/InputLayoutCache.h
@@ -39,9 +39,18 @@

     bool operator==(const PackedAttributeLayout &other) const;

-    uint32_t numAttributes;
+    // 64-bit so the struct has no padding bytes. std::hash below hashes
+    // the struct's raw bytes, and with a 32-bit count the 4 padding bytes
+    // before attributeData were left uninitialized: equal layouts hashed
+    // differently, the layout cache's index and list drifted apart, and a
+    // lookup could return an already-destroyed entry (null deref in
+    // StateManager11::syncVertexBuffersAndInputLayout).
+    uint64_t numAttributes;
     gl::AttribArray<uint64_t> attributeData;
 };
+static_assert(sizeof(PackedAttributeLayout) ==
+                  sizeof(uint64_t) + sizeof(gl::AttribArray<uint64_t>),
+              "PackedAttributeLayout is hashed as raw bytes; it must have no padding.");
 }  // namespace rx

 namespace std
'@
    }
)

# Find git.exe - checks standard install locations and VS's bundled copy.
function Find-Git {
    $candidates = @(
        'C:\Program Files\Git\cmd\git.exe',
        'C:\Program Files\Git\bin\git.exe',
        'C:\Program Files (x86)\Git\cmd\git.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\Git\cmd\git.exe')
    )
    foreach ($vsVersion in @('18', '2022')) {
        foreach ($vsEdition in @('Community', 'Professional', 'Enterprise', 'BuildTools')) {
            $candidates += (
                "C:\Program Files\Microsoft Visual Studio\$vsVersion\$vsEdition\" +
                'Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\' +
                'Team Explorer\Git\cmd\git.exe'
            )
        }
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

    # Add our own ANGLE patches to the port (see $AnglePatches above).
    $PortDir = "$VcpkgDir\ports\angle"
    $PortFile = "$PortDir\portfile.cmake"
    $PortLines = [System.Collections.Generic.List[string]](Get-Content $PortFile)
    # The first PATCHES list in the portfile belongs to the vcpkg_from_github
    # call that fetches ANGLE itself.
    $PatchesIdx = -1
    for ($i = 0; $i -lt $PortLines.Count; $i++) {
        if ($PortLines[$i] -match '^\s*PATCHES\s*$') { $PatchesIdx = $i; break }
    }
    if ($PatchesIdx -lt 0) {
        throw "No PATCHES list found in $PortFile; update the patch injection."
    }
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    foreach ($patch in $AnglePatches) {
        Write-Host "Adding ANGLE patch: $($patch.Name)"
        # LF endings and no BOM, whatever this script was checked out with.
        $Body = ($patch.Body -replace "`r`n", "`n") + "`n"
        [System.IO.File]::WriteAllText("$PortDir\$($patch.Name)", $Body, $Utf8NoBom)
        # Appended after the port's own patches so ours apply last.
        $InsertAt = $PatchesIdx + 1
        while ($InsertAt -lt $PortLines.Count -and
               $PortLines[$InsertAt] -match '^\s+\S+\.patch\s*$') { $InsertAt++ }
        $PortLines.Insert($InsertAt, "        $($patch.Name)")
    }
    [System.IO.File]::WriteAllLines($PortFile, $PortLines, $Utf8NoBom)

    # Set up overlay triplets: identical to the stock ones except zlib is
    # linked statically. Our staged ANGLE DLLs must not carry an external
    # zlib runtime dependency — we ship only libEGL.dll/libGLESv2.dll, and
    # vcpkg's zlib DLL name is not stable (it changed zlib1.dll -> z.dll in
    # 2026, which broke shipped builds; the old name was only ever
    # accidentally satisfied by the Python distribution's zlib1.dll).
    $TripletDir = Join-Path $TempDir 'triplets'
    New-Item -ItemType Directory -Path $TripletDir -Force | Out-Null
    foreach ($triplet in $Triplets) {
        $name = $triplet.Name
        Copy-Item "$VcpkgDir\triplets\$name.cmake" "$TripletDir\$name.cmake"
        Add-Content "$TripletDir\$name.cmake" @"

if(PORT STREQUAL "zlib")
    set(VCPKG_LIBRARY_LINKAGE static)
endif()
"@
    }

    foreach ($triplet in $Triplets) {
        $name = $triplet.Name
        Write-Host ""
        Write-Host "=== Building ANGLE for $name ==="
        Write-Host ""

        & "$VcpkgDir\vcpkg.exe" install "angle:$name" --overlay-triplets "$TripletDir" --no-binarycaching --no-print-usage --clean-after-build
        if ($LASTEXITCODE -ne 0) { throw "ANGLE build failed for $name." }

        $InstallDir = "$VcpkgDir\installed\$name"

        # Copy headers (identical across all triplets; overwriting is fine).
        foreach ($dir in @('EGL', 'GLES2', 'GLES3', 'KHR')) {
            $Src = "$InstallDir\include\$dir"
            $Dst = "$StagingDir\include\$dir"
            if (-not (Test-Path $Src)) { throw "Expected header dir not found: $Src" }
            Write-Host "  Staging headers: $dir"
            # Remove any existing destination first; Copy-Item copies *into*
            # an existing dir (yielding nested EGL\EGL\ from the 2nd/3rd
            # triplets) rather than replacing it.
            if (Test-Path $Dst) { Remove-Item $Dst -Recurse -Force }
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

    Write-Host ""
    Write-Host "ANGLE artifacts staged to: $StagingDir"
    Write-Host ""

} finally {
    # Stage build logs BEFORE the cleanup below nukes them. This has to
    # live in the finally: a *failed* build is exactly when the logs are
    # wanted, and vcpkg writes the compiler output to
    # buildtrees\angle\install-<triplet>-out.log rather than to stdout, so
    # without this a failure leaves nothing to diagnose from (hit on
    # 2026-09-23 -- a build error was unrecoverable because cleanup had
    # already run).
    $LogSrc = "$VcpkgDir\buildtrees\angle"
    $LogDst = "$StagingDir\logs"
    if (Test-Path $LogSrc) {
        New-Item -ItemType Directory -Path $LogDst -Force | Out-Null
        Get-ChildItem -Path $LogSrc -Filter '*.log' | ForEach-Object {
            Write-Host "  Staging log: $($_.Name)"
            Copy-Item $_.FullName $LogDst -Force
        }
    }

    # Always clean up vcpkg temp dir.
    # Use cmd.exe rd instead of Remove-Item because vcpkg's bundled cmake
    # includes HTML docs with filenames that exceed MAX_PATH (260 chars),
    # which causes Remove-Item to fail with DirectoryNotFoundException.
    if (Test-Path $TempDir) {
        Write-Host "Cleaning up vcpkg temp dir..."
        & 'cmd.exe' /c "rd /s /q `"$TempDir`""
    }
}
