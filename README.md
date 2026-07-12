# Otimização de Rotas Hospitalares

Sistema em Python para planejar entregas de medicamentos e insumos com múltiplos
veículos. A solução usa um algoritmo genético com representação combinatória,
restrições de capacidade, autonomia e prioridade, visualização em mapa e geração de
instruções operacionais com uma LLM pré-treinada.

## Execução rápida

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m hospital_routes.cli --input data/deliveries.json --output outputs
```

## Interface interativa

```powershell
.\.venv\Scripts\python.exe -m hospital_routes.gui
```

## Execução integral pelo Jupyter

Abra `notebooks/projeto_completo.ipynb` no VS Code ou Jupyter, selecione o kernel da
`.venv` e use **Executar tudo**. O próprio notebook prepara o projeto, permite alterar
cenário e parâmetros, acompanha a convergência e gera todos os arquivos em `outputs`.

## Azure Machine Learning

A pasta `azure` contém o script de experimento, ambiente, ativo de dados, job
serverless e sweep de hiperparâmetros. A infraestrutura do workspace e do cluster CPU
fica em `infra/azure`. Depois do provisionamento, abra `notebooks/azure_ml.ipynb`,
informe assinatura, Resource Group e workspace e execute as células para registrar os
ativos e submeter os jobs.

## Configuração segura do Gemini

Crie uma chave em um projeto autorizado no Google AI Studio e mantenha-a fora do Git.
Para execução local, copie `.env.example` para `.env` e preencha `GEMINI_API_KEY`.
Os notebooks informam se a chave foi detectada e continuam com o gerador local quando
ela não estiver disponível. Em Docker e Azure, forneça `GEMINI_API_KEY` como variável
protegida.

A interface permite alterar quantidade de entregas e veículos, capacidade, autonomia,
população, gerações, taxas de crossover e mutação e semente aleatória. Os pontos de
entrega podem ser arrastados no mapa; um clique curto alterna sua prioridade. O campo
`Elitismo` define quantos dos melhores indivíduos passam intactos para a próxima
geração. Durante a otimização, as rotas e o gráfico de convergência são atualizados a cada geração.

`Novo cenário` sorteia quantidades, frota, capacidade, autonomia, semente e posições,
incluindo uma nova posição para o hospital. `Aplicar dados` cria o cenário usando os
valores digitados. Ao manter o cursor sobre qualquer entrega ou sobre o hospital, são
exibidas suas coordenadas; para entregas, também aparecem prioridade e carga.
No mapa, um clique com o botão direito em uma área vazia inclui uma entrega, enquanto
um clique direito sobre uma entrega existente a remove. O hospital não pode ser
removido e o cenário mantém ao menos uma entrega.
O indicador `Instruções`, acima do mapa, apresenta um resumo dessas interações ao
receber o cursor.

Se o PowerShell bloquear o `Activate.ps1`, não é necessário mudar a política de
execução do Windows. Use diretamente o interpretador do ambiente virtual:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m hospital_routes.cli --input data/deliveries.json --output outputs
```

Os relatórios usam por padrão a integração Gemini configurada no projeto. O modo
determinístico permanece disponível com `--llm local` para testes sem acesso à rede.

```bash
pytest
jupyter notebook notebooks/demonstracao.ipynb
```

## Estrutura

- `src/hospital_routes`: modelos, algoritmo genético, baselines, mapas e relatórios;
- `data`: cenário fictício e reproduzível;
- `notebooks`: demonstração explicada e análise dos resultados;
- `tests`: testes unitários e de integração;
- `docs`: relatório técnico, arquitetura e documentação de uso;
- `infra`: infraestrutura como código para execução conteinerizada em nuvem.

Consulte [docs/relatorio_tecnico.md](docs/relatorio_tecnico.md) para as decisões de
modelagem, limitações e análises.
