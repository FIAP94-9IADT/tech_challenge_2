# Execução no Azure Machine Learning

Os arquivos usam Azure ML CLI v2. O job individual omite `compute` e, por isso, usa
computação serverless. Mesmo nesse modo, é necessário haver cota de vCPU do Azure
Machine Learning na região. O sweep utiliza `cpu-cluster`, que é opcional no Terraform
e deve ser habilitado somente após a liberação da cota.

## Preparação pelo Azure ML Studio

1. Provisione a infraestrutura descrita em `infra/azure`.
2. Confirme a cota de computação na região; para usar o sweep, crie o cluster com
   `terraform apply -var="create_compute_cluster=true"`.
3. Abra o workspace no Azure ML Studio e inicie um terminal na Compute Instance, ou
   use o notebook `notebooks/azure_ml.ipynb`.
4. Registre ambiente e dados e submeta o job ou o sweep.
5. Acompanhe `fitness`, `total_distance_km` e `feasible` na área de experimentos.
6. Ao concluir os testes, confirme que o cluster voltou a zero nós e desligue a
   Compute Instance para evitar cobranças.

Os resultados de cada job ficam no output nomeado `artifacts`: `solution.json`, mapa,
convergência, relatório e histórico em CSV.

## Ordem recomendada para avaliação

1. No Azure Cloud Shell, clone o repositório e aplique `infra/azure` conforme o README
   daquela pasta. O cluster é opcional e não é necessário para o job principal.
2. Confirme que a assinatura possui pelo menos duas vCPUs do Azure Machine Learning
   para `Standard_DS2_v2` na região do workspace.
3. No Azure ML Studio, abra **Notebooks**, clone ou carregue o repositório e associe
   um kernel Python a uma Compute Instance disponível.
4. Abra `notebooks/azure_ml.ipynb` e execute as células na ordem. Os identificadores
   necessários podem ser copiados diretamente de `terraform output`.

O notebook verifica a estrutura local, conecta-se ao workspace, registra ambiente e
dados, submete o job serverless, acompanha sua conclusão e baixa os artefatos. O sweep
é separado e desativado por padrão porque requer `cpu-cluster`, mais cota e mais tempo.

## Segurança no envio do código

O arquivo `.amlignore` limita o pacote enviado ao Azure ML e exclui `.env`, histórico
Git, notebooks, infraestrutura, testes e resultados locais. A chave do Gemini não é
necessária para validar a otimização: sem a variável `GEMINI_API_KEY`, o job gera o
relatório determinístico local. Nenhuma credencial deve ser inserida nos manifestos.
