# Otimização de Rotas Hospitalares

Este projeto planeja entregas de medicamentos e insumos com uma frota de vários
veículos. O algoritmo genético considera distância, prioridade, capacidade de carga e
autonomia. Os resultados podem ser analisados em mapas, gráficos de convergência e
relatórios operacionais gerados pelo Gemini ou pelo gerador local.

## Execução pelo Jupyter

O caminho mais completo é o notebook `notebooks/projeto_completo.ipynb`. Abra-o no
VS Code ou Jupyter, selecione o kernel da `.venv` e use **Executar tudo**. O notebook
prepara o ambiente, valida o cenário, executa a otimização, compara abordagens de
referência e grava os resultados em `outputs`.

As explicações acompanham cada etapa e mostram como interpretar viabilidade, fitness,
distância e variação entre sementes. Quando um parâmetro ou dado de entrada for
alterado, execute novamente as células seguintes para manter os resultados coerentes.

## Preparação do ambiente

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Se o PowerShell bloquear `Activate.ps1`, use diretamente o Python do ambiente virtual:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m hospital_routes.cli --input data/deliveries.json --output outputs
```

## Interface interativa

```powershell
.\.venv\Scripts\python.exe -m hospital_routes.gui
```

Na interface, é possível alterar frota, entregas, capacidade, autonomia e parâmetros
do algoritmo. O campo `Elitismo` aceita zero e define quantos dos melhores indivíduos
passam intactos para a geração seguinte.

`Novo cenário` sorteia quantidades, limites, semente e coordenadas, inclusive a posição
do hospital. `Aplicar dados` usa os valores preenchidos nos campos. No mapa, o botão
direito inclui uma entrega em uma área vazia ou remove a entrega selecionada. Também
é possível arrastar pontos, clicar para mudar a prioridade e posicionar o cursor para
consultar coordenadas, carga e prioridade. O item `Instruções` resume esses comandos.

Durante a otimização, o mapa e os dois gráficos de convergência são atualizados a cada
geração.

## Linha de comando

```bash
python -m hospital_routes.cli --input data/deliveries.json --output outputs
```

Para executar sem acesso ao Gemini, acrescente `--llm local`.

## Configuração do Gemini

Crie uma chave em um projeto autorizado no Google AI Studio e mantenha-a fora do Git.
Para uso local, copie `.env.example` para `.env` e preencha `GEMINI_API_KEY`. Os
notebooks apenas informam se a chave foi encontrada; seu valor nunca é exibido.

Se a chave estiver ausente ou o provedor não responder, a otimização continua e o
gerador local produz um relatório determinístico. O job do Azure também segue esse
comportamento e não inclui credenciais nos manifestos.

## Azure Machine Learning

A pasta `azure` contém os manifestos do ambiente, do ativo de dados, do job serverless
e do sweep de hiperparâmetros. O Terraform em `infra/azure` provisiona o workspace e
seus recursos de apoio; o cluster usado pelo sweep é opcional.

Depois do provisionamento, abra `notebooks/azure_ml.ipynb`, informe os dados exibidos
por `terraform output` e execute as células em ordem. O notebook registra os ativos,
submete o job, acompanha os logs e baixa os artefatos. Consulte os READMEs dessas
pastas para detalhes sobre cotas e custos.

## Estrutura

- `src/hospital_routes`: modelos, algoritmo genético, métodos de referência, mapas e relatórios;
- `data`: cenário fictício e reproduzível;
- `notebooks`: execução completa e experimentação no Azure ML;
- `tests`: testes automatizados;
- `docs`: guia de uso e relatório técnico;
- `azure`: manifestos e script do experimento em nuvem;
- `infra/azure`: infraestrutura como código para o Azure Machine Learning.

Não há API REST nesta arquitetura. A solução é usada pela interface Pygame,
pelos notebooks, pela linha de comando e pelo job do Azure ML; portanto, não existem
endpoints HTTP a documentar.

O [relatório técnico](docs/relatorio_tecnico.pdf) apresenta a modelagem, as decisões
de implementação, os resultados experimentais e as limitações da solução.
