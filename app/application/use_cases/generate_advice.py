from app.application.interfaces.advice_dto import AdviceRequestDTO, AdviceResponseDTO
from app.application.interfaces.llm_provider import LLMProvider
from app.domain.entities.advice_log import AdviceLog
from app.domain.entities.message import Message, MessageRole

_GENERATION_TRIGGER = (
    "Conceda-me um novo conselho para minha jornada de hoje, ó sábio oráculo."
)

MEDIEVAL_ADVICE_SYSTEM_PROMPT = """\
Você é um sábio oráculo de um reino medieval fantástico, guardião de \
lendas sobre cavaleiros, magos, dragões, reis e guerreiros. Sua missão \
é entregar, a cada chamado, um único conselho curto para um(a) \
aventureiro(a) que está prestes a continuar sua jornada em uma \
plataforma de gamificação da vida real (hábitos, metas e missões).

Regras que você DEVE seguir rigorosamente:
1. Escreva no máximo 3 ou 4 frases.
2. Use um tom épico, medieval e mítico (referências a espadas, \
batalhas, dragões, reinos, magia, honra, jornadas).
3. O conselho deve transmitir motivação para continuar a jornada de \
desenvolvimento pessoal do usuário, mesmo sem citar tarefas específicas.
4. Não use formatação markdown, apenas texto corrido.
5. Nunca repita literalmente conselhos anteriores; seja sempre original.
"""


class GenerateAdviceUseCase:
    """ """

    def __init__(
        self, llm_provider: LLMProvider, advice_log_repository: AdviceLogRepository
    ) -> None:
        self._llm_provider = llm_provider
        self._advice_log = advice_log

    async def execute(self, request: AdviceRequestDTO) -> AdviceResponseDTO:
        messages = [Message(role=MessageRole.USER, content=_GENERATION_TRIGGER)]

        advice = await self._llm_provider.generate(
            messages=messages,
            system_prompt=MEDIEVAL_ADVICE_SYSTEM_PROMPT,
        )

        normalizedAdvice = advice.strip()

        advice_log = AdviceLog(user_id=request.user_id, advice=normalizedAdvice)

        # return AdviceResponseDTO(message=advice)
