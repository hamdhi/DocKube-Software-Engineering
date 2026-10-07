"""Validate build-mobile.yml and print its steps."""
import yaml

with open(".github/workflows/build-mobile.yml", encoding="utf-8") as fh:
    data = yaml.safe_load(fh)

print("YAML OK")
steps = data["jobs"]["build"]["steps"]
for i, s in enumerate(steps):
    print(f"  {i}: {s.get('name', '?')}")

print()
print("--- Delete step run ---")
print(steps[4]["run"])

print()
print("--- Upload step env ---")
print(steps[6].get("env"))
