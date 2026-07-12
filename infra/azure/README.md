# Infraestrutura Azure

O Terraform provisiona Resource Group, Storage Account, Key Vault, Log Analytics,
Application Insights, Azure Machine Learning Workspace e um cluster CPU. O cluster
usa nós de baixa prioridade, escala de zero a quatro e retorna a zero após dois minutos
ocioso. Command jobs individuais usam serverless e não dependem do cluster.

```bash
az login
terraform init
terraform plan
terraform apply
```

Os nomes do resource group e workspace aparecem nos outputs. A criação gera custos;
ao encerrar os experimentos, use `terraform destroy`. A autenticação utiliza a sessão
do Azure CLI e nenhuma credencial é armazenada no repositório.
