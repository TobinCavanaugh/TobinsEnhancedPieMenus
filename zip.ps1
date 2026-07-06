$ZipName = "TobinsEnhancedPieMenus.zip"

if (Test-Path $ZipName) { Remove-Item $ZipName }

# 1. Define what to exclude (relative to the current folder)
$Exclusions = @(
    ".gitignore",
    "zip.ps1",
    $ZipName,
    "TestProjects/*",
    ".git/*"
)

# 2. Get all local files recursively, filtering out the exclusions
$Files = Get-ChildItem -Path . -Recurse -File | Where-Object {
    $RelativePath = $_.FullName.Replace("$PWD\", "").Replace("\", "/")
    
    # Check if the path matches any exclusion pattern
    $Keep = $true
    foreach ($Pattern in $Exclusions) {
        if ($RelativePath -like $Pattern) {
            $Keep = $false
            break
        }
    }
    $Keep
} | Select-Object -ExpandProperty FullName

# 3. Compress the remaining local files
if ($Files) {
    Compress-Archive -Path $Files -DestinationPath $ZipName
}