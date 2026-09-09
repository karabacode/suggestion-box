#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def compile_protos():
    # Define paths relative to current working directory
    schemas_dir = Path("schemas")
    output_dir = Path("app/ports/model")

    # 1. Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Find all .proto files recursively
    proto_files = [str(p) for p in schemas_dir.glob("**/*.proto")]

    if not proto_files:
        print(f"Error: No .proto files found in '{schemas_dir}'")
        sys.exit(1)

    print(f"Found {len(proto_files)} .proto file(s):")
    for f in proto_files:
        print(f"  - {f}")

    # 3. Construct the compilation command
    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I={schemas_dir}",
        f"--python_out={output_dir}",
    ] + proto_files

    # 4. Execute protoc
    print("\nCompiling Protobuf definitions...")
    try:
        subprocess.run(cmd, check=True)
        print(
            f"Successfully generated Protobuf files in '{output_dir}'!"
        )
    except subprocess.CalledProcessError as e:
        print(f"\nCompilation failed with exit code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    compile_protos()