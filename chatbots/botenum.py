from enum import Enum


class BotFlowEnum(Enum):
    QUAL_CARDAPIO = 'Qual o cardápio?'
    AVALIAR_REFEICAO = 'Avaliar refeição'
    RECEBER_NOTIFICACAO = 'Receber notificações'
    CANCELAR_NOTIFICACAO = 'Cancelar notificações'
    NENHUM = 'Nenhum'

    STEP_INITIAL = 1
