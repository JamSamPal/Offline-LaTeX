import subprocess, time, os

filename = "example.tex"

print(f"Watching {filename} for changes... (Ctrl+C to quit)")

last_mtime = None
while True:
    try:
        mtime = os.path.getmtime(filename)
        if mtime != last_mtime:
            last_mtime = mtime
            print("Compiling...")
            subprocess.run(["pdflatex", "-interaction=nonstopmode", filename])
            print("PDF updated.")
        time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
        break
