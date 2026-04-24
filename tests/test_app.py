from pathlib import Path

from fastapi.testclient import TestClient

from backend.server import create_app


def build_user_payload() -> dict:
    return {
        "profile_name": "leonardo",
        "nome": "Leonardo Ribeiro",
        "email": "leo@example.com",
        "telefone": "(11) 99999-0000",
        "linkedin": "linkedin.com/in/leonardo",
        "github": "github.com/leonardo",
        "cidade": "Sao Paulo",
        "estado": "SP",
        "cargo_atual": "Desenvolvedor Full Stack",
        "experiencias": [
            {
                "empresa": "Empresa A",
                "cargo": "Backend Developer",
                "periodo": "2022 - Atual",
                "descricao": "Atuação com Python, FastAPI, Docker e APIs REST.",
                "tecnologias": ["Python", "FastAPI", "Docker"],
                "realizacoes": ["Reduziu tempo de deploy", "Criou APIs escaláveis"],
            },
            {
                "empresa": "Empresa B",
                "cargo": "Software Engineer",
                "periodo": "2020 - 2022",
                "descricao": "Desenvolvimento com React, Node.js e PostgreSQL.",
                "tecnologias": ["React", "Node.js", "PostgreSQL"],
                "realizacoes": ["Entregou painel administrativo"],
            },
        ],
        "educacao": [
            {
                "instituicao": "Universidade X",
                "curso": "Ciência da Computação",
                "periodo": "2016 - 2019",
            }
        ],
        "habilidades": ["Python", "FastAPI", "Docker", "React", "Node.js", "PostgreSQL"],
        "idiomas": [{"idioma": "Inglês", "nivel": "Avançado"}],
    }


def test_user_and_resume_flow(tmp_path: Path) -> None:
    data_file = tmp_path / "app_state.json"
    output_dir = tmp_path / "output"
    client = TestClient(create_app(data_file=str(data_file), output_dir=str(output_dir), enable_llm=False))

    user_response = client.post("/api/users", json=build_user_payload())
    assert user_response.status_code == 201
    user = user_response.json()

    active_response = client.get("/api/users/active/current")
    assert active_response.status_code == 200
    assert active_response.json()["id"] == user["id"]

    job_payload = {
        "input_type": "text",
        "content": """
        Cargo: Backend Developer
        Empresa: Tech Corp
        Local: São Paulo
        Buscamos alguém com Python, FastAPI, Docker, APIs REST e PostgreSQL.
        É importante ter boa comunicação e trabalho em equipe.
        """,
    }
    job_response = client.post("/api/resume/jobs", json=job_payload)
    assert job_response.status_code == 200
    job = job_response.json()
    assert job["cargo"] == "Backend Developer"
    assert "Python" in job["requisitos_tecnicos"]

    generate_response = client.post(f"/api/resume/jobs/{job['id']}/generate", json={"count": 2})
    assert generate_response.status_code == 200
    assert generate_response.json()["generated_variants"] == 2

    variants_response = client.get(f"/api/resume/jobs/{job['id']}/variants")
    assert variants_response.status_code == 200
    variants = variants_response.json()
    assert len(variants) == 2
    assert variants[0]["content"]["nome"] == "Leonardo Ribeiro"

    history_response = client.get("/api/resume/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history[0]["variants_count"] == 2
    assert history[0]["has_cvs"] is True

    download_response = client.get(f"/api/resume/variants/{variants[0]['id']}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    saved_files = list(output_dir.glob("*.docx"))
    assert saved_files


def test_generate_requires_active_user(tmp_path: Path) -> None:
    client = TestClient(
        create_app(data_file=str(tmp_path / "state.json"), output_dir=str(tmp_path / "output"), enable_llm=False)
    )

    job_response = client.post(
        "/api/resume/jobs",
        json={"input_type": "text", "content": "Cargo: QA Engineer\nEmpresa: Testes SA\nExperiência com API e automação."},
    )
    assert job_response.status_code == 200
    job_id = job_response.json()["id"]

    generate_response = client.post(f"/api/resume/jobs/{job_id}/generate", json={"count": 1})
    assert generate_response.status_code == 400
    assert "No active user set" in generate_response.json()["detail"]
