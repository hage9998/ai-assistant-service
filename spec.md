# Spec: Observabilidade (OTel SDK + sidecar collector) para métricas no Grafana

## Objetivo

Instrumentar o `ai-assistant-service` com OpenTelemetry Python SDK, enviando métricas (e traces) via OTLP para um sidecar OTel Collector no mesmo pod, espelhando exatamente o padrão já usado pelo `auth-service` (NestJS), para que o Prometheus (via `ServiceMonitor`) e o Grafana consigam visualizar as métricas do serviço.

## Contexto

- O pedido original era usar `prometheus-fastapi-instrumentator` (já presente em `requirements.in`/`requirements.txt`, sem uso no código). Após inspecionar o `auth-service`, decidimos seguir o mesmo padrão dele em vez disso: **OpenTelemetry SDK fazendo push OTLP para um sidecar Collector**, não scrape direto de `/metrics` pelo Prometheus. `prometheus-fastapi-instrumentator` será removido do `requirements.in`.
- Referência 1:1 no `auth-service`:
  - `src/infrastructure/observability/instrumentation.ts`: `NodeSDK` com `OTLPTraceExporter` + `OTLPMetricExporter` (`PeriodicExportingMetricReader`, 5s) apontando para `OTEL_EXPORTER_OTLP_ENDPOINT` (default `http://localhost:4317`), `resource` com `service.name`/`service.version` vindos de `OTEL_SERVICE_NAME`/`npm_package_version`, e auto-instrumentations (http, express, pg, redis, nestjs-core).
  - `k8s/base/deployment.yaml`: sidecar `otel-collector` (`otel/opentelemetry-collector-contrib`) montando `otel-collector-sidecar-config` em `/etc/otel`, portas 4317/4318/8889.
  - `k8s/base/otelconfigmap.yaml`: `receiver otlp` (grpc 4317 / http 4318) → `processor batch` → `exporter otlp/jaeger` (traces) e `exporter prometheus` (metrics, `0.0.0.0:8889`).
  - `k8s/base/metricsService.yaml`: `Service` `auth-api-metrics`, seleciona `app: auth-api`, expõe porta `8889` nomeada `metrics`.
  - `k8s/overlays/dev/patch-deployment.yaml`: injeta `OTEL_SERVICE_NAME` e `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317` no container da app.
  - `k8s-infra/observability/prometheus.yaml`: `ServiceMonitor` (`monitoring.coreos.com/v1`) selecionando `app: auth-api`, porta `metrics`, `interval: 15s`, label `release: monitoring` (exigido pelo kube-prometheus-stack Operator).
- No `ai-assistant-service`, os arquivos `k8s/base/otelconfigmap.yaml` e `k8s/base/metricsService.yaml` já existem mas foram copiados do `auth-service` sem adaptar nomes/selectors (ainda dizem `auth-api`), e estão comentados em `k8s/base/kustomization.yaml`. O sidecar no `deployment.yaml` e as env vars `OTEL_*` no overlay `dev` também já estão presentes, comentados, prontos para ativar.
- Não existe `k8s-infra/observability/prometheus.yaml` equivalente para este serviço — é preciso criar um novo `ServiceMonitor` (provavelmente em `k8s-infra/observability/`, mesmo diretório do `auth-api`, para manter o padrão de infra compartilhada).

## Requisitos Funcionais

1. Criar `app/infrastructure/observability/instrumentation.py`, importado como primeira coisa em `app/main.py` (antes de qualquer outro import de app), configurando:
   - `Resource` com `service.name` = `OTEL_SERVICE_NAME` (default `"ai-assistant-api"`) e `service.version` = versão do app (`"1.0.0"`, mesma usada no `FastAPI(version=...)`).
   - `TracerProvider` com `BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_ENDPOINT))`.
   - `MeterProvider` com `PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=...), export_interval_millis=5000)`.
   - `OTEL_EXPORTER_OTLP_ENDPOINT` lido de env var, default `http://localhost:4317` (igual ao Node).
