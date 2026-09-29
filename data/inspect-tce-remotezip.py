#!/usr/bin/env python3
"""
Inspeção remota do ZIP consolidado PIT/TCE-PR via HTTP Range.
Não baixa o arquivo inteiro: lê apenas o diretório central e amostras
selecionadas dos arquivos internos.

Uso:
  python3 data/inspect-tce-remotezip.py 2025
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from remotezip import RemoteZip

HERE = Path(__file__).resolve().parent
OUT = HERE / "auditoria-pr-validacao"
UA = "Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"

def ext(name):
    base=name.rsplit("/",1)[-1]
    if "." not in base:
        return ""
    return "."+base.rsplit(".",1)[-1].lower()

def decode(raw):
    for enc in ("utf-8-sig","utf-8","cp1252","iso-8859-1"):
        try:
            return raw.decode(enc),enc
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8",errors="replace"),"utf-8-replace"

def main():
    ano=int(sys.argv[1]) if len(sys.argv)>1 else 2025
    url=f"https://pit.tce.pr.gov.br/Arquivos/{ano}_PIT_TodosArquivos.zip"
    headers={"User-Agent":UA}
    OUT.mkdir(parents=True,exist_ok=True)

    with RemoteZip(url, headers=headers) as rz:
        infos=rz.infolist()
        names=[i.filename for i in infos if not i.is_dir()]
        ext_counts=Counter(ext(n) for n in names)
        keywords=("receit","arrecad","tribut","orcament","contabil","moviment")
        candidates=[i for i in infos if not i.is_dir() and any(k in i.filename.lower() for k in keywords)]

        # Se o nome não ajuda, preserva uma amostra ampla dos nomes para
        # descobrir a convenção usada pelo PIT.
        sample_names=names[:500]

        inspected=[]
        for i in sorted(candidates,key=lambda x:x.file_size)[:80]:
            rec={
                "name":i.filename,
                "file_size":i.file_size,
                "compress_size":i.compress_size,
            }
            # Ler somente arquivos de texto e apenas os primeiros 256 KB.
            if ext(i.filename) in {".csv",".txt",".tsv",".json"} and i.file_size <= 100_000_000:
                try:
                    with rz.open(i) as fh:
                        raw=fh.read(262144)
                    txt,enc=decode(raw)
                    rec["encoding_guess"]=enc
                    rec["sample_lines"]=txt.splitlines()[:20]
                    rec["contains_iss_text"]=bool(re.search(r"imposto.{0,40}servi|issqn|\\biss\\b",txt,re.I))
                except Exception as e:
                    rec["read_error"]=repr(e)
            inspected.append(rec)

    result={
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "ano":ano,
        "url":url,
        "n_files":len(names),
        "extensions":dict(ext_counts.most_common()),
        "sample_names":sample_names,
        "n_name_candidates":len(candidates),
        "candidates":inspected,
    }
    p=OUT/f"inventario-tce-remotezip-{ano}.json"
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({
        "n_files":result["n_files"],
        "extensions":result["extensions"],
        "n_name_candidates":result["n_name_candidates"],
        "sample_names":sample_names[:80],
        "candidates":inspected[:30],
    },ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
