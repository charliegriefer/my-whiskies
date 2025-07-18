import os

import requests
import yaml

# === CONFIG ===
REPO = "charliegriefer/my-whiskies"
TOKEN = os.getenv("LABEL_GH_TOKEN")
LABELS_YAML = ".github/labels.yml"
GITHUB_API = f"https://api.github.com/repos/{REPO}/labels"
print("TOKEN: ", TOKEN)
headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}


def load_labels(path):
    with open(path) as f:
        return yaml.safe_load(f)["labels"]


def upsert_label(label):
    url = f"{GITHUB_API}/{label['name']}"
    payload = {
        "name": label["name"],
        "color": label["color"].lstrip("#"),
        "description": label["description"],
    }

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        print(f"Updating: {label['name']}")
        requests.patch(url, headers=headers, json=payload)
    else:
        print(f"Creating: {label['name']}")
        requests.post(GITHUB_API, headers=headers, json=payload)


def main():
    labels = load_labels(LABELS_YAML)
    for label in labels:
        upsert_label(label)


if __name__ == "__main__":
    main()
