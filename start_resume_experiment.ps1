Set-Location "c:\Users\dohoang\projects\EmotionAgent"
$Python = "c:\Users\dohoang\projects\EmotionAgent\.venv\Scripts\python.exe"
$Log = "logs/maze_resume_ep450.log"
$Err = "logs/maze_resume_ep450.err"

# Phải dùng cmd /c để hỗ trợ redirect (> và 2>) vì Win32_Process.Create không hỗ trợ trực tiếp.
# NOTE: Dùng dấu ngoặc kép bọc đường dẫn dài và thoát chuỗi cẩn thận.
$Command = "cmd /c `"$Python run_experiments.py --config experiments.json --resume results/multi_agent_complex_maze/checkpoint_ep_450 --start-episode 451 --headless > $Log 2> $Err`""

# Tạo cấu hình khởi động ẩn (Hidden) để tránh nhận tín hiệu đóng cửa sổ console.
# Phải ép kiểu [uint16] để tránh lỗi Type mismatch trong Invoke-CimMethod.
$Startup = New-CimInstance -ClassName Win32_ProcessStartup -Property @{ShowWindow = [uint16]0} -ClientOnly

$Result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $Command
    CurrentDirectory = "c:\Users\dohoang\projects\EmotionAgent"
    ProcessStartupInformation = $Startup
}

if ($Result.ReturnValue -eq 0) {
    if ($null -ne $Result.ProcessId) {
        $Result.ProcessId | Out-File "logs/maze_resume_ep450.pid"
        Write-Host "Tiến trình độc lập (Hidden) đã khởi tạo thành công. PID: $($Result.ProcessId)" -ForegroundColor Green
    } else {
        Write-Host "Tiến trình đã khởi tạo nhưng không lấy được PID ngay lập tức." -ForegroundColor Yellow
    }
} else {
    Write-Error "Không thể khởi tạo tiến trình. ReturnValue: $($Result.ReturnValue)"
}
