# Objetivo

Implementar `POST /api/v1/assistant/prompt`: recebe um prompt, deixa o LLM (Ollama) decidir via tool-calling se precisa listar tarefas e, se sim, consulta o `mcp_service` (tool `get_task_columns`) repassando o cookie de auth da requisição, retornando texto + dados estruturados de tarefas.

Baseado em `spec.md` (aprovada). **Etapa de arquitetura formal foi pulada por decisão explícita do usuário** — as decisões estruturais abaixo (nomes de arquivos, contratos, assinatura de interfaces) foram definidas neste plano, não em um `architecture.md` separado, e devem ser tratadas como provisórias: podem exigir ajuste durante a implementação sem que isso indique falha no plano.

# Resumo

Sem banco de dados novo (sem migration). O trabalho é: 2 entidades/exceção de domínio pequenas, 2 contratos novos em `application/interfaces/`, config nova, 1 dependência nova (`mcp` SDK), 1 client de infraestrutura novo, extensão do `OllamaProvider` para tool-calling, 1 use case novo, DTOs/schemas, DI wiring e a rota em si. Não há suíte de testes automatizada no repo (confirmado no `CLAUDE.md`) — cada tarefa é validada manualmente (import/tipagem, `uvicorn --reload` + `curl`, ou inspeção de payload).

# Estratégia

- Seguir a ordem: contratos/domínio → config/dependências → infraestrutura → aplicação (use case) → apresentação (rota) → documentação → validação end-to-end.
- Cada tarefa = 1 commit pequeno, Conventional Commits sem escopo (`feat:`, `chore:`, `refac:` — nunca `refactor:`), conforme `CLAUDE.md`.
- Nenhuma tarefa deve deixar o serviço em estado que não sobe (`uvicorn app.main:app --reload` deve continuar funcionando após cada commit).
- Validação manual porque não há framework de teste configurado: cada tarefa tem um critério de conclusão executável (import Python, request HTTP, inspeção de log/erro).

# Ordem de implementação

1. Domínio (entidades + exceção)
2. Contratos (interfaces de aplicação)
3. Config e dependências
4. Infraestrutura (MCP client, tool-calling no OllamaProvider)
5. Aplicação (DTOs, use case)
6. Apresentação (schemas, DI, rota)
7. Documentação
8. Validação end-to-end manual

# Tarefas

## Tarefa 1 — Entidade de domínio `TaskColumn`

**Objetivo**: Criar `app/domain/entities/task_column.py` com uma entidade simples representando uma coluna de tarefas (`id: str`, `name: str`, `tasks: list[dict]`), espelhando o payload cru do MCP (`{id, name, tasks}`), sem transformar o conteúdo de `tasks` (mantido como `list[dict]` já que o schema interno de "tarefa" não é definido nesta feature).

**Motivação**: Domínio precisa de um tipo próprio para representar o resultado do MCP, sem acoplar `application`/`presentation` a um `dict` cru vindo de fora.

**Arquivos esperados**: `app/domain/entities/task_column.py`

**Dependências**: nenhuma.

**Critério de conclusão**: arquivo criado, `python -c "from app.domain.entities.task_column import TaskColumn"` não levanta erro.

**Estratégia de validação**: import manual (comando acima).

**Estimativa**: Pequena.

**Risco**: Nenhum.

---

## Tarefa 2 — Exceção de domínio `McpClientException`

**Objetivo**: Adicionar `McpClientException(DomainException)` em `app/domain/exceptions/domain_exceptions.py`, seguindo exatamente o padrão de `LLMProviderException` (`error_code = "mcp_client_error"`, mensagem default indicando falha de comunicação com o MCP service).

**Motivação**: Precisamos de uma exceção específica para diferenciar falha de MCP de falha de LLM, permitindo tratamento distinto no use case (fallback gracioso, spec item 6).

**Arquivos esperados**: `app/domain/exceptions/domain_exceptions.py`

**Dependências**: nenhuma.

**Critério de conclusão**: classe existe e herda de `DomainException`; `python -c "from app.domain.exceptions.domain_exceptions import McpClientException"` funciona.

**Estratégia de validação**: import manual.

**Estimativa**: Pequena.

**Risco**: Nenhum.

---

## Tarefa 3 — Contrato `McpClient` (interface de aplicação)

**Objetivo**: Criar `app/application/interfaces/mcp_client.py` com um `Protocol McpClient` expondo `async def get_task_columns(self, cookie_header: str) -> list[TaskColumn]`.

