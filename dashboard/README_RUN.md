
## 🖥️ Cách chạy Dashboard (Thủ công)

Nếu Dashboard bị tắt, bạn có thể khởi động lại bằng cách mở 2 cửa sổ Terminal (PowerShell/CMD) riêng biệt:

### 1. Khởi động Backend (Server Nhận dữ liệu)
Cửa sổ này sẽ đọc file `metrics.json` từ thí nghiệm và gửi qua WebSocket.
```powershell
cd c:\Users\dohoang\projects\EmotionAgent
python -m uvicorn src.dashboard.server:socket_app --reload --host 0.0.0.0 --port 8000
```

### 2. Khởi động Frontend (Giao diện Web)
Cửa sổ này chạy giao diện Next.js tại cổng 3000.
```powershell
cd c:\Users\dohoang\projects\EmotionAgent\dashboard
npm run dev
```

Sau đó truy cập: [http://localhost:3000](http://localhost:3000)
