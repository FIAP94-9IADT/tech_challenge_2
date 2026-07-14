# Execução no Azure Machine Learning

Esta pasta reúne os manifestos do Azure ML CLI v2 e o script executado na nuvem. O
job principal usa computação serverless porque `job.yml` não define um cluster. O
sweep, por sua vez, usa o `cpu-cluster` opcional do Terraform.

Mesmo no modo serverless, a assinatura precisa ter cota de vCPU do Azure Machine
Learning na região escolhida. O job principal usa um `Standard_DS2_v2`, equivalente a
duas vCPUs.

## Passo a passo

1. Provisione a infraestrutura descrita em `infra/azure`.
2. Confirme a cota regional. Se quiser executar o sweep, habilite o cluster com
   `terraform apply -var="create_compute_cluster=true"`.
3. No Azure ML Studio, abra **Notebooks** e carregue ou clone o repositório.
4. Associe o notebook a uma Compute Instance disponível e abra
   `notebooks/azure_ml.ipynb`.
5. Copie os identificadores apresentados por `terraform output` e execute as células
   na ordem.
6. Acompanhe `fitness`, `total_distance_km`, `feasible` e as curvas por geração na
   página do experimento.
7. Ao terminar, desligue a Compute Instance. Se o sweep tiver sido usado, confirme que
   o cluster voltou a zero nós.

O notebook verifica a estrutura do projeto, conecta-se ao workspace, registra ambiente
e dados, submete o job, acompanha os logs e baixa os resultados. O sweep permanece
desativado por padrão porque exige mais tempo, cota e recursos.

## Resultados

O output `artifacts` contém:

- `solution.json`;
- `routes_map.html`;
- `convergence.png`;
- `daily_report.md`;
- `history.csv`.

## Segurança no envio do código

O arquivo `.amlignore` impede o envio de `.env`, histórico Git, notebooks,
infraestrutura, testes, dados locais e resultados anteriores. Nenhuma credencial deve
ser escrita nos manifestos.

A chave Gemini não é obrigatória para a otimização. Quando `GEMINI_API_KEY` não
está disponível no ambiente remoto, o job gera o relatório local e mantém todos os
demais artefatos.
