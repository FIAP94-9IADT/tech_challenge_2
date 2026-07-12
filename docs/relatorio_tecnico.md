# Relatório técnico: otimização de rotas para distribuição de medicamentos

Tech Challenge, Fase 2, Projeto 2. FIAP/POSTECH, IA para Devs - Grupo 4

## 1. Definição do problema

Escolhemos o projeto de distribuição de medicamentos e insumos. O cenário tem um Hospital Central, que funciona como depósito, e um conjunto de entregas em UBSs, clínicas e atendimentos domiciliares. Cada entrega possui peso e prioridade. A frota tem vários veículos, cada um com capacidade e autonomia próprias.

O ponto inicial é o Problema do Caixeiro Viajante. No TSP, uma solução deve visitar
cada ponto uma vez e voltar à origem. Como o desafio pede mais de um veículo e
acrescenta restrições, tratei a aplicação como uma versão simplificada do Problema
de Roteamento de Veículos, o VRP.

Não usei dados reais de um hospital. O gerador cria pontos próximos ao centro de
São Paulo e recebe uma `seed`, o que permite repetir o mesmo experimento. Na
primeira implementação, eu sorteava a capacidade dos veículos sem considerar a
demanda total. Muitos cenários ficavam inviáveis antes mesmo da otimização. Corrigi
isso dimensionando a frota com uma margem de 20% a 60% sobre a demanda média por
veículo.

## 2. Fundamentos aplicados

As escolhas centrais da implementação foram:


| Fundamento                               | Aplicação no projeto                                                  |
| ---------------------------------------- | --------------------------------------------------------------------- |
| TSP e heurística do vizinho mais próximo | Formulação do problema e criação do baseline                          |
| Codificação combinatória                 | Cromossomo como sequência de identificadores de entrega               |
| Função de aptidão                        | Avaliação por distância, prioridade e restrições                      |
| Order Crossover                          | Cruzamento que mantém uma permutação válida                           |
| Mutação por troca e por inversão         | Geração de novas sequências sem repetir entregas                      |
| Seleção proporcional                     | Implementação da seleção por roleta                                   |
| População, término e visualização        | Laço de gerações, histórico da melhor aptidão e parada por estagnação |
| Engenharia de prompt                     | Instruções diretas e formato de saída definido                        |
| Controle de respostas da LLM             | Restrição das respostas ao contexto enviado                           |
| Computação serverless                    | Proposta opcional de implantação no Cloud Run                         |


O código de TSP usado como ponto de partida está em `genetic_algorithm_tsp/`.
Mantive essa pasta separada para facilitar a comparação com a solução final.

## 3. Adaptação do código base


| Aspecto       | Código base                  | Implementação deste projeto                   |
| ------------- | ---------------------------- | --------------------------------------------- |
| Representação | Lista de coordenadas         | Permutação dos identificadores das entregas   |
| Distância     | Euclidiana em pixels         | Haversine em quilômetros                      |
| Aptidão       | Distância do ciclo           | Distância, prioridade e penalidades           |
| Veículos      | Um                           | Vários, por meio de uma divisão gulosa        |
| Cruzamento    | Order Crossover              | Mesmo operador, adaptado para identificadores |
| Mutação       | Troca de vizinhos            | Troca de vizinhos e inversão de segmento      |
| Seleção       | Melhores indivíduos e roleta | Torneio configurável e roleta                 |
| Término       | Execução contínua no Pygame  | Número de gerações ou estagnação              |




### 3.1 Representação e divisão das rotas

O cromossomo é uma permutação de todas as entregas, também chamada de `giant tour`. Essa é uma codificação combinatória: a posição do gene indica a ordem da
entrega.

Depois do cruzamento e da mutação, o método `split_tour` percorre o cromossomo e
inclui entregas no veículo atual enquanto houver capacidade e autonomia para sair
do depósito, atender as paradas e retornar. Quando a próxima entrega não cabe, o
método passa para o veículo seguinte. Entregas que não couberem em nenhum veículo
ficam na lista de não alocadas.

Essa divisão é simples e preserva a ordem dos genes. Ela também permite reutilizar
o Order Crossover, pois o cromossomo continua sendo uma permutação válida. A
limitação é que o corte entre veículos é guloso e pode rejeitar uma entrega que
caberia em outra organização das mesmas paradas.

### 3.2 Função de aptidão

Usei uma função de minimização:

```text
fitness = distância_total_km
        + 50 * kg_acima_da_capacidade
        + 50 * km_acima_da_autonomia
        + 1000 * entregas_não_alocadas
        + 0,30 * soma(peso_prioridade * distância_acumulada_até_a_parada)
```

Na execução normal, o `split_tour` só monta rotas que respeitam a capacidade e a
autonomia. Por isso, as duas penalidades de violação funcionam como uma proteção
do avaliador e são exercitadas isoladamente nos testes, mas geralmente ficam
zeradas nas soluções produzidas pelo decodificador. Quando a frota não consegue
receber todos os pontos, a penalidade que afeta a busca é a de entregas não
alocadas.

O termo de prioridade usa a distância acumulada até cada parada. Entregas críticas
têm peso maior, então sua presença no fim da rota aumenta a aptidão, o que é ruim
em um problema de minimização. Entregas normais têm peso zero nesse termo. Escolhi
o coeficiente 0,30 depois de testes locais, pois valores maiores faziam o algoritmo
aceitar percursos longos para antecipar uma entrega crítica.

### 3.3 Operadores genéticos

