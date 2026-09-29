#!/usr/bin/env python3
"""
Testa o endpoint detalhado de receitas do PIT/TCE-PR para localizar o ISS.
Obtém o id da entidade "MUNICÍPIO DE ..." no ReceitasEntidade.xml e consulta
o plano orçamentário padrão de dezembro do mesmo exercício.
"""
from __future__ import annotations
import io, json, re, sys, urllib.parse, urllib.request, zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from remotezip import RemoteZip
from bs4 import BeautifulSoup

HERE=Path(__file__).resolve().parent
OUT=HERE/"auditoria-pr-validacao"
UA="Mozilla/5.0 auditoria-reforma-tributaria-sefaz-es/1.0"
CODES={
 "Barbosa Ferraz":"410250",
 "Guaraqueçaba":"410950",
 "Pontal do Paraná":"411995",
}
PAT=re.compile(r"imposto\s+sobre\s+servi[cç]os\s+de\s+qualquer\s+natureza|issqn|\biss\b",re.I)

def http_text(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read()
        return r.status, raw.decode("utf-8",errors="replace")

def main():
    ano=int(sys.argv[1]) if len(sys.argv)>1 else 2025
    outer=f"https://pit.tce.pr.gov.br/Arquivos/{ano}_PIT_TodosArquivos.zip"
    result={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"ano":ano,"municipios":{}}
    with RemoteZip(outer,headers={"User-Agent":UA}) as rz:
        infos={i.filename:i for i in rz.infolist()}
        for mun,code in CODES.items():
            target=f"{ano}_{code}_Receita.zip"
            rec={"outer_name":target}
            info=infos.get(target)
            if not info:
                rec["error"]="zip ausente"; result["municipios"][mun]=rec; continue
            with zipfile.ZipFile(io.BytesIO(rz.read(info))) as nz:
                ent_name=next((n for n in nz.namelist() if "ReceitasEntidade" in n),None)
                root=ET.fromstring(nz.read(ent_name))
                entities={}
                for el in root.iter():
                    a=el.attrib
                    pid=a.get("idpessoa")
                    nm=(a.get("nmEntidade") or "").strip()
                    if pid and nm:
                        entities[pid]=nm
                rec["entities"]=entities
                chosen=None
                for pid,nm in entities.items():
                    if nm.upper().startswith("MUNICÍPIO DE ") or nm.upper().startswith("MUNICIPIO DE "):
                        chosen=(pid,nm); break
                if not chosen:
                    # fallback: primeira entidade com nome do município
                    nmkey=mun.upper()
                    for pid,nm in entities.items():
                        if nmkey in nm.upper():
                            chosen=(pid,nm); break
                if not chosen:
                    rec["error"]="entidade municipal não localizada"; result["municipios"][mun]=rec; continue
                rec["chosen_entity_id"], rec["chosen_entity_name"]=chosen

            params={
              "IdEntidade":rec["chosen_entity_id"],
              "NrAno":ano,
              "NrMes":12,
              "tipo":"padrao",
              "tipoExibicao":"Imprimir",
            }
            url="https://pit.tce.pr.gov.br/Receitas/ReceitaDetalhes/PlanoOrcamentarioPadrao?"+urllib.parse.urlencode(params)
            rec["detail_url"]=url
            try:
                status,html=http_text(url)
                rec["http_status"]=status
                soup=BeautifulSoup(html,"html.parser")
                text=soup.get_text(" ",strip=True)
                rec["title"]=soup.title.get_text(" ",strip=True) if soup.title else None
                matches=[]
                for tr in soup.find_all("tr"):
                    t=" ".join(tr.stripped_strings)
                    if PAT.search(t):
                        matches.append(t)
                rec["iss_rows"]=matches[:30]
                # fallback textual context
                if not matches:
                    m=PAT.search(text)
                    rec["text_context"]=text[max(0,m.start()-300):m.end()+500] if m else None
                rec["html_length"]=len(html)
            except Exception as exc:
                rec["http_error"]=f"{type(exc).__name__}: {exc}"
            result["municipios"][mun]=rec

    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/f"probe-tce-iss-detalhe-{ano}.json"
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
