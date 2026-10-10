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
