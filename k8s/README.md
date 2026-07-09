# Projeto Kubernetes - Life Gamefication

Este projeto contém a configuração necessária para implantar e gerenciar os recursos do aplicativo Life Gamefication no Kubernetes. A estrutura do projeto é organizada em duas pastas principais: `base` e `overlays`.

## Estrutura do Projeto

- **base/**: Contém os recursos Kubernetes básicos que são utilizados em todos os ambientes.
  - `namespace.yaml`: Define o namespace `life-gamefication-dev`.
  - `deployment.yaml`: Configuração do Deployment para gerenciar instâncias do aplicativo.
  - `service.yaml`: Define um Service para expor o Deployment.
  - `configmap.yaml`: Armazena dados de configuração utilizados pelos Pods.
  - `secret.yaml`: Armazena informações sensíveis de forma segura.
  - `kustomization.yaml`: Agrupa e personaliza os recursos da pasta `base`.

- **overlays/**: Contém personalizações específicas para diferentes ambientes (dev, staging, prod).
  - **dev/**: Personalizações para o ambiente de desenvolvimento.
    - `kustomization.yaml`: Referencia os recursos da pasta `base` para o ambiente de desenvolvimento.
    - `patch-deployment.yaml`: Modifica a configuração do Deployment para o ambiente de desenvolvimento.
  - **staging/**: Personalizações para o ambiente de staging.
    - `kustomization.yaml`: Referencia os recursos da pasta `base` para o ambiente de staging.
    - `patch-deployment.yaml`: Modifica a configuração do Deployment para o ambiente de staging.
  - **prod/**: Personalizações para o ambiente de produção.
    - `kustomization.yaml`: Referencia os recursos da pasta `base` para o ambiente de produção.
    - `patch-deployment.yaml`: Modifica a configuração do Deployment para o ambiente de produção.

## Instruções de Implantação

1. **Configuração do Kubernetes**: Certifique-se de que você tem acesso ao seu cluster Kubernetes e que o `kubectl` está configurado corretamente.

2. **Implantação do Namespace**:
   - Execute o comando:
     ```
     kubectl apply -f base/namespace.yaml
     ```

3. **Implantação dos Recursos**:
   - Para implantar os recursos básicos, execute:
     ```
     kubectl apply -k base/
     ```

4. **Implantação em Ambientes Específicos**:
   - Para implantar em um ambiente específico, como desenvolvimento, execute:
     ```
     kubectl apply -k overlays/dev/
     ```

5. **Verificação**: Após a implantação, verifique os recursos criados com:
   ```
   kubectl get all -n life-gamefication-dev
   ```

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests para melhorias e correções.