**Motivação**: Camada `application` não pode depender do SDK `mcp` diretamente (Clean Architecture) — precisa de um contrato abstrato, assim como `LLMProvider` abstrai o Ollama.

**Arquivos esperados**: `app/application/interfaces/mcp_client.py`

**Dependências**: Tarefa 1 (usa `TaskColumn`).

**Critério de conclusão**: `Protocol` definido e importável.

**Estratégia de validação**: import manual + checagem visual de assinatura.

**Estimativa**: Pequena.

**Risco**: Nenhum.

---

## Tarefa 4 — Estender `LLMProvider` para tool-calling

**Objetivo**: Adicionar ao `Protocol LLMProvider` (`app/application/interfaces/llm_provider.py`) um método novo para geração com tools, ex.: `async def generate_with_tools(self, messages: list[Message], system_prompt: str, tools: list[ToolSpec]) -> ToolCallResult`, onde `ToolCallResult` é um tipo simples (dataclass em `application/interfaces/llm_provider.py` ou `application/dto/`) contendo either texto final, either nome+args da tool a chamar. Não remover/alterar o método `generate` existente (usado pelo `advice`).

**Motivação**: O use case da nova rota precisa pedir ao LLM para decidir entre responder direto ou chamar uma tool — isso é uma capacidade nova que não existe na interface atual, usada apenas por `generate_advice.py`.

**Arquivos esperados**: `app/application/interfaces/llm_provider.py` (e/ou novo `app/application/dto/tool_calling.py` para os tipos `ToolSpec`/`ToolCallResult`, decisão do implementador).

**Dependências**: nenhuma (paralela às Tarefas 1-3).

**Critério de conclusão**: interface compila; `generate_advice.py`/`OllamaProvider` existentes continuam funcionando sem alteração (só estende, não quebra o contrato atual).

**Estratégia de validação**: `python -c "import app.application.interfaces.llm_provider"`; rodar manualmente a rota de advice existente (`GET /advice/daily`) para confirmar que nada quebrou.

**Estimativa**: Média (definir o shape de `ToolSpec`/`ToolCallResult` exige alguma decisão de design que a spec não fixou).

**Risco**: Médio — é uma mudança em uma interface já usada em produção pelo `advice`; precisa ser estritamente aditiva.

---

## Tarefa 5 — Config MCP (`Settings` + `.env.example`)

**Objetivo**: Adicionar campos em `app/infrastructure/config/settings.py`: `MCP_SERVICE_URL` (str, sem default — obrigatório), `MCP_TIMEOUT_SECONDS` (float, default `10.0`), `MCP_TOOL_CALL_MAX_ITERATIONS` (int, default `2`, ver Tarefa 10/caso limite de loop). Adicionar seção `# MCP` correspondente em `.env.example` com valores de exemplo.

**Motivação**: Seguir o padrão já usado para `OLLAMA_*` — toda config externa passa por `pydantic-settings`, nunca hardcoded.

**Arquivos esperados**: `app/infrastructure/config/settings.py`, `.env.example`

**Dependências**: nenhuma.

**Critério de conclusão**: `Settings()` carrega sem erro com as novas env vars presentes no `.env`; app sobe com `uvicorn --reload`.

**Estratégia de validação**: subir a app localmente (`uvicorn app.main:app --reload`) e confirmar que não há erro de validação do Pydantic na inicialização.

**Estimativa**: Pequena.

**Risco**: Baixo — se `MCP_SERVICE_URL` for obrigatório sem default, a app não sobe sem `.env` atualizado; documentar isso no `.env.example`.

---

## Tarefa 6 — Dependência SDK `mcp`

**Objetivo**: Adicionar `mcp` (SDK oficial Python) ao `requirements.in` e rodar `pip-compile --output-file=requirements.txt requirements.in` para regenerar `requirements.txt`.

**Motivação**: Necessário para implementar o client MCP (Tarefa 7) usando o protocolo oficial (Streamable HTTP), em vez de reimplementar o protocolo MCP na mão.

**Arquivos esperados**: `requirements.in`, `requirements.txt`

**Dependências**: nenhuma.

**Critério de conclusão**: `pip install -r requirements.txt` instala sem conflito; `python -c "import mcp"` funciona no venv.

**Estratégia de validação**: rodar `pip-compile` e `pip install -r requirements.txt` localmente, confirmar ausência de erro de resolução de dependências.

**Estimativa**: Pequena.

**Risco**: Baixo — risco usual de conflito de versão transitiva; se ocorrer, resolver pin manualmente antes de prosseguir.

