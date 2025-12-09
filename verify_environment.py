import json
from environment import GridWorld

def expand_line(line_def):
    coords = []
    start = line_def['start']
    end = line_def['end']
    y1, x1 = start
    y2, x2 = end

    if y1 == y2: # Horizontal
        for x in range(min(x1, x2), max(x1, x2) + 1):
            coords.append([y1, x])
    elif x1 == x2: # Vertical
        for y in range(min(y1, y2), max(y1, y2) + 1):
            coords.append([y, x1])
    return coords


def verify_maze_initialization(config_path: str, experiment_name: str):
    """
    Tải cấu hình, khởi tạo GridWorld và in ra trạng thái của nó để xác minh.
    """
    print(f"--- BẮT ĐẦU XÁC MINH KHỞI TẠO MÊ CUNG CHO '{experiment_name}' ---")
    print(f"--- Tải cấu hình từ: {config_path} ---")

    # Tải cấu hình từ file
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            full_config = json.load(f)
    except Exception as e:
        print(f"LỖI: Không thể đọc file cấu hình {config_path}: {e}")
        return

    # Tìm cấu hình thử nghiệm cụ thể
    experiment_params = None
    for exp in full_config.get("experiments", []):
        if exp.get("name") == experiment_name:
            experiment_params = exp.get("parameters")
            break
    
    if not experiment_params:
        print(f"LỖI: Không tìm thấy thử nghiệm có tên '{experiment_name}' trong {config_path}")
        return

    settings = {"environment_config": experiment_params.get("environment_config", {})}

    # 1. Khởi tạo GridWorld
    print("\n1. Đang khởi tạo GridWorld...")
    try:
        grid = GridWorld(settings)
        print("   -> Khởi tạo GridWorld thành công.")
    except Exception as e:
        print(f"   -> LỖI trong quá trình khởi tạo GridWorld: {e}")
        return

    # 2. Render mê cung ở trạng thái ban đầu
    print("\n2. Render mê cung ở trạng thái ban đầu (A: Agent, S: Switch, G: Goal, #: Tường tĩnh, %: Tường động):")
    grid.render()
    
    print("\n--- KẾT THÚC XÁC MINH ---")
    print("Phân tích: Vui lòng kiểm tra bản đồ trực quan bên trên để đảm bảo mê cung được thiết kế đúng như mong đợi.")
    print("   - Agent 'A' không bị nhốt trong một chiếc lồng kín.")
    print("   - Các tường động '%' được đặt ở các vị trí chiến lược.")
    print("   - Lối đi đến đích 'G' không bị chặn hoàn toàn bởi tường tĩnh.")


if __name__ == "__main__":
    # Point to the new balanced maze v2 config
    verify_maze_initialization(
        config_path="multi_agent_complex_maze.json",
        experiment_name="LogicGate_Test_Run"
    )
