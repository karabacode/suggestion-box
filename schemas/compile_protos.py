#!/usr/bin/env python3
import subprocess
import sys
import shutil
from pathlib import Path


def compile_protos():
    repository_root = Path(__file__).resolve().parents[1]
    schemas_dir = repository_root / "schemas"
    output_dir = schemas_dir

    # 1. Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Find all .proto files recursively
    proto_files = [str(p) for p in schemas_dir.glob("*.proto")]

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
        for service_name in (
            "suggestions-ingester",
            "suggestion-agent",
            "suggestion-response-dispatcher",
        ):
            service_schemas = repository_root / service_name / "schemas"
            service_schemas.mkdir(parents=True, exist_ok=True)
            for filename in (
                "__init__.py",
                "pydantic_schemas.py",
                "suggestion.proto",
                "suggestion_pb2.py",
            ):
                shutil.copy2(schemas_dir / filename, service_schemas / filename)
        print(
            "Successfully generated shared schemas and copied them to "
            "suggestions-ingester, suggestion-agent, and "
            "suggestion-response-dispatcher."
        )
    except subprocess.CalledProcessError as e:
        print(f"\nCompilation failed with exit code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    compile_protos()