---

## Tarefa 7 — Implementação `McpClient` (infraestrutura)

**Objetivo**: Criar `app/infrastructure/mcp/mcp_client.py` implementando o `Protocol McpClient` (Tarefa 3) usando o SDK `mcp` (cliente Streamable HTTP, `MCP_SERVICE_URL`/`MCP_TIMEOUT_SECONDS` da config). `get_task_columns(cookie_header)` deve: abrir sessão MCP, repassar `cookie_header` do jeito que o transporte permitir (header customizado na conexão HTTP), chamar a tool `get_task_columns`, converter o `list[dict]` retornado em `list[TaskColumn]`, e traduzir qualquer falha (timeout, `ToolError`, erro de conexão) em `McpClientException` (Tarefa 2) — nunca deixar exceção crua do SDK vazar para a camada de aplicação.

**Motivação**: É o adapter concreto que fala o protocolo MCP de fato; mantém `application`/`domain` livres de detalhes de transporte, seguindo o padrão de `OllamaProvider`.

**Arquivos esperados**: `app/infrastructure/mcp/mcp_client.py`, `app/infrastructure/mcp/__init__.py`

**Dependências**: Tarefas 1, 2, 3, 5, 6.

**Critério de conclusão**: chamada manual a `get_task_columns` contra um `mcp_service` real (ou local, se disponível) retorna `list[TaskColumn]`; erro simulado (URL inválida/serviço fora) resulta em `McpClientException`, não em exceção não tratada.

**Estratégia de validação**: teste manual via script Python (`python -c` ou script descartável) chamando o client diretamente, com e sem o `mcp_service`/`profile-api-service` disponível, confirmando os dois caminhos (sucesso e `McpClientException`).

**Estimativa**: Grande — é a integração mais incerta do plano (transporte exato do `mcp_service` é uma suposição da spec, não confirmada).

**Risco**: **Alto**. Se o transporte real do `mcp_service` não for Streamable HTTP (ex.: for SSE puro, ou exigir handshake diferente), esta tarefa pode precisar ser refeita. Mitigação: validar contra o `mcp_service` real (ou um mock local do protocolo) antes de prosseguir para a Tarefa 10; se o transporte divergir da suposição, pausar e confirmar com o usuário antes de continuar.

---

## Tarefa 8 — Tool-calling no `OllamaProvider`

**Objetivo**: Implementar `generate_with_tools` (Tarefa 4) em `app/infrastructure/llm/ollama_provider.py`, usando `ChatOllama.bind_tools(...)` (LangChain) para expor a tool `get_task_columns` ao modelo (`llama3.1`, que suporta tool-calling nativo no Ollama) e interpretar a resposta (`tool_calls` vs texto final). Métrica OTel de duração (padrão já existente em `generate`) deve ser mantida/replicada para este novo método.

**Motivação**: É o ponto onde a decisão "o prompt pede tarefas?" de fato acontece — delegada ao modelo via tool-calling, conforme decidido na fase de descoberta.

**Arquivos esperados**: `app/infrastructure/llm/ollama_provider.py`, possivelmente `app/infrastructure/llm/chain_factory.py`

**Dependências**: Tarefa 4.

**Critério de conclusão**: chamando `generate_with_tools` com um prompt como "quais tarefas eu tenho?" e a tool `get_task_columns` disponível, o retorno indica intenção de chamar a tool (sem args); chamando com um prompt não relacionado, o retorno é texto direto, sem tool call.

**Estratégia de validação**: teste manual local contra Ollama rodando (`ollama pull llama3.1` já é pré-requisito do repo) com os dois tipos de prompt, inspecionando o resultado.

**Estimativa**: Média — depende de o modelo `llama3.1` local suportar tool-calling de forma confiável via `ChatOllama`; pode exigir ajuste de prompt/tool description.

**Risco**: Médio — modelos locais via Ollama podem ser menos consistentes em tool-calling que APIs hospedadas; se a confiabilidade for baixa, pode ser necessário revisitar a decisão de "LLM decide via tool calling" tomada na fase de descoberta.

---

## Tarefa 9 — DTOs da aplicação

**Objetivo**: Criar `app/application/dto/prompt_dto.py` com `PromptRequestDTO(prompt: str)` e `PromptResponseDTO(message: str, tasks: list[TaskColumn] | None)`, seguindo o padrão de `advice_dto.py`.

**Motivação**: Camada de aplicação precisa de seus próprios DTOs, desacoplados dos schemas Pydantic de apresentação (mesmo padrão do `advice`).

