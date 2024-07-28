import subprocess
import sys
import os
import re

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

    progress_pattern = re.compile(r'^\s*\d+%\|')
    last_progress_line = ''

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            output = output.strip()
            if progress_pattern.match(output):
                # This is a progress bar update
                print(f'\r{output}', end='', flush=True)
                last_progress_line = output
            elif output != last_progress_line:
                # This is not a progress bar update and it's different from the last progress line
                if last_progress_line:
                    print()  # Move to a new line after the progress bar
                    last_progress_line = ''
                print(output)

    if last_progress_line:
        print()  # Ensure we move to a new line after the last progress bar

    rc = process.poll()
    if rc != 0:
        print(f"Error: Command '{command}' failed with return code {rc}")
        print(f"Error output:\n{process.stderr.read()}")
        sys.exit(1)

def main():
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Activate the virtual environment
    venv_activate = os.path.join(script_dir, "venv", "bin", "activate")
    activate_cmd = f"source {venv_activate} && "

    # Step 1: Run generate_sims.py
    print("Step 1: Running generate_sims.py")
    run_command(f"{activate_cmd} python generate_sims.py config_prod.ini")
    print("generate_sims.py completed successfully.")

    # Step 2: Run combine.py
    print("\nStep 2: Running combine.py")
    run_command(f"{activate_cmd} python combine.py config_prod.ini")
    print("combine.py completed successfully.")

    # Step 3: Run compare_reports.py
    print("\nStep 3: Running compare_reports.py")
    run_command(f"{activate_cmd} python compare_reports.py")
    print("compare_reports.py completed successfully.")

    print("\nFull build pipeline completed successfully!")

if __name__ == "__main__":
    main()