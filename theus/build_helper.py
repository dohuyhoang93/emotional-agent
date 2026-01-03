import subprocess
import os

print("Running maturin develop (direct log)...")
f_log = open("build_err.log", "w", encoding="utf-8")
try:
    # Use shell=True just in case, or False? True might help with environment?
    # No, keep False for safety.
    subprocess.run(["maturin", "develop"], stdout=f_log, stderr=subprocess.STDOUT, shell=False, check=True)
    print("Maturin finished.")
except Exception as e:
    f_log.write(f"\nEXCEPTION: {e}\n")
    print("Execution failed.")
finally:
    f_log.close()
