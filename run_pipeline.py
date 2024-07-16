import subprocess
import sys
import os

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())

    rc = process.poll()
    if rc != 0:
        print(f"Error: Command '{' '.join(command)}' failed with return code {rc}")
        print(f"Error output:\n{process.stderr.read()}")
        sys.exit(1)

def main():
    # Get the path to the current Python interpreter
    python_executable = sys.executable

    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Step 1: Run generate_sims.py
    print("Step 1: Running generate_sims.py")
    run_command([python_executable, "generate_sims.py", "config_prod.ini"])
    print("generate_sims.py completed successfully.")

    # Step 2: Run combine.py
    print("\nStep 2: Running combine.py")
    run_command([python_executable, "combine.py", "config_prod.ini"])
    print("combine.py completed successfully.")

    # Step 3: Run compare_reports.py
    print("\nStep 3: Running compare_reports.py")
    run_command([python_executable, "compare_reports.py"])
    print("compare_reports.py completed successfully.")

    print("\nFull build pipeline completed successfully!")

if __name__ == "__main__":
    main()