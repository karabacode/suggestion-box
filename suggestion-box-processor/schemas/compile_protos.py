#!/usr/bin/env python3
"""Compiles .proto schemas, generates pyi stubs, patches p2p model configs, converts Field(alias=...) to Annotated, and syncs assets across microservices."""

import argparse
import re
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


def patch_p2p_file(file_path: Path) -> None:
    """Injects model_config into all BaseModel classes, converts Field(alias=...) to Annotated, and replaces empty defaults with Ellipsis (...)."""
    content = file_path.read_text(encoding="utf-8")

    # 1. Ensure ConfigDict is imported from pydantic
    if "from pydantic import " in content and "ConfigDict" not in content:
        content = re.sub(
            r"from pydantic import (.*)",
            r"from pydantic import \1, ConfigDict",
            content,
            count=1,
        )

    # 2. Ensure Annotated is imported unconditionally if needed
    if "Annotated" not in content:
        if "from typing import " in content:
            content = re.sub(
                r"from typing import (.*)",
                r"from typing import \1, Annotated",
                content,
                count=1,
            )
        else:
            # Fallback: prepend the import at top of file
            content = "from typing import Annotated\n" + content

    # 3. Inject model_config directly under class declarations inheriting from BaseModel
    class_pattern = re.compile(r"^(class\s+\w+\(BaseModel\):)", re.MULTILINE)

    def inject_config(match: re.Match) -> str:
        class_decl = match.group(1)
        return f'{class_decl}\n    model_config = ConfigDict(populate_by_name=True, extra="ignore")'

    if "model_config =" not in content:
        content = class_pattern.sub(inject_config, content)

    # 4. Replace default="" or default='' with Ellipsis (...) inside Field calls
    content = re.sub(r'Field\(\s*default=["\']["\']\s*,\s*', 'Field(..., ', content)     
    content = re.sub(r',\s*default=["\']["\']\s*\)', ', ...)', content)
    content = re.sub(r'Field\(\s*default=["\']["\']\s*\)', 'Field(...)', content)

    # 5. Handle empty Field() calls by inserting Ellipsis (...)
    content = re.sub(r'Field\(\)', 'Field(...)', content)
    content = re.sub(r'\s*=\s*Field\(\.\.\.\)', '', content)

    # 6. Convert `field_name: <TYPE> = Field(alias="...", ...)` to `field_name: Annotated[<TYPE>, Field(..., alias="...", ...)]`
    # Ensures Field has `...` if no positional arg is present, avoiding Pydantic alias inspection warnings
    def add_ellipsis_if_missing(field_call: str) -> str:
        if not re.search(r'Field\(\s*\.\.\.', field_call):
            return re.sub(r'Field\(', 'Field(..., ', field_call)
        return field_call

    alias_field_pattern = re.compile(
        r'^(\s*)(\w+):\s*(.*?)\s*=\s*((?:pydantic\.)?Field\([^)]*alias=[^)]*\))',
        re.MULTILINE,
    )

    def replace_alias_field(match: re.Match) -> str:
        indent = match.group(1)
        field_name = match.group(2)
        field_type = match.group(3)
        field_call = add_ellipsis_if_missing(match.group(4))
        return f'{indent}{field_name}: Annotated[{field_type}, {field_call}]'

    content = alias_field_pattern.sub(replace_alias_field, content)

    file_path.write_text(content, encoding="utf-8")
    print(f"  - Patched model_config and Annotated fields in: {file_path.name}")


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
        "--protobuf-to-pydantic_opt=populate_by_name=True",
        "--protobuf-to-pydantic_opt=snake_to_camel=True",
    ] + [str(p) for p in proto_files]

    print("\nCompiling Protobuf definitions...")
    try:
        subprocess.run(cmd, check=True, cwd=schemas_root)
        print("Protobuf compilation successful.")

        # --- POST-PROCESSING STEP: Patch model_config and clean fields ---
        print("\nPatching generated Pydantic models with model_config and Annotated fields...")
        p2p_files = list(v1_dir.glob("*_p2p.py")) + list(v1_dir.glob("*_p2p.pyi"))
        if not p2p_files:
            # Fallback in case files don't use the _p2p suffix
            p2p_files = [p for p in v1_dir.glob("*.py") if not p.name.endswith("_pb2.py")]

        for p2p_file in p2p_files:
            if p2p_file.suffix == ".py":
                patch_p2p_file(p2p_file)
        # ----------------------------------------------------------------------------

        if skip_sync:
            print("\nSkipping sync step (--skip-sync passed).")
            return

        # 3. Synchronize all generated & schema files to services
        for service_name in SERVICES:
            target_schemas_root = repository_root / service_name / "app/schemas"
            service_schemas = target_schemas_root / "v1"

            # Clean destination directory if it already exists
            if service_schemas.exists():
                shutil.rmtree(service_schemas)

            service_schemas.mkdir(parents=True, exist_ok=True)

            # Copy all .py, .pyi, and .proto files dynamically from schemas/v1
            for source_file in v1_dir.iterdir():
                if source_file.suffix in (".py", ".pyi", ".proto"):
                    shutil.copy2(source_file, service_schemas / source_file.name)

            # Ensure __init__.py exists in top-level schemas/ for each service
            (target_schemas_root / "__init__.py").touch(exist_ok=True)
            (service_schemas / "__init__.py").touch(exist_ok=True)

            # Copy buf configuration files if they exist
            for buf_file in ("buf.yml", "buf.yaml", "buf.gen.yaml"):
                buf_source = schemas_root / buf_file
                if buf_source.exists():
                    shutil.copy2(buf_source, target_schemas_root / buf_file)

            print(f"Synced schemas and config to '{service_schemas}'")

        print("\nSuccessfully compiled, patched, and synced schemas across all services.")

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