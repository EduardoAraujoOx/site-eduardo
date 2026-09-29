#!/usr/bin/env python3
"""
Localiza, nos ReceitasEntidade.xml do PIT/TCE-PR, os registros cuja descrição
ou natureza contém termos relacionados ao ISS. Saída compacta para descobrir
os campos/códigos necessários à validação automatizada.
"""
from __future__ import annotations
import io, json, re, sys, zipfile, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from remotezip import RemoteZip

HERE=Path(__file__).resolve().parent
OUT=HERE/"auditoria-pr-validacao"
UA="Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"
CODES={
 "Barbosa Ferraz":"410250",
 "Guaraqueçaba":"410950",
 "Pontal do Paraná":"411995",
 "Curitiba":"410690",
}

PAT=re.compile(r"(issqn|\biss\b|servi[cç]os?\s+de\s+qualquer|imposto.{0,80}servi)",re.I)

def main():
    ano=int(sys.argv[1]) if len(sys.argv)>1 else 2025
    url=f"https://pit.tce.pr.gov.br/Arquivos/{ano}_PIT_TodosArquivos.zip"
    result={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"ano":ano,"url":url,"municipios":{}}
    with RemoteZip(url,headers={"User-Agent":UA}) as rz:
        infos={i.filename:i for i in rz.infolist()}
        for mun,code in CODES.items():
            target=f"{ano}_{code}_Receita.zip"
            info=infos.get(target)
            rec={"outer_name":target,"matches":[],"schema_samples":[]}
            if not info:
                rec["error"]="não encontrado"; result["municipios"][mun]=rec; continue
            with zipfile.ZipFile(io.BytesIO(rz.read(info))) as nz:
                ent_name=next((n for n in nz.namelist() if "ReceitasEntidade" in n),None)
                rec["inner_name"]=ent_name
                if not ent_name:
                    rec["error"]="ReceitasEntidade.xml ausente"; result["municipios"][mun]=rec; continue
                root=ET.fromstring(nz.read(ent_name))
                seen_schema=set()
                for el in root.iter():
                    if el.attrib and len(rec["schema_samples"])<5:
                        keys=tuple(sorted(el.attrib.keys()))
                        if keys not in seen_schema:
                            seen_schema.add(keys)
                            rec["schema_samples"].append({"tag":el.tag,"attrs":dict(el.attrib)})
                    blob=" | ".join(f"{k}={v}" for k,v in el.attrib.items())
                    if PAT.search(blob):
                        # preserva só campos úteis e limita duplicatas mensais
                        rec["matches"].append({"tag":el.tag,**dict(el.attrib)})
                # limitar saída, mantendo registros finais/mais completos
                if len(rec["matches"])>80:
                    rec["matches"]=rec["matches"][-80:]
            result["municipios"][mun]=rec
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/f"probe-tce-iss-{ano}.json"
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
