# Spec: Rota de prompt com listagem de tarefas via MCP service

## Objetivo

Criar uma nova rota HTTP que recebe um prompt em linguagem natural do usuário e, quando o prompt pedir ou exigir a listagem de tarefas, o serviço consulta um MCP service externo (já existente) para obter essa lista antes de responder.

## Contexto

- Sistema poliglota: este serviço (`ai-assistant-service`, FastAPI) já se comunica com um backend NestJS (JWT compartilhado). Existe também um `mcp_service` (fora deste repositório) que expõe, via **FastMCP**, a tool `get_task_columns`.
- `get_task_columns`:
  - Não recebe parâmetros explícitos no schema MCP — só o `ctx: Context` injetado pelo FastMCP.
  - Autentica repassando o header `Cookie` da requisição de entrada (`get_cookie_header(ctx)`) para o `profile-api-service`, chamando `GET /profile/task/columns`.
  - Retorna `list[dict]`, cada item no formato `{ "id": ..., "name": ..., "tasks": [...] }`.
  - Levanta `ToolError` se não houver cookie de auth ou se o `profile-api-service` responder 401/403.
- Hoje **não existe nenhuma integração MCP neste repositório** — nem código, nem dependência (`mcp`/`langchain-mcp-adapters`), nem config. É uma integração greenfield.
- Também não existe hoje nenhum client HTTP direto (`httpx`) usado em `app/infrastructure/` — o cliente MCP será o primeiro caso.
- A decisão de "o prompt pede/precisa listar tarefas" será feita via **tool calling do LLM** (o modelo Ollama, já usado para o `advice`, decide se deve chamar a tool `get_task_columns`), não por uma heurística/classificador separado.
- A rota é **nova e independente** da rota de advice existente (`GET /advice/daily`); não altera o fluxo atual de `GenerateAdviceUseCase`.

### Suposições a validar (assumptions)

Estes pontos não foram confirmados com certeza total e devem ser validados na fase de arquitetura/implementação:

1. **Transporte MCP**: o `mcp_service` expõe HTTP (Streamable HTTP ou SSE, padrão FastMCP moderno). Vamos assumir **Streamable HTTP** via SDK oficial `mcp` (Python), configurável por env var (`MCP_SERVICE_URL`), com endpoint/porta a confirmar.
2. **Repasse de auth**: o cliente desta rota deve enviar tanto o JWT Bearer (auth deste serviço) quanto o cookie de sessão do `profile-api-service` na mesma requisição; a rota extrai o `Cookie` do request recebido e repassa como header `Cookie` na chamada MCP. Não há troca/derivação de credencial — é passthrough puro.
3. Nome exato da env var de URL do MCP service e se há autenticação adicional entre `ai-assistant-service` e `mcp_service` (ex.: mTLS, API key de serviço) — a assumir como "não há" por enquanto (mesma rede interna do cluster).

## Requisitos Funcionais

1. Nova rota `POST /api/v1/assistant/prompt` (nome definitivo a confirmar no plano), recebendo `{ "prompt": string }`.
2. O serviço envia o prompt ao LLM (Ollama) com a tool `get_task_columns` disponível para tool-calling.
3. Se o LLM decidir chamar a tool (porque o prompt pede/requer listar tarefas):
   a. O serviço chama o `mcp_service` (tool `get_task_columns`), repassando o cookie de auth da requisição recebida.
   b. O resultado (colunas + tarefas) é devolvido ao LLM para compor a resposta final em linguagem natural.
4. Se o LLM não chamar a tool, a rota responde normalmente sem tocar no MCP service.
5. A resposta da rota inclui:
   - `message`: texto em linguagem natural (mesmo tom oráculo medieval do `advice`, ver `generate_advice.py`).
   - `tasks`: dado estruturado das colunas/tarefas retornadas pelo MCP, quando a tool tiver sido chamada com sucesso; `null`/ausente quando não aplicável.
