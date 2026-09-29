#!/usr/bin/env python3
"""
Inspeciona o conteúdo interno dos ZIPs de Receita de alguns municípios
no consolidado PIT/TCE-PR, sem baixar o arquivo anual inteiro.
"""
from __future__ import annotations
import io, json, re, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path
from remotezip import RemoteZip

HERE=Path(__file__).resolve().parent
OUT=HERE/"auditoria-pr-validacao"
UA="Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"

# 6 dígitos usados pelo PIT no nome do arquivo.
CODES={
    "Barbosa Ferraz":"410250",
    "Guaraqueçaba":"410950",
    "Pontal do Paraná":"411995",
    "Curitiba":"410690",
}

def decode(raw):
    for enc in ("utf-8-sig","utf-8","cp1252","iso-8859-1"):
        try: return raw.decode(enc),enc
        except UnicodeDecodeError: pass
    return raw.decode("utf-8",errors="replace"),"utf-8-replace"

def main():
    ano=int(sys.argv[1]) if len(sys.argv)>1 else 2025
    url=f"https://pit.tce.pr.gov.br/Arquivos/{ano}_PIT_TodosArquivos.zip"
    out={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"ano":ano,"url":url,"municipios":{}}
    with RemoteZip(url,headers={"User-Agent":UA}) as rz:
        names={i.filename:i for i in rz.infolist()}
        for mun,code in CODES.items():
            target=f"{ano}_{code}_Receita.zip"
            rec={"outer_name":target}
            info=names.get(target)
            if not info:
                rec["error"]="arquivo não encontrado"
                out["municipios"][mun]=rec
                continue
            raw=rz.read(info)
            rec["outer_file_size"]=info.file_size
            rec["outer_compress_size"]=info.compress_size
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                rec["inner_files"]=[]
                for ii in z.infolist():
                    if ii.is_dir(): continue
                    ir={"name":ii.filename,"size":ii.file_size}
                    if ii.file_size <= 10_000_000:
                        b=z.read(ii)
                        txt,enc=decode(b)
                        ir["encoding_guess"]=enc
                        lines=txt.splitlines()
                        ir["sample_lines"]=lines[:25]
                        ir["iss_matches"]=[ln for ln in lines if re.search(r"imposto.{0,50}servi|issqn|\\biss\\b",ln,re.I)][:25]
                    rec["inner_files"].append(ir)
            out["municipios"][mun]=rec
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/f"amostra-tce-receita-{ano}.json"
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
