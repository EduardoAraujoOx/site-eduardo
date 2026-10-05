#!/usr/bin/env python3
"""
Sensibilidade da faixa do nível da receita às premissas macro (crescimento do PIB e razão bolo/PIB):
bootstrap estacionário (base), independência, variabilidade reduzida e cenário com o viés histórico do Focus.
Não altera nenhum resultado publicado. Saída: data/sensibilidade-macro-variantes.json
"""
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("mc", HERE / "sensibilidade-projecao-mc.py")
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
mc.OUT = Path("/tmp/sensibilidade_macro_tmp.json")
PADRAO = {"KAPPA_G": 1.0, "SD_RATIO": 0.06, "SD_REF": 0.012, "G_BLOCO_MEDIO": 4, "BIAS_G": 0.0}
VARIANTES = {
    "base": {},
    "independencia_anual": {"G_BLOCO_MEDIO": 1},
    "pib_metade_da_variabilidade": {"KAPPA_G": 0.5},
    "sem_incerteza_da_razao": {"SD_RATIO": 0.0, "SD_REF": 0.0},
    "pib_e_razao_metade": {"KAPPA_G": 0.5, "SD_RATIO": 0.03, "SD_REF": 0.006},
    "viés_historico_do_Focus_menos_1_2pp_ao_ano": {"BIAS_G": -0.012},
}
saida = {}
for nome, kw in VARIANTES.items():
    for k, v in PADRAO.items():
        setattr(mc, k, v)
    for k, v in kw.items():
        setattr(mc, k, v)
    with contextlib.redirect_stdout(io.StringIO()):
        mc.main()
    r = json.loads(mc.OUT.read_text(encoding="utf-8"))["resultados"]["estado"]["nivel_em_reais_2025"]
    def hw(u, a):
        return round(r[u][a]["largura_rel_80"] * 100, 1)
    saida[nome] = {"PR": {a: hw("PR", a) for a in ["2029", "2031", "2033"]} | {"acum": round(r["PR"]["acumulado_2029_2033"]["largura_rel_80"] * 100, 1),
                                                                               "central_2033_bi": r["PR"]["2033"]["central_bi"], "p10_2033_bi": r["PR"]["2033"]["p10_bi"], "p90_2033_bi": r["PR"]["2033"]["p90_bi"]},
                   "media_27_UFs": {a: round(float(np.mean([r[u][a]["largura_rel_80"] for u in r])) * 100, 1) for a in ["2029", "2031", "2033"]}}
    print(nome, saida[nome]["PR"], saida[nome]["media_27_UFs"], flush=True)
(HERE / "sensibilidade-macro-variantes.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
