```bash
#!/bin/bash
set -e

cd "$(dirname "$0")"
zip -r reverse-rat.zip . \
  -x "*.git*" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x "*.zip" \
  -x ".DS_Store"

echo "[+] Created reverse-rat.zip"
```

Make it executable:

```bash
chmod +x build_zip.sh
```
