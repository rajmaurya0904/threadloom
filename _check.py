import yaml

with open(".github/workflows/ci.yml") as f:
    data = yaml.safe_load(f)

print("valid yaml")
print("jobs:", list(data.get("jobs", {}).keys()))