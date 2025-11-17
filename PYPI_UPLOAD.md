# PyPI Upload Anleitung

## Voraussetzungen

```bash
pip install build twine
```

## PyPI Account

1. Registriere dich auf: https://pypi.org/account/register/
2. Verifiziere deine E-Mail
3. Erstelle API Token:
   - Gehe zu: https://pypi.org/manage/account/token/
   - Name: `controme-scraper`
   - Scope: `Entire account` (später auf Package beschränken)
   - Kopiere den Token (beginnt mit `pypi-`)

## Build Package

```bash
cd /Users/mbick/Documents/Python/controme_scraper

# Alte Builds löschen
rm -rf dist/ build/ *.egg-info

# Package bauen
python3 -m build
```

Das erstellt:
- `dist/controme_scraper-0.1.0-py3-none-any.whl` (Wheel)
- `dist/controme-scraper-0.1.0.tar.gz` (Source Distribution)

## Upload zu PyPI

### Test PyPI (empfohlen für ersten Upload)

```bash
# Test PyPI Upload
python3 -m twine upload --repository testpypi dist/*

# Username: __token__
# Password: pypi-... (dein Test PyPI Token)
```

Verifiziere: https://test.pypi.org/project/controme-scraper/

Test Installation:
```bash
pip install --index-url https://test.pypi.org/simple/ controme-scraper
```

### Production PyPI

```bash
# Production PyPI Upload
python3 -m twine upload dist/*

# Username: __token__
# Password: pypi-... (dein PyPI Token)
```

Verifiziere: https://pypi.org/project/controme-scraper/

## Nach dem Upload

1. Test Installation:
   ```bash
   pip install controme-scraper
   python3 -c "from controme_scraper import ContromeController; print('✅ Success')"
   ```

2. Update in controme_ha `manifest.json` falls nötig:
   ```json
   "requirements": ["controme-scraper==0.1.0"]
   ```

3. GitHub Release erstellen mit PyPI Link

## Neue Versionen

1. Update Version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit und Tag:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.1.1"
   git tag -a v0.1.1 -m "Release v0.1.1"
   git push origin main --tags
   ```
4. Build und Upload wie oben

## Troubleshooting

### "Invalid distribution filename"
- Lösche `dist/`, `build/`, `*.egg-info` und baue neu

### "File already exists"
- Version wurde bereits hochgeladen
- PyPI erlaubt keine Überschreibung
- Erhöhe Version in `pyproject.toml`

### Import Error nach Installation
- Prüfe Package-Namen: `controme-scraper` (PyPI) vs `controme_scraper` (Import)
- Verifiziere `pyproject.toml` → `[tool.setuptools] packages = [...]`