Implementei duas formas de seleção. O torneio sorteia três indivíduos e escolhe o
de menor aptidão. A roleta usa o inverso da aptidão, pois valores menores
representam soluções melhores.

No cruzamento, mantive o Order Crossover. Uma parte do primeiro pai é copiada e os
genes restantes são preenchidos na ordem em que aparecem no segundo pai. O
operador evita entregas repetidas ou ausentes.

A mutação usa inversão de segmento em 70% das chamadas e troca de vizinhos nas
demais. A inversão consegue desfazer cruzamentos de caminho com uma única
alteração. Por fim, o elitismo copia os dois melhores indivíduos para a próxima
geração.

## 4. Experimentos

Mantive o mesmo cenário em todas as execuções: 25 entregas, 3 veículos, `seed`
42 e 400 gerações. Comparei quatro configurações do algoritmo genético com a
heurística Nearest Neighbor. O baseline cria a sequência escolhendo sempre o ponto
mais próximo e usa o mesmo `split_tour` e a mesma função de avaliação do AG.


| Configuração     | População | Mutação | Seleção | Fitness | Distância (km) | Viável | Tempo (s) |
| ---------------- | --------- | ------- | ------- | ------- | -------------- | ------ | --------- |
| Nearest Neighbor | -         | -       | -       | 188,1   | 157,1          | sim    | <0,1      |
| A                | 50        | 0,1     | torneio | 208,0   | 184,1          | sim    | 0,2       |
| B                | 150       | 0,3     | torneio | 186,9   | 159,0          | sim    | 0,6       |
| C                | 150       | 0,3     | roleta  | 190,9   | 153,8          | sim    | 1,2       |
| D                | 300       | 0,5     | torneio | 159,7   | 138,3          | sim    | 1,3       |


Curvas de convergênciaComparação da distância total

A configuração A terminou pior que o baseline. Com população pequena e mutação
baixa, ela perdeu diversidade e estabilizou em uma solução inferior. A configuração
D obteve o menor valor de aptidão e percorreu 138,3 km, uma redução de cerca de
12% na distância em relação ao Nearest Neighbor.

A configuração C percorreu menos quilômetros que a B, mas teve aptidão maior. A
diferença indica que a ordem das entregas prioritárias também influenciou o
resultado. Neste cenário e com esta semente, o torneio da configuração D teve o
melhor resultado. Um único cenário não permite concluir que torneio sempre supera
roleta.

Os tempos ficaram abaixo de dois segundos no computador usado para o experimento.
Eles servem para comparar estas quatro execuções, não como medida geral de
desempenho em produção.

## 5. Integração com a LLM

A API oferece três operações com a LLM:

1. instruções de entrega para um veículo ou para toda a frota;
2. relatório diário ou semanal com os dados da rota e a comparação com o baseline;
3. perguntas em linguagem natural sobre a última solução calculada.

Centralizei os textos em `backend/app/services/prompts.py`. O contexto é enviado
em JSON com nomes, pesos, prioridades, capacidade, autonomia e ordem das paradas.
O prompt de sistema define a função de coordenador de logística hospitalar. Também
instrui o modelo a responder somente com os dados recebidos e a informar quando
uma resposta não estiver no contexto.

Usei temperatura 0,2 nas perguntas e 0,4 nas instruções e relatórios. Durante a
verificação manual, comparei nomes, pesos e sequência das paradas com o JSON
enviado. Perguntas diretas sobre quantidade ou localização das entregas críticas
foram respondidas de acordo com esse contexto. Ainda assim, a verificação é
qualitativa e não substitui uma avaliação com casos registrados e critérios de
pontuação.

A principal limitação apareceu em cálculos com várias rotas. A LLM pode arredondar
ou somar valores de forma incorreta. Por esse motivo, os totais que já existem no
sistema são calculados em Python antes do envio. Uma evolução possível é calcular
todos os indicadores no backend e deixar para a LLM apenas a redação.

## 6. Arquitetura e testes

O backend usa Flask. O algoritmo genético está isolado em `app/core/` e não depende
do framework web. O frontend usa React e apresenta as rotas no mapa, o histórico de
aptidão e os dados de cada veículo. Os resultados da LLM ficam em cache até que uma
nova otimização seja executada.

Criei 31 testes com `pytest`. Eles verificam a distância haversine, os termos da
função de aptidão, a validade do Order Crossover, as mutações, a divisão das rotas e
os endpoints. As chamadas externas da LLM são substituídas por mocks nos testes da
API.

A implantação no GCP é opcional. A proposta usa imagens Docker no Cloud Run e
Terraform para declarar os recursos. A chave da API fica no Secret Manager. O
diagrama e os comandos estão em `docs/arquitetura.md`.

## 7. Limitações e possíveis melhorias

O `split_tour` é o principal limite da solução. Ele decide os cortes na ordem em
que encontra as entregas e não reconsidera veículos anteriores. Eu substituiria
essa etapa por um método de divisão ótima do `giant tour` e acrescentaria uma busca
local 2-opt dentro de cada rota.

O cenário também não possui janelas de horário, tempo de atendimento, trânsito ou
compatibilidade entre carga e veículo. Esses dados tornariam o problema mais
próximo da operação de um hospital, mas exigiriam outra forma de geração e
validação dos cenários.

Por fim, os experimentos usam um cenário e uma semente. Para uma avaliação mais
forte, eu executaria cada configuração com várias sementes e apresentaria média,
desvio padrão e taxa de soluções viáveis.