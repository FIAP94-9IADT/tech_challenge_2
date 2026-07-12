# Interface de visualização das rotas

Esta pasta contém o frontend do Tech Challenge. Usei React com Vite para exibir o
cenário, as rotas calculadas pelo backend, a curva de aptidão e a comparação com a
heurística Nearest Neighbor.

## Execução

```bash
npm install
npm run dev
```

A interface é aberta em `http://localhost:5173`. O backend deve estar ativo em
`http://localhost:8000`.

O mapa usa Google Maps quando `VITE_GOOGLE_MAPS_API_KEY` está configurada. Caso
contrário, usa Leaflet com OpenStreetMap. A integração com a LLM também depende da
chave configurada no backend, mas o algoritmo genético e as visualizações funcionam
sem ela.

## Deploy

A aplicação está implantada em https://rotas-frontend-obejqx6ika-uc.a.run.app

Para verificar a compilação de produção:

```bash
npm run build
```
