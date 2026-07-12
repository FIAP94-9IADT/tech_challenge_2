# Execução no Azure Machine Learning

Os arquivos usam Azure ML CLI v2. O job individual omite `compute` e, por isso, usa
computação serverless. O sweep utiliza `cpu-cluster`, provisionado com escala mínima
zero, para executar até quatro tentativas em paralelo.

## Preparação pelo Azure ML Studio

1. Provisione a infraestrutura descrita em `infra/azure`.
2. Abra o workspace no Azure ML Studio e inicie um terminal na Compute Instance, ou
   use o notebook `notebooks/azure_ml.ipynb`.
3. Registre ambiente e dados e submeta o job ou o sweep.
4. Acompanhe `fitness`, `total_distance_km` e `feasible` na área de experimentos.
5. Ao concluir os testes, confirme que o cluster voltou a zero nós e desligue a
   Compute Instance para evitar cobranças.

Os resultados de cada job ficam no output nomeado `artifacts`: `solution.json`, mapa,
convergência, relatório e histórico em CSV.
