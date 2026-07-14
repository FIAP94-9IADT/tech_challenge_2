# Infraestrutura Azure

O Terraform provisiona Resource Group, Storage Account, Key Vault, Log Analytics,
Application Insights e Azure Machine Learning Workspace. Por padrão, o cluster CPU
não é criado, o que permite concluir a infraestrutura mesmo em assinaturas com cota
de vCPU igual a zero.

```bash
az login
terraform init
terraform plan
terraform apply
terraform output
```

Para executar jobs, a assinatura também precisa ter cota de computação do Azure
Machine Learning na região escolhida. Isso vale inclusive para jobs serverless. Após
a liberação da cota, o cluster do sweep pode ser habilitado com:

```bash
az ml compute list-usage \
  --resource-group "$(terraform output -raw resource_group_name)" \
  --workspace-name "$(terraform output -raw workspace_name)" \
  --location brazilsouth \
  --output table

terraform apply -var="create_compute_cluster=true"
```

O cluster usa nós de baixa prioridade, escala de zero a quatro e retorna a zero após
dois minutos ocioso. Para `Standard_DS2_v2`, cada nó usa duas vCPUs; quatro nós
exigem cota para até oito vCPUs. O limite pode ser reduzido, por exemplo, com
`-var="max_compute_nodes=1"`.

Os nomes do resource group e workspace aparecem nos outputs. A criação gera custos;
ao encerrar os experimentos, use `terraform destroy`. A autenticação utiliza a sessão
do Azure CLI e nenhuma credencial é armazenada no repositório.

## Utilização do IaC

O estado (`terraform.tfstate`) e o plano (`tfplan`) são artefatos locais e não devem
ser versionados. Os mesmos arquivos podem ser aplicados em outra assinatura; o sufixo
aleatório evita colisões de nomes globais. A saída de `terraform output` fornece
`subscription_id`, `resource_group_name`, `workspace_name` e `location`, utilizados no
notebook `notebooks/azure_ml.ipynb`.
