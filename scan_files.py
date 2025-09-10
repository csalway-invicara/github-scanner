import os
import json

root_dir = "./files"
pattern = "package-lock.json"
packages = [
    "ansi-regex@6.2.1",
    "ansi-styles@6.2.2",
    "backslash@0.2.1",
    "chalk@5.6.1",
    "chalk-template@1.1.1",
    "color-convert@3.1.1",
    "color-name@2.0.1",
    "color-string@2.1.1",
    "debug@4.4.2",
    "error-ex@1.3.3",
    "has-ansi@6.0.1",
    "is-arrayish@0.3.3",
    "proto-tinker-wc@1.8.7",
    "supports-hyperlinks@4.1.1",
    "simple-swizzle@0.2.3",
    "slice-ansi@7.1.1",
    "strip-ansi@7.1.1",
    "supports-color@10.2.1",
    "supports-hyperlinks@4.1.1",
    "wrap-ansi@9.0.1",
    #"@babel/cli@7.15.4"  # test to make sure it works
]

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(pattern):
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                if 'dependencies' in data:
                    for k, v in data['dependencies'].items():
                        pkg = f"{k}@{v.get('version')}"
                        if pkg in packages:
                            print(f"FOUND {pkg} in {filepath}")
                
                elif 'packages' in data:
                    for k, v in data['packages'].items():
                        k1 = "/".join(k.split('/')[1:])  # remove node_modules/
                        pkg = f"{k1}@{v.get('version')}"
                        if pkg in packages:
                            print(f"FOUND {pkg} in {filepath}")
                
                else:
                    raise Exception("No dependencies specified")

            except Exception as e:
                print(filepath)
                print(e)