6. Se a chamada ao MCP falhar (timeout, `ToolError`, 401/403, serviço indisponível), a rota **não retorna erro HTTP** — responde `200` com uma mensagem (tom oráculo) avisando que não foi possível consultar as tarefas no momento, e `tasks: null`.
7. A rota exige autenticação JWT, seguindo o mesmo padrão das demais rotas do serviço (`CurrentUserDependency`).

## Requisitos Não Funcionais

- Seguir Clean Architecture: contrato do cliente MCP definido em `application/interfaces/` (ex.: `McpClient` Protocol); implementação concreta em `app/infrastructure/mcp/`, espelhando o padrão de `app/infrastructure/llm/`.
- Nova exceção de domínio (`app/domain/exceptions/domain_exceptions.py`) para falha de comunicação com o MCP service, seguindo o padrão de `LLMProviderException`.
- Timeout configurável na chamada ao MCP service (não travar a rota indefinidamente se o `mcp_service`/`profile-api-service` ficar lento).
- Nova(s) dependência(s) adicionada(s) via `requirements.in` + `pip-compile` (ex.: SDK oficial `mcp`), nunca editando `requirements.txt` à mão.
- Config nova via `pydantic-settings` (`app/infrastructure/config/settings.py`) e documentada em `.env.example`, seguindo o padrão das seções existentes (`# LLM / Ollama`).

## Casos de Uso

- Como usuário, envio um prompt como "quais tarefas eu tenho pra hoje?" e recebo uma resposta em tom de oráculo junto com a lista real das minhas tarefas.
- Como usuário, envio um prompt que não tem relação com tarefas (ex.: "me dê uma frase de motivação") e recebo resposta normal do LLM, sem chamada ao MCP.
- Como usuário, envio um prompt pedindo tarefas mas minha sessão com o `profile-api-service` expirou (sem cookie válido) — recebo uma resposta educada dizendo que não consegui consultar as tarefas agora, sem erro 500.

## Critérios de Aceitação

- `POST /api/v1/assistant/prompt` com prompt relacionado a tarefas retorna `message` (texto) e `tasks` (lista de colunas) preenchidos, refletindo o retorno real do MCP service.
- `POST /api/v1/assistant/prompt` com prompt não relacionado a tarefas retorna `message` preenchido e `tasks` nulo/ausente, sem nenhuma chamada ao MCP service.
- Falha do MCP service (mockável em teste) resulta em resposta `200` com mensagem de fallback, nunca em erro 500 vazando para o cliente.
- Rota protegida por JWT: requisição sem token válido retorna 401, igual às demais rotas.
- `requirements.txt` atualizado via `pip-compile` contendo a(s) nova(s) dependência(s) MCP.

## Casos Limite

- Cookie de auth ausente na requisição de entrada, mas o prompt pede tarefas → tratado como falha do MCP (item 6 dos Requisitos Funcionais), não como erro de autenticação da própria rota.
- LLM tenta chamar a tool mais de uma vez na mesma conversa (loop) → deve haver um limite de iterações de tool-calling para evitar loop infinito.
- MCP retorna lista vazia de colunas (usuário sem tarefas) → `tasks: []`, mensagem deve refletir que não há tarefas, não deve ser tratado como erro.
- Prompt vazio ou só espaços → validação de request (400), sem chamar LLM nem MCP.

## Fora do Escopo

- Criação/edição/conclusão de tarefas (somente listagem, via `get_task_columns`).
- Qualquer mudança no `mcp_service` ou no `profile-api-service` (são consumidos como estão).
- Alterar o fluxo/rota de `advice` existente.
- Autenticação mTLS ou API key de serviço entre `ai-assistant-service` e `mcp_service` (assume-se rede interna confiável do cluster, a revisitar se necessário).
- Cache de resultados do MCP service.
- Suporte a outras tools MCP além de `get_task_columns`.
