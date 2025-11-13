import json

# --- Các process ---
def boil_water(ctx):
    print("Đun nước sôi...")
    ctx["water"] = "hot"
    return ctx

def brew_coffee(ctx):
    print("Pha cà phê...")
    ctx["coffee"] = "brewed"
    return ctx

def add_sugar(ctx):
    print("Thêm đường...")
    ctx["coffee"] += " + sugar"
    return ctx

def add_milk(ctx):
    print("Thêm sữa...")
    ctx["coffee"] += " + milk"
    return ctx

def taste_test(ctx):
    print("Uống thử:", ctx["coffee"])
    return ctx

def enjoy(ctx):
    print("Thưởng thức:", ctx["coffee"])
    return ctx

# Map tên -> hàm
REGISTRY = {
    "boil_water": boil_water,
    "brew_coffee": brew_coffee,
    "add_sugar": add_sugar,
    "add_milk": add_milk,
    "taste_test": taste_test,
    "enjoy": enjoy,
}

# --- Engine chạy workflow ---
def run_workflow(workflow, ctx):
    for step in workflow:
        if isinstance(step, str):          # bước đơn
            ctx = REGISTRY[step](ctx)
        elif isinstance(step, list):       # bước song song (chạy tuần tự cho dễ hiểu)
            for s in step:
                ctx = REGISTRY[s](ctx)
    return ctx

if __name__ == "__main__":
    choice = input("Chọn loại (black/milk): ").strip().lower()
    filename = f"{choice}.json"
    with open(filename, "r", encoding="utf-8") as f:
        wf = json.load(f)

    print(f"\n=== Pha {wf['name']} ===")
    run_workflow(wf["steps"], {"coffee": ""})
