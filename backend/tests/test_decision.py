"""Aviso crítico que pide una decisión: "Cuelgo y verifico" o "Sigo, sé lo que hago" tras una pausa."""
import re

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)
PAGINAS_CON_AVISO = ("/", "/llamada.html", "/acompanante.html")


def test_las_tres_pantallas_con_aviso_piden_decidir():
    for pagina in PAGINAS_CON_AVISO:
        html = cliente.get(pagina).text
        i = html.index('id="alerta"')
        aviso = html[i:html.index("</section>", i)]
        assert 'class="alerta-decision oculto"' in aviso, pagina
        assert ">Cuelgo y verifico<" in aviso and ">Sigo, sé lo que hago<" in aviso, pagina
        # "Entendido" sigue para los avisos que no son críticos
        assert 'id="cerrar-alerta"' in aviso, pagina
        assert "Buscar el canal oficial" in aviso, pagina


def test_seguir_espera_una_pausa_y_solo_en_critico():
    js = cliente.get("/comun.js").text
    pausa = int(re.search(r"PAUSA_PARA_SEGUIR = (\d+)", js).group(1))
    assert 3 <= pausa <= 10
    assert 'prepararDecision(alerta, decision.nivel === "critico")' in js
    # Escape y deslizar no se saltan la decisión
    assert "cerrarConGesto" in js and "sigo.disabled" in js


def test_colgar_desde_el_aviso_termina_la_llamada_por_centinela():
    assert '"centinela:decision"' in cliente.get("/llamada.js").text
    assert '"centinela:decision"' in cliente.get("/acompanante.js").text
