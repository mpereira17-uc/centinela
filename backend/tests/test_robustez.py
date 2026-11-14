"""Que el servidor siga atendiendo aunque alguien abuse de él (modelo de amenazas, A6)."""
from datetime import timedelta

from fastapi.testclient import TestClient

from app import main
from app.main import app

cliente = TestClient(app)


def test_las_llamadas_viejas_se_borran_y_nunca_se_bloquean_las_nuevas(monkeypatch):
    # Antes: después de 1000 conversaciones el servidor rechazaba todas las llamadas nuevas
    monkeypatch.setattr(main, "MAX_LLAMADAS", 5)
    main.llamadas.clear()
    ids = [cliente.post("/llamadas").json()["id"] for _ in range(5)]
    nueva = cliente.post("/llamadas")
    assert nueva.status_code == 201
    assert len(main.llamadas) == 5 and ids[0] not in main.llamadas  # sale la más antigua
    # Las vencidas salen primero, aunque no esté lleno
    vieja = main.llamadas[ids[1]]
    vieja.creada -= timedelta(seconds=main.VIDA_LLAMADA + 1)
    cliente.post("/llamadas")
    assert ids[1] not in main.llamadas
    main.llamadas.clear()


def test_crear_llamadas_en_bucle_tiene_limite():
    codigos = [cliente.post("/llamadas").status_code for _ in range(main.limite_llamadas.maximo + 1)]
    assert codigos[:-1] == [201] * main.limite_llamadas.maximo and codigos[-1] == 429
    main.llamadas.clear()


def test_abrir_salas_en_bucle_tiene_limite():
    from app import senalizacion

    codigos = [cliente.post("/salas").status_code for _ in range(senalizacion.limite_salas.maximo + 1)]
    assert codigos[-1] == 429
    senalizacion.salas.clear()


def test_el_chequeo_y_el_asistente_tienen_limite():
    from app import chequeo

    codigos = [cliente.post("/chequeo", json={}).status_code for _ in range(chequeo.limite_chequeo.maximo + 1)]
    assert codigos[-2] == 200 and codigos[-1] == 429
    codigos = [cliente.post("/asistente", json={"texto": "hola"}).status_code for _ in range(main.limite_asistente.maximo + 1)]
    assert codigos[-1] == 429


def test_transcribir_y_sintetizar_voz_tienen_limite():
    # Whisper y Piper son lo que más CPU gasta; sin límite, un bucle de subidas tumba el equipo
    fuente = (main.__file__ and open(main.__file__, encoding="utf-8").read())
    for decorador in ('@app.post("/llamadas/{llamada_id}/audio", dependencies=[Depends(limite_audio)])',
                      '@app.post("/asistente/voz", dependencies=[Depends(limite_audio)])',
                      '@app.post("/voz", dependencies=[Depends(limite_voz)])',
                      '@app.post("/llamadas/{llamada_id}/fragmentos", dependencies=[Depends(limite_fragmentos)])'):
        assert decorador in fuente, decorador
