from app.application.interfaces.advice_dto import AdviceRequestDTO, AdviceResponseDTO
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

    async def execute(self, request: AdviceRequestDTO) -> AdviceResponseDTO:
        messages = [Message(role=MessageRole.USER, content=_GENERATION_TRIGGER)]
