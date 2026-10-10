"""Keep compared application dependencies independent of instrumentation tools."""
import re


def declared_modules(gomod):
    return dict(re.findall(r"(?m)^\s*(?:require\s+)?(\S+)\s+(v\S+)", gomod))


def diagnostic_build_script(command):
    return """status=0
(""" + command + """) || status=$?
if [ "$status" -ne 0 ]; then
  mkdir -p /ws/native-diagnostics
  cp -a /root/.cache/go-inject/native /ws/native-diagnostics/ 2>/dev/null || true
  chmod -R a+rX /ws/native-diagnostics
  ps -eo pid,ppid,lstart,stat,comm > /ws/native-diagnostics/processes.txt
  free -m > /ws/native-diagnostics/memory.txt
  df -h > /ws/native-diagnostics/disk.txt
fi
exit "$status"
"""


def pin_declared_modules(gomod):
    # The reference tool adds requirements. Preserve the declared versions
    # on both sides while retaining existing local module replacements.
    replaced = set(re.findall(r"(?m)^replace\s+(\S+)\s+=>", gomod))
    pins = [(module, version) for module, version in declared_modules(gomod).items() if module not in replaced]
    if not pins:
        return gomod
    return gomod + "\nreplace (\n" + "\n".join(
        f"\t{module} => {module} {version}" for module, version in pins) + "\n)\n"


def align_requirement_metadata(gomod, reference_info):
    """Align MVS labels only when both binaries use the same replacement code."""
    replacements = {m: (target, version) for m, target, version in re.findall(
        r"(?m)^\s*(?:replace\s+)?(\S+)\s+=>\s+(\S+)\s+(v\S+)", gomod)}
    requirements = declared_modules(gomod)
    lines = reference_info.splitlines()
    aligned = []
    for index, line in enumerate(lines[:-1]):
        parts = line.split()
        replacement = lines[index + 1].split()
        if len(parts) < 3 or parts[0] != "dep" or len(replacement) < 3 or replacement[0] != "=>":
            continue
        module, logical = parts[1:3]
        if module not in replacements:
            continue
        effective = tuple(replacement[1:3])
        if replacements[module] != effective:
            raise ValueError(f"reference and candidate use different effective module code: {module}")
        if requirements[module] == logical:
            continue
        gomod = re.sub(r"(?m)^(\s*(?:require\s+)?" + re.escape(module) + r"\s+)v\S+",
                       lambda match: match[1] + logical, gomod)
        aligned.append({"module": module, "logical": logical, "effective": effective[1]})
    return gomod, aligned
