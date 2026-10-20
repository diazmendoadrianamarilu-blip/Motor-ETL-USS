"""Reporte HTML de calidad e integridad de una corrida, generado LOCAL desde SQLite.

Autocontenido (sin CDN ni servidor) y sin sacar datos de personas fuera de la máquina.
"""
import html
import json
import sqlite3
from pathlib import Path

_CSS = """
:root{--bg:#f6f7f9;--card:#fff;--tx:#1b2430;--mut:#667085;--bd:#e3e6eb;--ok:#067647;--ko:#b42318;--wa:#b54708}
@media(prefers-color-scheme:dark){:root{--bg:#12161c;--card:#1b212a;--tx:#e8ecf2;--mut:#98a2b3;--bd:#2c3440;--ok:#47cd89;--ko:#f97066;--wa:#fdb022}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px}h1{margin:0 0 4px;font-size:22px}h2{font-size:16px;margin:28px 0 10px}
.mut{color:var(--mut);font-size:13px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:16px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px}.card b{display:block;font-size:26px}
.ok{color:var(--ok)}.ko{color:var(--ko)}.wa{color:var(--wa)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--bd);border-radius:10px;overflow:hidden;font-size:13px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--bd);vertical-align:top}th{color:var(--mut);font-weight:600}
.wrap{overflow-x:auto}code{font-size:12px;word-break:break-all}input{width:100%;padding:8px 10px;margin-bottom:8px;border:1px solid var(--bd);border-radius:8px;background:var(--card);color:var(--tx)}
"""


def _tabla(cabeceras: list[str], filas: list[tuple], clase_id: str = "") -> str:
    th = "".join(f"<th>{html.escape(c)}</th>" for c in cabeceras)
    tr = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in f) + "</tr>" for f in filas)
    return f'<div class="wrap"><table id="{clase_id}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def generar_reporte(dlq_path: Path, modulo: str, destino: Path) -> Path:
    con = sqlite3.connect(dlq_path)
    corr = con.execute(
        "SELECT corrida, leidos, validos, rechazados, planilla, sha256, creado_en FROM corridas "
        "WHERE modulo=? ORDER BY corrida DESC LIMIT 1", (modulo,)).fetchone()
    if not corr:
        raise ValueError(f"No hay corridas registradas para '{modulo}' en {dlq_path}")
    corrida, leidos, validos, rechazados, planilla, sha, creado = corr

    huerf = con.execute(
        "SELECT catalogo, valor, filas FROM huerfanos WHERE modulo=? AND corrida=? ORDER BY filas DESC", (modulo, corrida)).fetchall()
    rech = con.execute(
        "SELECT motivo, registro_origen FROM dead_letter_queue WHERE modulo=? AND corrida=?", (modulo, corrida)).fetchall()
    con.close()

    cuadra = leidos == validos + rechazados
    pct = (validos / leidos * 100) if leidos else 0.0
    por_motivo: dict[str, int] = {}
    for motivo, _ in rech:
        por_motivo[motivo] = por_motivo.get(motivo, 0) + 1
    detalle = [(m, json.dumps(json.loads(r), ensure_ascii=False)) for m, r in rech]

    estado = ('<span class="ok">✔ Conciliado</span>' if cuadra else '<span class="ko">✖ Descuadre</span>')
    cuerpo = f"""
<h1>Reporte de migración · {html.escape(modulo)}</h1>
<div class="mut">Corrida {html.escape(corrida)} · {html.escape(creado)} · {estado}</div>
<div class="grid">
 <div class="card"><span class="mut">Leídos (legacy)</span><b>{leidos}</b></div>
 <div class="card"><span class="mut">En planilla</span><b class="ok">{validos}</b></div>
 <div class="card"><span class="mut">Rechazados (DLQ)</span><b class="{'ko' if rechazados else 'ok'}">{rechazados}</b></div>
 <div class="card"><span class="mut">Íntegros</span><b class="{'ok' if pct == 100 else 'wa'}">{pct:.1f}%</b></div>
</div>
<p class="mut">Conciliación: {leidos} = {validos} + {rechazados}. Planilla: <code>{html.escape(planilla)}</code><br>
SHA-256: <code>{sha}</code> (verifica que el archivo enviado a Ellucian es el generado).</p>

<h2>Valores sin equivalencia — agregar al catálogo de los funcionales</h2>
{_tabla(['Catálogo', 'Valor legacy', 'Filas afectadas'], huerf) if huerf else '<p class="mut">Ninguno.</p>'}

<h2>Rechazos por motivo</h2>
{_tabla(['Motivo', 'Registros'], sorted(por_motivo.items(), key=lambda x: -x[1])) if por_motivo else '<p class="mut">Sin rechazos.</p>'}

<h2>Detalle de registros rechazados</h2>
<input id="q" placeholder="Filtrar por motivo, ID o valor…">
{_tabla(['Motivo', 'Registro de origen'], detalle, 'det') if detalle else '<p class="mut">Sin rechazos.</p>'}
<script>
const q=document.getElementById('q');if(q)q.oninput=()=>{{const t=q.value.toLowerCase();
document.querySelectorAll('#det tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(t)?'':'none')}}
</script>"""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        f'<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Reporte {html.escape(modulo)}</title><style>{_CSS}</style><main>{cuerpo}</main></html>",
        encoding="utf-8",
    )
    return destino
