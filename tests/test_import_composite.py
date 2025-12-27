
print("Start Import...")
try:
    from src.processes import snn_composite_theus
    print("Import Successful!")
except Exception as e:
    print(f"Import Failed: {e}")
except KeyboardInterrupt:
    print("Import Interrupted")
