
import os

spec_path = 'theus/Documents/POP_specification.md'
supplement_path = 'theus/Documents/POP_specification_supplement.md'

# Read the main spec
with open(spec_path, 'r', encoding='utf-8') as f:
    spec_lines = f.readlines()

# Find the start of the old Epilogue to truncate
truncate_index = -1
for i, line in enumerate(spec_lines):
    if "Lời kết cho Bộ Đặc tả (Epilogue)" in line:
        # We want to remove the section header "## 🟩 **3. Lời kết..." and everything after
        # But we need to check if there are empty lines or dashes before it.
        # Let's look for the preceding line "---" if possible.
        if i > 0 and "---" in spec_lines[i-2]:
            truncate_index = i - 2
        else:
            truncate_index = i
        break

if truncate_index != -1:
    print(f"Truncating main spec at line {truncate_index}")
    new_spec_lines = spec_lines[:truncate_index]
else:
    print("Old Epilogue not found, appending to end.")
    new_spec_lines = spec_lines

# Read the supplement
with open(supplement_path, 'r', encoding='utf-8') as f:
    supplement_content = f.read()

# Filter out the YAML frontmatter and Title from supplement if present
# The supplement starts with "# 📘 **POP Specification — Tập 3..."
# We want to skip the header and start from "# **Chương 15..."
# But wait, looking at the file content in Step 191/192:
# It starts with metadata block, then title.
# We should parse it to find "# **Chương 15"

supplement_lines = supplement_content.splitlines()
start_append_index = 0
for i, line in enumerate(supplement_lines):
    if "# **Chương 15" in line:
        start_append_index = i
        break

# If we found the chapter start, take from there. 
# We should also add a "---" separator if missing.
if start_append_index > 0:
    content_to_append = "\n\n" + "\n".join(supplement_lines[start_append_index:])
else:
    content_to_append = "\n" + supplement_content

# Write back to POP_specification.md
with open(spec_path, 'w', encoding='utf-8') as f:
    f.writelines(new_spec_lines)
    f.write(content_to_append)

print("Successfully merged supplement into POP_specification.md")
