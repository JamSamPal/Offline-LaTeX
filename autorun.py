import subprocess, datetime, os, sys, shutil, re

RED = "\033[91m"
RESET = "\033[0m"


if len(sys.argv) < 2:
    print("Usage: python autolatex <path/to/file.tex> [<path/to/output/directory>]")
    sys.exit(1)

filename = sys.argv[1]

if not os.path.exists(filename):
    print(f"Error: file '{filename}' not found.")
    sys.exit(1)

if len(sys.argv) > 2:
    pdf_dir = sys.argv[2]
    os.makedirs(pdf_dir, exist_ok=True)
else:
    pdf_dir = os.path.dirname(os.path.abspath(filename))

print(f"Output directory '{pdf_dir}'")

# Allow user to save a history
history_dir = os.path.join(os.path.dirname(os.path.abspath(filename)), "history")
os.makedirs(history_dir, exist_ok=True)

print(f"Watching {filename} for changes... (Ctrl+C to quit)")
print("Press 's' + Enter at any time to save a history snapshot.")
last_mtime = None
while True:
    try:
        # Non-blocking input for saving history
        import select, sys as sys_in

        print("\r", end="")  # keep terminal neat
        if sys_in.stdin in select.select([sys_in.stdin], [], [], 1)[0]:
            line = sys_in.stdin.readline().strip()
            if line.lower() == "s":
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                basename = os.path.basename(filename)
                snapshot_file = os.path.join(history_dir, f"{basename}_{timestamp}.tex")
                shutil.copy(filename, snapshot_file)
                # Also copy PDF if exists
                pdf_file = os.path.splitext(filename)[0] + ".pdf"
                if os.path.exists(os.path.join(pdf_dir, os.path.basename(pdf_file))):
                    shutil.copy(
                        os.path.join(pdf_dir, os.path.basename(pdf_file)),
                        os.path.join(
                            history_dir, f"{os.path.basename(pdf_file)}_{timestamp}.pdf"
                        ),
                    )
                print(f"Saved snapshot: {snapshot_file}")

        # Check for file changes
        mtime = os.path.getmtime(filename)
        if mtime != last_mtime:
            last_mtime = mtime
            print("Compiling...")
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory",
                    pdf_dir,
                    filename,
                ],
                capture_output=True,
                text=True,
            )

            # Parse errors with line numbers
            errors = []
            lines = result.stdout.splitlines()
            for i, l in enumerate(lines):
                if l.startswith("!"):
                    msg = l
                    line_info = ""
                    # Check next few lines for "l.<number> ..."
                    for j in range(i + 1, min(i + 5, len(lines))):
                        m = re.match(r"l\.(\d+)\s+(.*)", lines[j])
                        if m:
                            line_info = f"Line {m.group(1)}: {m.group(2)}"
                            break
                    errors.append((msg, line_info))

            if errors:
                print(f"{RED} Errors detected:{RESET}")
                for e, info in errors:
                    if info:
                        print(f"{RED}{e} ({info}){RESET}")
                    else:
                        print(f"{RED}{e}{RESET}")
            else:
                print(f"PDF updated in {pdf_dir}")
    except KeyboardInterrupt:
        print("\nStopped.")
        break
