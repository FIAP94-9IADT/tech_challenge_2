# Infraestrutura Azure

O Terraform provisiona Resource Group, Storage Account, Key Vault, Log Analytics,
Application Insights e Azure Machine Learning Workspace. O cluster do sweep é
opcional e não é criado por padrão. Dessa forma, o workspace pode ser provisionado
mesmo quando a assinatura ainda não possui cota de vCPU.

## Provisionamento

Em uma sessão autenticada do Azure Cloud Shell, execute:

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
terraform output
```

Os outputs apresentam `subscription_id`, `resource_group_name`, `workspace_name` e
`location`. Esses valores são usados na configuração do notebook
`notebooks/azure_ml.ipynb`.

## Cota e cluster opcional

Jobs serverless também consomem cota do Azure Machine Learning. Consulte a cota da
região com:

```bash
az ml compute list-usage \
  --resource-group "$(terraform output -raw resource_group_name)" \
  --workspace-name "$(terraform output -raw workspace_name)" \
  --location "$(terraform output -raw location)" \
  --output table
```

Depois que a cota estiver disponível, crie o cluster do sweep com:

```bash
terraform apply \
  -var="create_compute_cluster=true" \
  -var="max_compute_nodes=1"
```

O cluster usa nós de baixa prioridade e volta a zero depois de dois minutos ocioso.
Cada `Standard_DS2_v2` usa duas vCPUs. O limite pode chegar a quatro nós, desde que a
assinatura tenha cota suficiente.

## Estado e encerramento

`terraform.tfstate` e `tfplan` são arquivos locais e não devem ser versionados. O
sufixo aleatório dos recursos evita colisões de nomes quando o IaC é aplicado em outra
assinatura.

Os recursos podem gerar cobrança. Quando não forem mais necessários, revise o plano de
remoção e encerre a infraestrutura:

```bash
terraform plan -destroy
terraform destroy
```

A autenticação usa a sessão do Azure CLI; nenhuma credencial é armazenada no
repositório.
