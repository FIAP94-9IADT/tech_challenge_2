# Arquitetura

## Visão geral (local)

```mermaid
flowchart LR
    subgraph Frontend [React + Vite]
        UI[Painel de configuração]
        MAP[Mapa Leaflet]
        CHART[Gráfico de convergência]
        CHAT[Chat Q&A]
    end

    subgraph Backend [Flask]
        API[Blueprint /api]
        GA[Núcleo AG<br/>core/]
        SPLIT[Decoder VRP<br/>split guloso]
        NN[Baseline<br/>Nearest Neighbor]
        SYN[Gerador sintético<br/>data/]
        LLM[LLM Service<br/>services/]
    end

    OPENAI[(OpenAI API<br/>gpt-4o-mini)]

    UI -->|POST /api/optimize| API
    CHAT -->|POST /api/llm/ask| API
    MAP -.->|rotas| API
    API --> SYN --> GA
    GA --> SPLIT
    API --> NN
    API --> LLM --> OPENAI
```

## Fluxo da otimização

```mermaid
sequenceDiagram
    participant U as Usuário
    participant F as Frontend
    participant B as Backend Flask
    participant G as AG (core)
    participant L as OpenAI

    U->>F: configura cenário e parâmetros
    F->>B: POST /api/optimize
    B->>B: gera cenário sintético (seed)
    B->>G: run_ga(depot, points, vehicles, config)
    loop gerações
        G->>G: avaliação (split + fitness) → seleção → OX → mutação
    end
    G-->>B: melhor solução + histórico
    B->>B: baseline Nearest Neighbor
    B-->>F: rotas, convergência, comparativo
    F-->>U: mapa + gráfico + cards

    U->>F: "qual van leva os críticos?"
    F->>B: POST /api/llm/ask
    B->>L: system prompt + contexto JSON + pergunta
    L-->>B: resposta
    B-->>F: answer
```

## Nuvem (GCP)

```mermaid
flowchart LR
    DEV[Dev local] -->|gcloud builds submit| CB[Cloud Build]
    CB --> AR[(Artifact Registry)]
    AR --> CRB[Cloud Run<br/>rotas-backend<br/>scale to zero]
    AR --> CRF[Cloud Run<br/>rotas-frontend<br/>nginx]
    SM[(Secret Manager<br/>openai-api-key)] -->|env var| CRB
    USER([Usuário]) --> CRF -->|VITE_API_URL| CRB
    CRB --> OPENAI[(OpenAI API)]
    TF[Terraform<br/>infra/] -.provisiona.-> AR & CRB & CRF & SM
```

Escolhi o Cloud Run por ser um serviço serverless com escalabilidade automática.
Limitei o serviço a duas instâncias para controlar o uso durante a demonstração.

As imagens Docker ficam no Artifact Registry. A chave da OpenAI fica no Secret
Manager e é injetada no backend como variável de ambiente, sem ser gravada no
código ou no estado do Terraform. Declarei os recursos em `infra/` com Terraform.
Usei a região `us-central1` na configuração de exemplo.

## Deploy passo a passo

```bash
# 0. pré-requisitos: gcloud CLI + terraform instalados, projeto criado
gcloud auth login
gcloud auth application-default login
gcloud config set project SEU_PROJETO

# 1. provisionar a infra (na primeira vez o apply cria o Artifact Registry;
#    os serviços Cloud Run só sobem depois do push das imagens)
cd infra
cp terraform.tfvars.example terraform.tfvars   # editar project_id e imagens
terraform init
terraform apply -target=google_artifact_registry_repository.repo \
                -target=google_secret_manager_secret.openai_key

# 2. subir a chave da OpenAI (fora do state do Terraform, de propósito)
echo -n "sk-..." | gcloud secrets versions add openai-api-key --data-file=-

# 3. build + push das imagens via Cloud Build
gcloud builds submit ../backend \
  -t us-central1-docker.pkg.dev/SEU_PROJETO/rotas-medicas/backend:latest

# o frontend precisa saber a URL do backend em build time (Vite),
# por isso uso um cloudbuild.yaml com build-arg:
gcloud builds submit ../frontend --config ../frontend/cloudbuild.yaml \
  --substitutions=_VITE_API_URL=https://rotas-backend-XXXX.run.app,_IMAGE=us-central1-docker.pkg.dev/SEU_PROJETO/rotas-medicas/frontend:latest

# 4. subir o resto da infra
terraform apply

# 5. URLs de saída
terraform output frontend_url
terraform output backend_url
```

URL atual do frontend em produção: https://rotas-frontend-obejqx6ika-uc.a.run.app
