#!/usr/bin/env python3
"""
Compara três calibrações da simulação (parâmetros pontuais; bootstrap dos parâmetros; bootstrap com
fator de escala kappa de validação cruzada) para mostrar quanto a conclusão depende dessa escolha.
Não altera nenhum resultado publicado. Saída: data/sensibilidade-calibracoes.json
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
mc.OUT = Path("/tmp/sensibilidade_calibracoes_tmp.json")
saida = {}
for nome, kap, boot in [("A_parametros_pontuais", 1.0, False), ("B_bootstrap_kappa1", 1.0, True), ("C_bootstrap_kappa0_8", 0.8, True)]:
    mc.KAPPA = kap
    mc.USAR_BOOT = boot
    with contextlib.redirect_stdout(io.StringIO()):
        mc.main()
    r = json.loads(mc.OUT.read_text(encoding="utf-8"))["resultados"]["estado"]
    hw = {y: round(float(np.mean([(v[y]["p90"] - v[y]["p10"]) / 2 * 100 for v in r["por_uf"].values()])), 1) for y in ["2029", "2031", "2033"]}
    ac = round(float(np.mean([(v["p90"] - v["p10"]) / 2 * 100 for v in r["acumulado_2029_2033"].values()])), 1)
    es = r["por_uf"]["ES"]["2033"]
    esa = r["acumulado_2029_2033"]["ES"]
    saida[nome] = {"kappa": kap, "bootstrap_parametros": boot, "meia_largura_80_pp": hw, "meia_largura_acumulado_pp": ac,
                   "ES_2033": {k: round(es[k] * 100, 1) if k != "prob_ganho" else es[k] for k in ["central", "p10", "p90", "prob_ganho"]},
                   "ES_acumulado": {k: round(esa[k] * 100, 1) if k != "prob_ganho" else esa[k] for k in ["central", "p10", "p90", "prob_ganho"]},
                   "sinal_robusto_2033": [u for u, v in r["por_uf"].items() if v["2033"]["p10"] > 0 or v["2033"]["p90"] < 0],
                   "sinal_robusto_acumulado": [u for u, v in r["acumulado_2029_2033"].items() if v["p10"] > 0 or v["p90"] < 0]}
(HERE / "sensibilidade-calibracoes.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(saida, ensure_ascii=False, indent=1))
