import json
import logging

from app.application.dto.prompt_dto import PromptRequestDTO, PromptResponseDTO
from app.application.dto.tool_calling import ToolSpec
from app.application.interfaces.llm_provider import LLMProvider
from app.application.interfaces.mcp_client import McpClient
from app.domain.entities.message import Message, MessageRole
from app.domain.entities.task_column import TaskColumn
from app.domain.exceptions.domain_exceptions import LLMProviderException, McpClientException

logger = logging.getLogger(__name__)

_GET_TASK_COLUMNS_TOOL = "get_task_columns"

PROMPT_ASSISTANT_SYSTEM_PROMPT = """\
Você é um sábio oráculo de um reino medieval fantástico, guardião de \
lendas sobre cavaleiros, magos, dragões, reis e guerreiros, que auxilia \
um(a) aventureiro(a) em sua jornada em uma plataforma de gamificação da \
vida real (hábitos, metas e missões).

Regras que você DEVE seguir rigorosamente:
1. Quando o aventureiro pedir para ver, listar ou saber quais/quantas \
são suas tarefas ou missões pendentes, chame a ferramenta \
`get_task_columns` para consultar o grimório de missões antes de \
responder. Nunca invente tarefas.
2. Para qualquer outro pedido, responda diretamente, sem usar a \
ferramenta.
3. Escreva no máximo 3 ou 4 frases, em tom épico, medieval e mítico.
4. Não use formatação markdown, apenas texto corrido.
"""

_TASK_COLUMNS_TOOL_SPEC = ToolSpec(
    name=_GET_TASK_COLUMNS_TOOL,
    description=(
        "Consulta o grimório de missões do aventureiro e retorna suas "
        "colunas de tarefas pendentes. Use quando o aventureiro pedir para "
        "ver, listar, saber quantas ou quais são suas tarefas/missões."
    ),
)

_TASKS_UNAVAILABLE_FALLBACK = (
    "Peço perdão, nobre aventureiro, mas as brumas encobriram meu grimório "
    "de missões neste instante e não consigo enxergar suas tarefas. "
    "Tente novamente em breve, pois vossa jornada continua digna de "
    "atenção."
)

_TOOL_LOOP_EXCEEDED_FALLBACK = (
    "Peço perdão, aventureiro, mas minha visão se turvou ao tentar "
    "decifrar vosso pedido. Reformulai vossa pergunta e eu tentarei "
    "novamente vos guiar."
)


class HandlePromptUseCase:
    """Orchestrates answering a free-form prompt, calling the MCP service
    to list tasks when the LLM decides it's needed.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        mcp_client: McpClient,
        max_tool_iterations: int = 2,
    ) -> None:
        self._llm_provider = llm_provider
        self._mcp_client = mcp_client
        self._max_tool_iterations = max_tool_iterations

    async def execute(
        self, request: PromptRequestDTO, cookie_header: str | None
    ) -> PromptResponseDTO:
        messages: list[Message] = [
            Message(role=MessageRole.USER, content=request.prompt)
        ]
        tasks: list[TaskColumn] | None = None

        for _ in range(self._max_tool_iterations):
            try:
                result = await self._llm_provider.generate_with_tools(
                    messages=messages,
                    system_prompt=PROMPT_ASSISTANT_SYSTEM_PROMPT,
                    tools=[_TASK_COLUMNS_TOOL_SPEC],
                )
            except Exception as e:
                logger.exception("Failed to generate assistant response")
                raise LLMProviderException("Error generating assistant response") from e

            if not result.requires_tool_call:
                return PromptResponseDTO(message=result.text.strip(), tasks=tasks)

            if not cookie_header:
                logger.warning("Task listing requested but no cookie header is present")
                return PromptResponseDTO(message=_TASKS_UNAVAILABLE_FALLBACK, tasks=None)

            try:
                tasks = await self._mcp_client.get_task_columns(cookie_header)
            except McpClientException:
                logger.exception("Failed to fetch task columns from MCP service")
                return PromptResponseDTO(message=_TASKS_UNAVAILABLE_FALLBACK, tasks=None)

            messages.append(
                Message(
                    role=MessageRole.USER,
                    content=(
                        "Resultado da consulta ao grimório de missões (JSON): "
                        f"{json.dumps([column.__dict__ for column in tasks])}\n\n"
                        "Componha a resposta final para o aventureiro com base "
                        "nesses dados, seguindo as regras do seu papel."
                    ),
                )
            )

        return PromptResponseDTO(message=_TOOL_LOOP_EXCEEDED_FALLBACK, tasks=tasks)
