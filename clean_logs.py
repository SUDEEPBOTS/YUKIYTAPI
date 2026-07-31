import re

with open("setup.sh", "r") as f:
    lines = f.readlines()

new_lines = []
logs_to_keep = [
    'log "Installing Python requirements..."',
    'log "Compiling High-Security Cython Native Binaries..."',
    'log "Wiping Raw C Source Files for extra security..."',
    'log "Port ${PORT} busy',
    'log "Found duplicate',
    'log "Starting ${APP_NAME}',
    'log "SUCCESS - test song',
    'log "All done.',
    'log "Project directory:'
]

for line in lines:
    if line.strip().startswith('log "'):
        keep = False
        for k in logs_to_keep:
            if k in line:
                keep = True
                break
        if not keep:
            continue
    new_lines.append(line)

# Add "Checking system dependencies..." at the start of main()
main_idx = -1
for i, line in enumerate(new_lines):
    if line.startswith("main() {"):
        main_idx = i
        break

if main_idx != -1:
    new_lines.insert(main_idx + 1, '    log "Checking system dependencies..."\n')

with open("setup.sh", "w") as f:
    f.writelines(new_lines)
