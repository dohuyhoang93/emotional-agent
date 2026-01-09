# Fix all process contracts by adding parent context paths
# Strategy: Add 'domain_ctx' and 'global_ctx' to inputs/outputs wherever child paths exist

$processFiles = Get-ChildItem -Path "C:\Users\dohuy\Downloads\emotional-agent\src" -Recurse -Filter "*.py" | 
    Where-Object { $_.Name -match "^p.*\.py$|processes" }

$fixedCount = 0

foreach ($file in $processFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $original = $content
    
    # Pattern 1: Add 'domain_ctx' to inputs if 'domain_ctx.' exists but not 'domain_ctx' alone
    if ($content -match "inputs=\[" -and $content -match "'domain_ctx\." -and $content -notmatch "inputs=\[[^\]]*'domain_ctx'[,\]]") {
        $content = $content -replace "(inputs=\[)", "`$1'domain_ctx', "
    }
    
    # Pattern 2: Add 'global_ctx' to inputs if 'global_ctx.' exists but not 'global_ctx' alone  
    if ($content -match "inputs=\[" -and $content -match "'global_ctx\." -and $content -notmatch "inputs=\[[^\]]*'global_ctx'[,\]]") {
        $content = $content -replace "(inputs=\[)", "`$1'global_ctx', "
    }
    
    # Pattern 3: Add 'domain_ctx' to outputs if 'domain_ctx.' or 'domain.' exists
    if ($content -match "outputs=\[" -and ($content -match "'domain_ctx\." -or $content -match "'domain\.") -and $content -notmatch "outputs=\[[^\]]*'domain_ctx'[,\]]") {
        $content = $content -replace "(outputs=\[)", "`$1'domain_ctx', "
    }
    
    # Pattern 4: Add 'global_ctx' to outputs if 'global_ctx.' or 'global.' exists
    if ($content -match "outputs=\[" -and ($content -match "'global_ctx\." -or $content -match "'global\.") -and $content -notmatch "outputs=\[[^\]]*'global_ctx'[,\]]") {
        $content = $content -replace "(outputs=\[)", "`$1'global_ctx', "
    }
    
    if ($content -ne $original) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8
        Write-Host "Fixed: $($file.Name)"
        $fixedCount++
    }
}

Write-Host "`nTotal fixed: $fixedCount files"
