import subprocess, time, os, sys

if len(sys.argv) < 2:
    print("Usage: python autolatex <path/to/file.tex> [<path/to/output/directory>]")
    sys.exit(1)

filename = sys.argv[1]
pdfpath = sys.argv[1]

if not os.path.exists(filename):
    print(f"Error: file '{filename}' not found.")
    sys.exit(1)

if len(sys.argv) > 2:
    pdf_dir = sys.argv[2]
    os.makedirs(pdf_dir, exist_ok=True)
else:
    pdf_dir = os.path.dirname(os.path.abspath(filename))


print(f"Watching {filename} for changes... (Ctrl+C to quit)")

last_mtime = None
while True:
    try:
        mtime = os.path.getmtime(filename)
        if mtime != last_mtime:
            last_mtime = mtime
            print("Compiling...")
            subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory",
                    pdf_dir,
                    filename,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("PDF updated.")
        time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
        break
