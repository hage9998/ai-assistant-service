from app.application.interfaces.advice_dto import AdviceRequestDTO, AdviceResponseDTO
from app.domain.entities.message import Message, MessageRole

_GENERATION_TRIGGER = (
    "Conceda-me um novo conselho para minha jornada de hoje, ó sábio oráculo."
)


class GenerateAdviceUseCase:
    """ """

    async def execute(self, request: AdviceRequestDTO) -> AdviceResponseDTO:
        messages = [Message(role=MessageRole.USER, content=_GENERATION_TRIGGER)]
