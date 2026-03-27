Set-Location "c:\Users\dohoang\projects\EmotionAgent"
$Python = "c:\Users\dohoang\projects\EmotionAgent\.venv\Scripts\python.exe"
$Log = "logs/maze_sanity_run.log"
$Err = "logs/maze_sanity_run.err"
$PidFile = "logs/maze_sanity_run.pid"

# Không truyền tham số --resume và --start-episode để chạy một experiment hoàn toàn mới từ đầu
$Command = "cmd /c `"$Python run_experiments.py --config experiments_sanity.json --headless > $Log 2> $Err`""

# Tạo cấu hình khởi động ẩn (Hidden) để tránh nhận tín hiệu đóng cửa sổ console.
$Startup = New-CimInstance -ClassName Win32_ProcessStartup -Property @{ShowWindow = [uint16]0} -ClientOnly

$Result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $Command
    CurrentDirectory = "c:\Users\dohoang\projects\EmotionAgent"
    ProcessStartupInformation = $Startup
}

if ($Result.ReturnValue -eq 0) {
    if ($null -ne $Result.ProcessId) {
        $Result.ProcessId | Out-File $PidFile
        Write-Host "Tiến trình độc lập chạy Sanity Check đã khởi tạo thành công. PID: $($Result.ProcessId)" -ForegroundColor Green
    } else {
        Write-Host "Tiến trình đã khởi tạo nhưng không lấy được PID ngay lập tức." -ForegroundColor Yellow
    }
} else {
    Write-Error "Không thể khởi tạo tiến trình. ReturnValue: $($Result.ReturnValue)"
}
