#!/bin/bash
# Corpus Download Script
# Downloads all three policy corpora into corpus/raw/
# Run from repo root: bash corpus/download.sh

set -e  # exit on any error

echo "Creating corpus/raw directory if it doesn't exist..."
mkdir -p corpus/raw

echo ""
echo "=== Downloading OWASP API Security Top 10 (2023) ==="
BASE="https://raw.githubusercontent.com/OWASP/API-Security/master/editions/2023/en"
for f in \
  0xa1-broken-object-level-authorization \
  0xa2-broken-authentication \
  0xa3-broken-object-property-level-authorization \
  0xa4-unrestricted-resource-consumption \
  0xa5-broken-function-level-authorization \
  0xa6-unrestricted-access-to-sensitive-business-flows \
  0xa7-server-side-request-forgery \
  0xa8-security-misconfiguration \
  0xa9-improper-inventory-management \
  0xa10-unsafe-consumption-of-apis; do
  echo "  Downloading $f.md..."
  curl -fsSL "$BASE/$f.md" -o "corpus/raw/owasp-api-$f.md"
done
echo "OWASP API Top 10: 10 files downloaded"

echo ""
echo "=== Downloading OWASP ASVS 4.0.3 (CSV) ==="
curl -fsSL "https://raw.githubusercontent.com/OWASP/ASVS/master/4.0/docs_en/OWASP%20Application%20Security%20Verification%20Standard%204.0.3-en.csv" \
  -o "corpus/raw/owasp-asvs-4.0.3.csv"
echo "OWASP ASVS: 1 CSV file downloaded"

echo ""
echo "=== Downloading Zalando REST API Guidelines (12 chapters) ==="
ZBASE="https://raw.githubusercontent.com/zalando/restful-api-guidelines/main/chapters"
for f in \
  general-guidelines \
  security \
  urls \
  http-requests \
  http-status-codes-and-errors \
  http-headers \
  json-guidelines \
  data-formats \
  compatibility \
  pagination \
  performance \
  api-operation; do
  echo "  Downloading $f.adoc..."
  curl -fsSL "$ZBASE/$f.adoc" -o "corpus/raw/zalando-$f.adoc"
done
echo "Zalando Guidelines: 12 files downloaded"

echo ""
echo "=== Verifying downloads ==="
echo "File count: $(ls corpus/raw/ | wc -l) files (expected 23)"
echo "File sizes:"
wc -l corpus/raw/* | tail -1
echo ""
echo "Download complete. Run wc -l corpus/raw/* to inspect individual files."
