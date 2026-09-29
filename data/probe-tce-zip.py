#!/usr/bin/env python3
import json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL="https://pit.tce.pr.gov.br/Arquivos/2025_PIT_TodosArquivos.zip"
OUT=Path(__file__).resolve().parent/"auditoria-pr-validacao"/"probe-range-tce-2025.json"
UA="Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"

def headers_dict(h):
    return {k:v for k,v in h.items()}

result={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"url":URL}
try:
    req=urllib.request.Request(URL,method="HEAD",headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=60) as r:
        result["head"]={"status":r.status,"headers":headers_dict(r.headers)}
except Exception as e:
    result["head_error"]=repr(e)

try:
    req=urllib.request.Request(URL,headers={"User-Agent":UA,"Range":"bytes=-65536"})
    with urllib.request.urlopen(req,timeout=60) as r:
        sample=r.read(1024)
        result["range"]={"status":r.status,"headers":headers_dict(r.headers),"sample_hex":sample[:32].hex()}
except Exception as e:
    result["range_error"]=repr(e)

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(result,ensure_ascii=False,indent=2))
