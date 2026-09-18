#!/usr/bin/env python3
"""Compiles .proto schemas, generates pyi stubs, and syncs assets across microservices."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SERVICES = (
    "gmail-suggestion-ingester",
    "suggestion-agent",
    "suggestion-core",
    "suggestion-response-dispatcher",
)


def compile_protos(skip_sync: bool = False) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    schemas_root = repository_root / "schemas"
    v1_dir = schemas_root / "v1"

    if not v1_dir.exists():
        print(f"Error: Directory '{v1_dir}' does not exist.")
        sys.exit(1)

    # 1. Find relative proto paths (e.g., v1/suggestion.proto)
    proto_files = [p.relative_to(schemas_root) for p in v1_dir.glob("*.proto")]

    if not proto_files:
        print(f"Error: No .proto files found in '{v1_dir}'")
        sys.exit(1)

    print(f"Found {len(proto_files)} .proto file(s) in schemas/v1:")
    for f in proto_files:
        print(f"  - {f}")

    # 2. Construct compilation command with pyi stub generation
    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I={schemas_root}",          # Inclusion root is schemas/
        f"--python_out={schemas_root}", # Outputs to schemas/v1/...
        f"--pyi_out={schemas_root}",    # Generates _pb2.pyi stubs for IDEs
        f"--protobuf-to-pydantic_out={schemas_root}",
    ] + [str(p) for p in proto_files]

    print("\nCompiling Protobuf definitions...")
    try:
        subprocess.run(cmd, check=True, cwd=schemas_root)
        print("Protobuf compilation successful.")

        if skip_sync:
            print("\nSkipping sync step (--skip-sync passed).")
            return

        # 3. Synchronize all generated & schema files to services
        for service_name in SERVICES:
            service_schemas = repository_root / service_name / "app/schemas/v1"

            # Clean destination directory if it already exists
            if service_schemas.exists():
                shutil.rmtree(service_schemas)

            service_schemas.mkdir(parents=True, exist_ok=True)

            # Copy all .py, .pyi, and .proto files dynamically from schemas/v1
            for source_file in v1_dir.iterdir():
                if source_file.suffix in (".py", ".pyi", ".proto"):
                    shutil.copy2(source_file, service_schemas / source_file.name)

            # Ensure __init__.py exists in top-level schemas/ for each service
            (repository_root / service_name / "app/schemas" / "__init__.py").touch(exist_ok=True)
            (service_schemas / "__init__.py").touch(exist_ok=True)

            print(f"Synced schemas to '{service_schemas}'")

        print("\nSuccessfully compiled and synced schemas across all services.")

    except subprocess.CalledProcessError as e:
        print(f"\nCompilation failed with exit code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compile .proto schemas and optionally sync to services."
    )
    parser.add_argument(
        "-s",
        "--skip-sync",
        action="store_true",
        help="Compile protos in place under schemas/ without copying to microservices.",
    )
    args = parser.parse_args()

    compile_protos(skip_sync=args.skip_sync)