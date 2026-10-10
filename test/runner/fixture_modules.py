"""Keep compared application dependencies independent of instrumentation tools."""
import re


def declared_modules(gomod):
    return dict(re.findall(r"(?m)^\s*(?:require\s+)?(\S+)\s+(v\S+)", gomod))


def pin_declared_modules(gomod):
    # The reference tool adds requirements. Preserve the declared versions
    # on both sides while retaining existing local module replacements.
    replaced = set(re.findall(r"(?m)^replace\s+(\S+)\s+=>", gomod))
    pins = [(module, version) for module, version in declared_modules(gomod).items() if module not in replaced]
    if not pins:
        return gomod
    return gomod + "\nreplace (\n" + "\n".join(
        f"\t{module} => {module} {version}" for module, version in pins) + "\n)\n"
