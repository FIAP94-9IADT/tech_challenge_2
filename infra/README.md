# Infraestrutura como código

O Terraform usa o provedor Docker para construir e executar a mesma imagem em um
ambiente reproduzível. É uma implantação local, suficiente para demonstrar o
provisionamento sem criar custos ou depender de uma conta em nuvem.

```bash
terraform init
terraform plan
terraform apply
```

A chave da LLM é opcional e deve ser informada por variável sensível, nunca incluída
no controle de versão: `terraform apply -var="gemini_api_key=..."`.