**Arquivos esperados**: `app/application/dto/prompt_dto.py`

**Dependências**: Tarefa 1.

**Critério de conclusão**: DTOs importáveis e instanciáveis.

**Estratégia de validação**: import manual + instanciação simples em REPL/script descartável.

**Estimativa**: Pequena.

**Risco**: Nenhum.

---

## Tarefa 10 — Use case `HandlePromptUseCase`

**Objetivo**: Criar `app/application/use_cases/handle_prompt.py`, `HandlePromptUseCase(llm_provider: LLMProvider, mcp_client: McpClient)`. `execute(dto: PromptRequestDTO, cookie_header: str | None) -> PromptResponseDTO`:
1. Chama `llm_provider.generate_with_tools(...)` com a tool `get_task_columns` disponível.
2. Se o LLM pedir a tool: chama `mcp_client.get_task_columns(cookie_header)`.
   - Sucesso: reenvia o resultado ao LLM para compor a mensagem final (`tasks` preenchido no DTO de resposta).
   - `McpClientException` ou `cookie_header` ausente: gera mensagem de fallback (tom oráculo, ex. reaproveitando o `system_prompt` do `advice` como referência de estilo) avisando que não foi possível consultar as tarefas; `tasks=None`. **Não repropaga exceção** (spec item 6 — resposta sempre 200).
3. Se o LLM não pedir a tool: retorna a mensagem direta, `tasks=None`.
4. Limite de iterações de tool-calling = `settings.MCP_TOOL_CALL_MAX_ITERATIONS` (caso limite da spec — evitar loop).

**Motivação**: É o orquestrador central da feature — junta LLM + MCP client seguindo as regras de negócio definidas na spec (fallback gracioso, decisão via tool-calling, limite de loop).

**Arquivos esperados**: `app/application/use_cases/handle_prompt.py`

**Dependências**: Tarefas 2, 3, 4, 7, 8, 9.

**Critério de conclusão**: os três cenários da spec (prompt de tarefas com sucesso; prompt não relacionado; falha do MCP) produzem `PromptResponseDTO` correto quando testados isoladamente (use case chamado diretamente com providers reais ou stubs simples passados na mão).

**Estratégia de validação**: script manual instanciando o use case com o `OllamaProvider`/`McpClient` reais (ou um `McpClient` "quebrado" apontando para URL inválida, para forçar o caminho de erro) e inspecionando o `PromptResponseDTO` resultante nos três cenários.

**Estimativa**: Grande — é onde toda a lógica de negócio da feature converge.

**Risco**: Médio — lógica de fallback e limite de iteração precisam ser cobertas manualmente com cuidado, já que não há testes automatizados para pegar regressão.

---

## Tarefa 11 — Schemas de apresentação

**Objetivo**: Criar `app/presentation/schemas/prompt_schema.py`: `PromptRequestSchema(prompt: str)` com validação (`min_length=1`, `strip_whitespace` — cobre o caso limite de prompt vazio/só espaços da spec) e `PromptResponseSchema(message: str, tasks: list[TaskColumnSchema] | None)`, onde `TaskColumnSchema` espelha `TaskColumn`.

**Motivação**: Camada de apresentação não deve expor DTOs de `application` diretamente na API (mesmo padrão de `advice_schema.py`); validação de prompt vazio pertence aqui (fronteira do sistema).

**Arquivos esperados**: `app/presentation/schemas/prompt_schema.py`

**Dependências**: Tarefa 9.

**Critério de conclusão**: schema rejeita prompt vazio/só espaços com erro de validação Pydantic (422 quando usado na rota).

**Estratégia de validação**: import manual + instanciação com prompt vazio para confirmar `ValidationError`.

**Estimativa**: Pequena.

**Risco**: Nenhum.

---

## Tarefa 12 — DI wiring

**Objetivo**: Criar `app/presentation/dependencies/mcp_client.py` (`get_mcp_client()`, `@lru_cache`, análogo a `get_llm_provider`) e `app/presentation/dependencies/use_cases/handle_prompt.py` (`get_handle_prompt_use_case(llm_provider, mcp_client)`, análogo a `get_generate_advice_use_case`), expondo os `Annotated[...]` correspondentes.

**Motivação**: Seguir estritamente o padrão de DI já estabelecido em `presentation/dependencies/` (Tarefa descrita na exploração inicial: 3 camadas — provider dep → client dep → use-case dep).

