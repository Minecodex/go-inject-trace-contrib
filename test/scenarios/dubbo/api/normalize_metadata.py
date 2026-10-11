"""Adapt generated Triple metadata to the oldest declared RPC attachment API."""
import re
import sys
from pathlib import Path


def normalize_metadata(source):
    # protoc-gen-go-triple v1.0.10-rc2 stores every metadata value as []string.
    # Dubbo v3.0.1 GetAttachment accepts string; later versions accept both.
    # Preserve multiple values and the actual wire metadata. Only represent
    # a single value as the scalar supported by all declared framework rows.
    def scalar(match):
        indent = match[1]
        return (f"{indent}if len(v) == 1 {{\n"
                f"{indent}\tinvAttachment[k] = v[0]\n"
                f"{indent}}} else {{\n"
                f"{indent}\tinvAttachment[k] = v\n"
                f"{indent}}}")

    return re.subn(r"(?m)^([ \t]*)invAttachment\[k\] = v$", scalar, source)


def main():
    root = Path(sys.argv[1])
    files = sorted(root.glob("*_triple.pb.go"))
    changed = 0
    for path in files:
        source, count = normalize_metadata(path.read_text(encoding="utf-8"))
        if count:
            path.write_text(source, encoding="utf-8")
            changed += count
    if not changed:
        raise SystemExit("Pinned Triple generator attachment contract changed")
    print(f"TRIPLE_SINGLE_VALUE_METADATA_HANDLERS={changed}")


if __name__ == "__main__":
    main()
