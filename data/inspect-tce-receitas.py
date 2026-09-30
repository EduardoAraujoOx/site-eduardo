#!/usr/bin/env python3
"""
Descoberta do layout dos dados consolidados do PIT/TCE-PR para validação do ISS.

Baixa apenas o arquivo consolidado do ano solicitado, inspeciona arquivos cujo
nome ou conteúdo indique receita e grava amostras de cabeçalho. Não altera
nenhuma base do modelo.

Uso:
  python3 data/inspect-tce-receitas.py 2025
"""
from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "auditoria-pr-validacao"
USER_AGENT = "Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def decode(raw):
    for enc in ("utf-8-sig", "utf-8", "cp1252", "iso-8859-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def inspect_zip(zf, prefix="", depth=0):
    out = []
    inventory_all = []
    if depth > 3:
        return out, inventory_all, inventory_all
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = f"{prefix}{info.filename}"
        low = name.lower()
        inventory_all.append({
            "name": name,
            "size": info.file_size,
            "compressed_size": info.compress_size,
        })
        is_text = low.endswith((".csv", ".txt", ".tsv"))
        is_nested = low.endswith(".zip")
        interesting_name = "receit" in low or "arrecad" in low

        if is_nested and info.file_size < 500_000_000:
            try:
                raw = zf.read(info)
                with zipfile.ZipFile(io.BytesIO(raw)) as nested:
                    nested_out, nested_all = inspect_zip(nested, prefix=name + "::", depth=depth + 1)
                    out.extend(nested_out)
                    inventory_all.extend(nested_all)
            except Exception as exc:
                out.append({"name": name, "nested_error": str(exc)})
            continue

        if not is_text:
            continue

        # Ler no máximo 300KB para descoberta.
        with zf.open(info) as fh:
            raw = fh.read(300_000)
        text, enc = decode(raw)
        low_text = text.lower()
        interesting_content = any(k in low_text for k in (
            "receita", "arrecad", "imposto sobre serv", "issqn", "iss ",
        ))
        if not (interesting_name or interesting_content):
            continue

        lines = text.splitlines()
        out.append({
            "name": name,
            "size": info.file_size,
            "encoding_guess": enc,
            "sample_lines": lines[:12],
            "contains_iss_text": bool(re.search(r"imposto.{0,30}servi|issqn|\\biss\\b", low_text)),
        })
    return out


def main():
    ano = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    url = f"https://pit.tce.pr.gov.br/Arquivos/{ano}_PIT_TodosArquivos.zip"
    OUT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        archive = Path(td) / f"pit-{ano}.zip"
        print(f"Baixando {url}")
        download(url, archive)
        print(f"Arquivo: {archive.stat().st_size / 1024 / 1024:.1f} MB")
        with zipfile.ZipFile(archive) as zf:
            inventory, inventory_all = inspect_zip(zf)

    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ano": ano,
        "url": url,
        "n_files_all_levels": len(inventory_all),
        "files_all_levels": inventory_all,
        "n_candidates": len(inventory),
        "candidates": inventory,
    }
    path = OUT / f"inventario-tce-receitas-{ano}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