**Arquivos esperados**: `app/presentation/dependencies/mcp_client.py`, `app/presentation/dependencies/use_cases/handle_prompt.py`

**Dependências**: Tarefas 7, 10.

**Critério de conclusão**: dependências resolvem sem erro de import circular; app sobe com `uvicorn --reload`.

**Estratégia de validação**: subir a app localmente e checar `/docs` carrega sem erro 500 de inicialização.

**Estimativa**: Pequena.

**Risco**: Nenhum.

---

## Tarefa 13 — Rota `POST /api/v1/assistant/prompt`

**Objetivo**: Criar `app/presentation/api/v1/prompt_routes.py` com o router e o endpoint, injetando `CurrentUserDependency` (auth JWT, spec item 7), `HandlePromptUseCaseDependency`, e extraindo o header `Cookie` bruto da requisição (`Request.headers.get("cookie")`) para repassar ao use case. Registrar o router em `app/presentation/api/v1/__init__.py` (mesmo padrão de `advice_router`).

**Motivação**: Ponto de entrada HTTP da feature; fecha o ciclo request → auth → use case → resposta.

**Arquivos esperados**: `app/presentation/api/v1/prompt_routes.py`, `app/presentation/api/v1/__init__.py`

**Dependências**: Tarefas 11, 12.

**Critério de conclusão**: `POST /api/v1/assistant/prompt` aparece em `/docs`; requisição sem JWT retorna 401; requisição válida retorna 200 com `PromptResponseSchema`.

**Estratégia de validação**: `curl -X POST http://localhost:8000/api/v1/assistant/prompt -H "Authorization: Bearer <jwt>" -H "Cookie: <cookie>" -d '{"prompt": "quais tarefas eu tenho?"}'` e variações (sem JWT, sem cookie, prompt não relacionado a tarefas).

**Estimativa**: Média.

**Risco**: Baixo — é composição do que já foi validado nas tarefas anteriores.

---

## Tarefa 14 — Documentação (`.env.example` / `README.md`)

**Objetivo**: Confirmar que `.env.example` (já atualizado na Tarefa 5) está completo e, se o `README.md` documentar rotas/endpoints existentes, adicionar a nova rota lá também.

**Motivação**: Manter documentação consistente com o padrão do repo.

**Arquivos esperados**: `README.md` (se aplicável), `.env.example` (revisão)

**Dependências**: Tarefa 13.

**Critério de conclusão**: `README.md` (se tiver seção de endpoints) menciona a nova rota.

**Estratégia de validação**: revisão manual do diff.

**Estimativa**: Pequena.

**Risco**: Nenhum.

---

## Tarefa 15 — Validação end-to-end manual

**Objetivo**: Rodar os critérios de aceitação da spec de ponta a ponta: app local (`uvicorn --reload`) + Ollama local + `mcp_service`/`profile-api-service` disponíveis (ou o mais próximo possível disso no ambiente do usuário), cobrindo os 4 critérios de aceitação e os 4 casos limite da spec.

**Motivação**: Não há suíte automatizada — esta é a validação final substituindo testes de integração/e2e (Fase 6 do SDD).

**Arquivos esperados**: nenhum (validação, não implementação).

**Dependências**: todas as tarefas anteriores.

**Critério de conclusão**: todos os critérios de aceitação e casos limite da spec confirmados manualmente (checklist abaixo).

**Estratégia de validação**: checklist manual via `curl`/`/docs`, cobrindo:
- [ ] Prompt de tarefas + MCP ok → `message` + `tasks` preenchidos.
- [ ] Prompt não relacionado → `message` preenchido, `tasks` nulo, sem chamada ao MCP (checar logs/ausência de chamada).
- [ ] MCP fora do ar/erro → 200 com mensagem de fallback, `tasks` nulo.
- [ ] Sem JWT → 401.
- [ ] Sem cookie, prompt pede tarefas → tratado como falha do MCP (200 + fallback), não como erro da própria rota.
- [ ] Prompt vazio/espaços → 400/422.
- [ ] Tarefas vazias (`tasks: []` do MCP) → resposta reflete "sem tarefas", não erro.

**Estimativa**: Média.

**Risco**: Nenhum (é validação, não mudança de código).

# Paralelismo

