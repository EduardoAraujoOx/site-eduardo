#!/usr/bin/env python3
"""
Resumo compacto da estrutura dos ZIPs Receita do PIT/TCE-PR.
Lista arquivos internos e itens de receita cujo nome contém 'imposto' ou
'servi', agregando o realizado no ano pelo maior valor de
vlRealizadoAteOMes observado para cada item.
"""
from __future__ import annotations
import io, json, sys, zipfile, xml.etree.ElementTree as ET
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

def parse_xml_bytes(raw):
    # XML do PIT é UTF-8; ET lida com declaração quando presente.
    return ET.fromstring(raw)

def main():
    ano=int(sys.argv[1]) if len(sys.argv)>1 else 2025
    url=f"https://pit.tce.pr.gov.br/Arquivos/{ano}_PIT_TodosArquivos.zip"
    result={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"ano":ano,"url":url,"municipios":{}}
    with RemoteZip(url,headers={"User-Agent":UA}) as rz:
        infos={i.filename:i for i in rz.infolist()}
        for mun,code in CODES.items():
            target=f"{ano}_{code}_Receita.zip"
            rec={"outer_name":target,"inner_files":[],"itens":[]}
            info=infos.get(target)
            if not info:
                rec["error"]="não encontrado"
                result["municipios"][mun]=rec
                continue
            rawzip=rz.read(info)
            items={}
            with zipfile.ZipFile(io.BytesIO(rawzip)) as nz:
                for ii in nz.infolist():
                    if ii.is_dir(): continue
                    rec["inner_files"].append({"name":ii.filename,"size":ii.file_size})
                    if not ii.filename.lower().endswith((".xml",".txt")):
                        continue
                    raw=nz.read(ii)
                    try:
                        root=parse_xml_bytes(raw)
                    except Exception:
                        continue
                    for el in root.iter():
                        ds=(el.attrib.get("dsItem") or "").strip()
                        if not ds: continue
                        low=ds.lower()
                        if "imposto" not in low and "servi" not in low:
                            continue
                        key=(el.attrib.get("idSumarioItem"),ds)
                        val=el.attrib.get("vlRealizadoAteOMes")
                        mes=el.attrib.get("nrMes")
                        try: valf=float(val) if val is not None else None
                        except: valf=None
                        cur=items.get(key)
                        # guarda o maior acumulado e o mês correspondente
                        if cur is None or (valf is not None and (cur["vlRealizadoAteOMes"] is None or valf>cur["vlRealizadoAteOMes"])):
                            items[key]={
                              "idSumarioItem":key[0],"dsItem":ds,
                              "vlRealizadoAteOMes":valf,"nrMes":int(mes) if mes and mes.isdigit() else mes,
                              "source_file":ii.filename,
                            }
            rec["itens"]=sorted(items.values(),key=lambda x:(x["dsItem"],str(x["idSumarioItem"])))
            result["municipios"][mun]=rec
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/f"estrutura-tce-receita-{ano}.json"
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
