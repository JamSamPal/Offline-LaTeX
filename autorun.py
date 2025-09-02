import subprocess, datetime, os, sys, shutil, re, select

RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def run_pdflatex(filename, pdf_dir):
    """Run pdflatex twice to resolve references."""
    for _ in range(2):
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
    return result


def run_bibtex(filename, pdf_dir):
    """Run bibtex on the .aux file (basename only)."""
    aux_basename = os.path.splitext(os.path.basename(filename))[0]
    result = subprocess.run(
        ["bibtex", aux_basename],
        cwd=pdf_dir,  # run in the output directory
        capture_output=True,
        text=True,
    )
    return result


def parse_latex_output(output):
    """Extract LaTeX errors and warnings with line numbers if possible."""
    errors = []
    warnings = []

    lines = output.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("!"):  # LaTeX error
            msg = l
            line_info = ""
            # look ahead for "l.<number>"
            for j in range(i + 1, min(i + 5, len(lines))):
                m = re.match(r"l\.(\d+)\s+(.*)", lines[j])
                if m:
                    line_info = f"Line {m.group(1)}: {m.group(2)}"
                    break
            errors.append((msg, line_info))
        elif "LaTeX Warning" in l:
            warnings.append(l)

    return errors, warnings


def main():
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

    # History snapshots
    history_dir = os.path.join(os.path.dirname(os.path.abspath(filename)), "history")
    os.makedirs(history_dir, exist_ok=True)

    print(f"Watching {filename} for changes... (Ctrl+C to quit)")
    print("Press 's' + Enter at any time to save a history snapshot.")
    last_mtime = None

    while True:
        try:
            # Non-blocking input for saving history
            if sys.stdin in select.select([sys.stdin], [], [], 1)[0]:
                line = sys.stdin.readline().strip()
                if line.lower() == "s":
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    basename = os.path.basename(filename)
                    snapshot_file = os.path.join(
                        history_dir, f"{basename}_{timestamp}.tex"
                    )
                    shutil.copy(filename, snapshot_file)

                    # Copy PDF if exists
                    pdf_file = os.path.splitext(filename)[0] + ".pdf"
                    pdf_target = os.path.join(pdf_dir, os.path.basename(pdf_file))
                    if os.path.exists(pdf_target):
                        shutil.copy(
                            pdf_target,
                            os.path.join(
                                history_dir,
                                f"{os.path.basename(pdf_file)}_{timestamp}.pdf",
                            ),
                        )
                    print(f"Saved snapshot: {snapshot_file}")

            # Check for file changes
            mtime = os.path.getmtime(filename)
            if mtime != last_mtime:
                last_mtime = mtime
                print("\nCompiling...")

                # Run LaTeX once (to generate .aux)
                result = run_pdflatex(filename, pdf_dir)

                # Run BibTeX if .aux exists
                aux_file = os.path.join(
                    pdf_dir, os.path.splitext(os.path.basename(filename))[0] + ".aux"
                )
                if os.path.exists(aux_file):
                    bib_result = run_bibtex(filename, pdf_dir)
                    if bib_result.returncode != 0:
                        print(f"{RED}BibTeX error:{RESET}\n{bib_result.stdout}")
                    elif "error" in bib_result.stdout.lower():
                        print(f"{RED}BibTeX messages:{RESET}\n{bib_result.stdout}")

                # Run LaTeX twice to resolve refs
                result = run_pdflatex(filename, pdf_dir)

                # Parse errors/warnings
                errors, warnings = parse_latex_output(result.stdout)

                if errors:
                    print(f"{RED}Errors detected:{RESET}")
                    for e, info in errors:
                        if info:
                            print(f"{RED}{e} ({info}){RESET}")
                        else:
                            print(f"{RED}{e}{RESET}")
                else:
                    print(f"PDF updated in {pdf_dir}")

                if warnings:
                    print(f"{YELLOW}Warnings:{RESET}")
                    for w in warnings:
                        print(f"{YELLOW}{w}{RESET}")

        except KeyboardInterrupt:
            print("\nStopped.")
            break


if __name__ == "__main__":
    main()