2. Auto-instrumentar com `opentelemetry-instrumentation-fastapi` (aplicado sobre o `app` em `create_app()`) e `opentelemetry-instrumentation-sqlalchemy` (equivalente ao `instrumentation-pg` do Node, instrumenta o `engine` async).
3. Métrica customizada de duração da chamada ao LLM (Ollama): um `Histogram` OTel (`meter.create_histogram("llm_generation_duration_seconds", ...)`) registrado em `OllamaProvider.generate`, com atributo `status` (`success`/`error`).
4. K8s (`ai-assistant-service`):
   - Corrigir `k8s/base/metricsService.yaml`: nome `ai-assistant-api-metrics`, `selector`/`labels` `app: ai-assistant-api`.
   - Descomentar `otelconfigmap.yaml` e `metricsService.yaml` em `k8s/base/kustomization.yaml`.
   - Descomentar o sidecar `otel-collector` e o volume `otel-config` em `k8s/base/deployment.yaml`.
   - Descomentar `OTEL_SERVICE_NAME`/`OTEL_EXPORTER_OTLP_ENDPOINT` em `k8s/overlays/dev/patch-deployment.yaml`, com `OTEL_SERVICE_NAME: "ai-assistant-api"`.
5. Criar `k8s-infra/observability/prometheus-ai-assistant.yaml` (ou nome equivalente): `ServiceMonitor` selecionando `app: ai-assistant-api`, porta `metrics`, `interval: 15s`, label `release: monitoring` — mesmo padrão do `auth-api`.
6. Remover `prometheus-fastapi-instrumentator` de `requirements.in` e recompilar `requirements.txt` via `pip-compile`.

## Requisitos Não Funcionais

- Seguir Clean Architecture: setup de OTel fica em `app/infrastructure/observability/`; a métrica de LLM é registrada dentro de `OllamaProvider` (infra), sem vazar `opentelemetry` para `application`/`domain`.
- Se o Collector sidecar não estiver acessível (ex.: rodando local via `uvicorn --reload` fora do k8s), a app não deve falhar ao subir — exporters OTLP devem falhar silenciosamente/logar erro no envio, não travar o request.
- Nomes de métricas/recursos devem seguir convenção do OpenTelemetry (snake_case, unidade no sufixo, ex. `_seconds`).

## Casos de Uso

- Como operador do cluster, quero que o Prometheus Operator descubra o `ai-assistant-service` automaticamente via `ServiceMonitor`, sem configuração manual.
- Como usuário do Grafana, quero ver no mesmo painel/datasource métricas de HTTP (requests, latência) e de negócio (latência de geração de conselho via LLM) do `ai-assistant-service`, consistente com o que já existe para o `auth-api`.
- Como dev rodando local (`uvicorn --reload`, sem sidecar), quero que a app suba normalmente mesmo sem um Collector disponível em `localhost:4317`.

## Critérios de Aceitação

- Rodando local com o sidecar disponível (ou apontando `OTEL_EXPORTER_OTLP_ENDPOINT` para um collector de teste), requests HTTP e chamadas ao endpoint de advice geram spans e métricas visíveis no Collector/Prometheus.
- `kubectl apply -k k8s/base` sobe o pod com os dois containers (app + otel-collector) e o `Service` de métricas na porta 8889.
- `ServiceMonitor` novo aparece em `kubectl get servicemonitor -n life-gamefication-dev` e o Prometheus lista o target do `ai-assistant-service` como `up`.
- `requirements.txt` não contém mais `prometheus-fastapi-instrumentator`/`prometheus-client`.
- App sobe sem erro mesmo sem Collector acessível (dev local puro).

## Casos Limite

- Falha na chamada ao Ollama (exceção em `GenerateAdviceUseCase`) deve registrar a métrica de duração com `status=error` mesmo quando a exceção é repropagada.
- Ausência do Collector (rede indisponível) não deve derrubar a app nem adicionar latência perceptível às requests (exporters OTLP são assíncronos/batched).

## Fora do Escopo

- Dashboards prontos do Grafana.
- Deploy/configuração do Jaeger (o pipeline de traces já aponta pra ele, mas validar se está rodando não é escopo desta task).
- Alertas/`PrometheusRule`.
- Mudanças no `auth-service` ou em qualquer outro serviço.
- Métricas de infraestrutura do Postgres além do que `opentelemetry-instrumentation-sqlalchemy` oferece de fábrica.
