from api_client import PratoAbertoApiClient


class BaseBot(object):
    """Faz pesquisas em comum entre os dois mensageiros"""

    def __init__(self, conn):
        self.conn = conn
        self.api_client = PratoAbertoApiClient()

    def fluxo_conversa(self):
        return self._step1()

    def _step1(self):
        name = input('digite o nome da escola\n')
        escolas = self._get_escolas(name)
        if not escolas:
            return 'não temos escolas para a descrição {}'.format(name)
        escola = self._escolhe_escola(escolas)
        if not escola:
            return 'voce voltou'
        return escola

    #
    # Private
    #

    def _get_escolas(self, name):
        """
        Retorna array parecido com este:
        [
        {'_id': 108, 'nome': 'marcelo maia'},
        {'_id': 19089, 'nome': 'EMEI JOAO RUBENS MARCELO (TERC.)'}
        ]
        onde vem o id do mongo e o nome da escola, sendo que
        id é a mesma coisa que o codigo eol
        """
        return self.api_client.get_escolas_by_name(name)


    def _escolhe_escola(self, escolas):
        print('Escolha uma das escolas pela numeração\n')
        for escola in escolas:
            print('{} - {}'.format(escola['_id'], escola['nome']))
        eol = input('Escolha uma escola\n')
        retval = None
        for escola in escolas:
            if eol == str(escola['_id']):
                retval = escola
        return retval


b = BaseBot('')
print(b.fluxo_conversa())