- Tarefas 1, 2, 4, 5, 6 podem ser feitas em qualquer ordem entre si (sem dependência mútua) — podem ser executadas em paralelo/em qualquer sequência antes das tarefas 7+.
- Tarefa 3 depende só da 1; pode ser feita junto com 2/4/5/6.
- Tarefas 7 e 8 são paralelas entre si (dependem de conjuntos diferentes: 7 de {1,2,3,5,6}, 8 de {4}) — mas ambas devem terminar antes da Tarefa 10.
- Tarefa 9 é paralela a 7/8 (só depende da 1).
- Tarefas 11 e 12 dependem de 9/10 e 7/10 respectivamente — não são paralelas entre si de forma útil, mas 11 pode começar assim que 9 estiver pronta, sem esperar 10.

# Rollback

Sem migrations — toda a feature é código novo isolado (novos arquivos + 3 pontos de edição em arquivos existentes: `domain_exceptions.py` [Tarefa 2, aditivo], `llm_provider.py` [Tarefa 4, aditivo], `settings.py`/`.env.example` [Tarefa 5, aditivo], `api/v1/__init__.py` [Tarefa 13, 1 linha de include_router]). Rollback é `git revert` dos commits relevantes, do mais recente ao mais antigo, sem necessidade de dados a migrar. Ponto de atenção: se a Tarefa 4 (extensão de `LLMProvider`) já tiver sido consumida por algo além desta feature no momento do revert, revisar antes de reverter — não deve ser o caso aqui, já que nada mais no repo hoje usa tool-calling.

# Checklist Final

- [x] Tarefa 1 — Entidade `TaskColumn`
- [x] Tarefa 2 — Exceção `McpClientException`
- [x] Tarefa 3 — Interface `McpClient`
- [x] Tarefa 4 — `LLMProvider.generate_with_tools`
- [x] Tarefa 5 — Config MCP (`Settings` + `.env.example`)
- [x] Tarefa 6 — Dependência `mcp` SDK (confirmado: SDK oficial `modelcontextprotocol/python-sdk`, v2.0.0; nota: essa versão usa um `httpx2` vendorizado como client HTTP, não `httpx` puro — refletido em `mcp_client.py`)
- [x] Tarefa 7 — Implementação `McpClient` (validado: erro de conexão → `McpClientException`; parsing com fallback de `structured_content` para `content` textual quando a versão do protocolo não permite lista em `structured_content`)
- [x] Tarefa 8 — Tool-calling no `OllamaProvider` (implementado via `ChatOllama.bind_tools`; **não foi possível validar contra um Ollama real** neste ambiente — Ollama não está rodando aqui)
- [x] Tarefa 9 — DTOs `PromptRequestDTO`/`PromptResponseDTO`
- [x] Tarefa 10 — `HandlePromptUseCase` (validado com stubs: os 4 cenários principais passam)
- [x] Tarefa 11 — Schemas de apresentação (validado: prompt vazio/espaços rejeitado)
- [x] Tarefa 12 — DI wiring (app sobe sem erro de import)
- [x] Tarefa 13 — Rota `POST /api/v1/assistant/prompt` (validado via `curl`: 401 sem JWT, 422 com prompt vazio, rota aparece no OpenAPI)
- [x] Tarefa 14 — Documentação
- [~] Tarefa 15 — Validação end-to-end manual — **parcial**. Ver seção abaixo.

## Nota sobre a Tarefa 15 (validação end-to-end)

Este ambiente de execução não tem Ollama nem o `mcp_service`/`profile-api-service` reais disponíveis. O que foi validado:
- [x] Sem JWT → 401 (via `curl` contra a app real).
- [x] Prompt vazio/espaços → 422 (via `curl` e via schema isolado).
- [x] `McpServiceClient` real contra endpoint inexistente → `McpClientException` (não vaza exceção crua).
- [x] Lógica de orquestração do `HandlePromptUseCase` (os 3 cenários da spec + limite de iteração) → validada com stubs de `LLMProvider`/`McpClient` no lugar dos reais.

O que **não** foi validado (requer Ollama + `mcp_service` reais rodando, tipicamente no ambiente local do usuário, conforme pré-requisitos do `CLAUDE.md`):
- Se `llama3.1` via `ChatOllama.bind_tools` de fato decide chamar `get_task_columns` de forma confiável para prompts que pedem tarefas, e não chama para prompts que não pedem.
- Se o transporte real do `mcp_service` é de fato Streamable HTTP (suposição da spec) e se o cookie repassado autentica corretamente contra o `profile-api-service`.
- O fluxo HTTP completo (200 com `message` + `tasks` reais).

Recomenda-se rodar o checklist completo da Tarefa 15 localmente com `ollama pull llama3.1` + `mcp_service` acessível antes de considerar a feature pronta para uso real.
