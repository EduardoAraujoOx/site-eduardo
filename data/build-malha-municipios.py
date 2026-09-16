#!/usr/bin/env python3
"""
Malha municipal do Brasil para o mapa da aba Municípios do painel.

Baixa a malha do IBGE (qualidade mínima, que já vem generalizada) e grava
uma versão com as coordenadas arredondadas, reduzindo o arquivo sem perda
visível na escala em que o mapa é desenhado.

Por que versionar o arquivo em vez de consultar a API em tempo de execução:
a malha estadual já usa a API e precisa de uma URL de reserva justamente
porque o serviço nem sempre responde. Para um mapa que abre a aba, uma
falha de rede deixaria a página vazia. Servindo do próprio repositório, o
mapa não depende de terceiros no momento da visita.

O identificador de cada feição é `codarea`, o código do IBGE de 7 dígitos,
que é a mesma chave usada em painel-municipios/. O casamento é direto.

Uso:
  python3 build-malha-municipios.py
"""

import gzip
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "malha-municipios.json"

URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio"
)

# Três casas decimais equivalem a cerca de 100 metros. O mapa nacional
# desenha cada município com poucos pixels, então essa precisão sobra.
CASAS = 3


def arredonda(o):
    if isinstance(o, list):
        return [arredonda(x) for x in o]
    if isinstance(o, float):
        return round(o, CASAS)
    return o


def area_assinada(anel):
    s = 0.0
    for i in range(len(anel) - 1):
        s += anel[i][0] * anel[i + 1][1] - anel[i + 1][0] * anel[i][1]
    return s


def orienta(poligono):
    """Deixa o anel externo no sentido horário e os buracos no anti-horário.

    O IBGE entrega no sentido do RFC 7946 (externo anti-horário). O D3 lê
    polígonos como regiões da esfera e adota a convenção oposta, de modo que
    um anel anti-horário é interpretado como "todo o planeta menos esta
    área". Sem esta correção, o cálculo de limites devolve o globo inteiro e
    o Brasil é reduzido a um ponto no centro da tela.
    """
    for i, anel in enumerate(poligono):
        a = area_assinada(anel)
        if (i == 0 and a > 0) or (i > 0 and a < 0):
            anel.reverse()
    return poligono


def main():
    print("Baixando malha municipal do IBGE...")
    req = urllib.request.Request(URL, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=180) as r:
        bruto = r.read()
    if r.headers.get("Content-Encoding") == "gzip" or bruto[:2] == b"\x1f\x8b":
        bruto = gzip.decompress(bruto)
    geo = json.loads(bruto)

    feicoes = geo.get("features") or []
    if len(feicoes) < 5000:
        raise SystemExit(f"malha inesperada: {len(feicoes)} feições, esperado ~5570")

    sem_codigo = [f for f in feicoes if not (f.get("properties") or {}).get("codarea")]
    if sem_codigo:
        raise SystemExit(f"{len(sem_codigo)} feições sem codarea; o casamento com os dados quebraria")

    for f in feicoes:
        g = f["geometry"]
        coords = arredonda(g["coordinates"])
        if g["type"] == "Polygon":
            g["coordinates"] = orienta(coords)
        elif g["type"] == "MultiPolygon":
            g["coordinates"] = [orienta(p) for p in coords]
        else:
            raise SystemExit(f"geometria inesperada: {g['type']}")
        # Só o código interessa; qualquer outro campo é peso morto no arquivo.
        f["properties"] = {"cod": str(f["properties"]["codarea"])}

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(geo, fh, ensure_ascii=False, separators=(",", ":"))

    tamanho = OUT.stat().st_size / 1e6
    print(f"Salvo em {OUT}")
    print(f"Feições: {len(feicoes)} | {tamanho:.2f} MB (cerca de 0,7 MB comprimido na entrega)")


if __name__ == "__main__":
    main()
