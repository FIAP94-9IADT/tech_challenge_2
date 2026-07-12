# Tech Challenge Fase 2: otimização de rotas para distribuição de medicamentos

Este repositório contém minha entrega do Projeto 2 da Fase 2 da pós-graduação
IA para Devs, da FIAP/POSTECH. O problema proposto é organizar a distribuição
de medicamentos e insumos entre um hospital, unidades de saúde e atendimentos
domiciliares.

Usei como ponto de partida o código de TSP incluído no desafio, que
está preservado em `genetic_algorithm_tsp/`. A partir dele, troquei a distância
euclidiana em pixels pela distância haversine, passei a representar as entregas
por identificadores e dividi a sequência encontrada pelo algoritmo entre vários
veículos. Também incluí prioridade das entregas, capacidade de carga e autonomia.

A parte de linguagem natural usa a API da OpenAI para produzir instruções de
entrega, um relatório de eficiência e respostas sobre a solução calculada. A
otimização continua funcionando quando não há uma chave configurada.

As adaptações para o cenário hospitalar, os operadores genéticos e a integração
com a LLM estão explicados em `docs/relatorio_tecnico.md`.

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| `backend/` | API Flask, algoritmo genético, dados sintéticos e integração com a LLM |
| `frontend/` | Interface React com mapa, gráfico de convergência e chat |
| `infra/` | Configuração Terraform para uma implantação opcional no GCP |
| `docs/` | Relatório técnico, arquitetura, roteiro do vídeo e gráficos |
| `genetic_algorithm_tsp/` | Código base de TSP incluído no desafio |

## Execução local

### Backend

O projeto usa Python 3.12 ou superior e um ambiente virtual, conforme solicitado
no enunciado.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --port 8000
```

Para habilitar os recursos da LLM, copie `backend/.env.example` para
`backend/.env` e informe `OPENAI_API_KEY`. Sem essa variável, os endpoints da LLM
retornam uma mensagem de configuração e os demais recursos continuam disponíveis.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

O frontend é aberto em `http://localhost:5173` e espera o backend na porta 8000.
Quando `VITE_GOOGLE_MAPS_API_KEY` não está definida, o mapa usa Leaflet e
OpenStreetMap.

### Testes

```bash
cd backend
source .venv/bin/activate
pytest
```

### Experimentos

```bash
cd backend
.venv/bin/python experiments/run_experiments.py
```

O script repete o mesmo cenário com quatro configurações do algoritmo genético e
compara os resultados com a heurística Nearest Neighbor. Ele também atualiza os
gráficos em `docs/img/`.

## API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/health` | Verifica se a API está ativa |
| GET | `/api/scenario` | Gera um cenário sintético |
| POST | `/api/optimize` | Executa o algoritmo genético e o baseline |
| POST | `/api/llm/instructions` | Gera instruções de entrega |
| POST | `/api/llm/report` | Gera um relatório de eficiência |
| POST | `/api/llm/ask` | Responde perguntas sobre as rotas |

Exemplo de otimização:

```bash
curl -X POST http://localhost:8000/api/optimize \
  -H 'Content-Type: application/json' \
  -d '{"n_points": 20, "n_vehicles": 3, "population_size": 150, "generations": 400}'
```

## Implantação opcional

A aplicação está implantada em https://rotas-frontend-obejqx6ika-uc.a.run.app

A pasta `infra/` contém a configuração de Cloud Run, Artifact Registry e Secret
Manager por meio do Terraform. O procedimento e as decisões adotadas estão em
`docs/arquitetura.md`. A chave da OpenAI deve ser criada diretamente no Secret
Manager e não deve ser gravada no código ou no estado do Terraform.

## Documentação

- [Relatório técnico](docs/relatorio_tecnico.md)
- [Arquitetura](docs/arquitetura.md)
- [Roteiro do vídeo](docs/roteiro_video.md)
