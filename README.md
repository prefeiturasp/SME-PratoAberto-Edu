# Educassis

O Educassis é o robô de atendimento virtual da SME.

Atualmente o robô permite aos usuários:

 * saber o cardápio das escolas;
 * forneceder feedback sobre a comida; e
 * se cadastrar para receber notificações

# Arquitetura

![arquitetura](https://github.com/PratoAberto/educassis/blob/master/assets/arquitetura.png?raw=true)

# Pré-requisitos

 * [rabbitmq](https://www.rabbitmq.com/)
 * [mongodb](https://www.mongodb.com/)
 * [python 3](https://www.python.org/)
 * pacotes python

```
	$ pip install -r requirements.txt
```

Recomenda-se o uso de algum gestor de processos, como o [supervisor](http://supervisord.org/).

# Plataformas de chat

O educassis suporta as seguintes plataformas:

 * [Telegram](https://core.telegram.org/bots#3-how-do-i-create-a-bot)
 * [Facebook](https://developers.facebook.com/docs/messenger-platform/guides/quick-start)

Note que:

 1) Será necessário gerar tokens de acesso à plataforma que desejar suportar, e adicionar no `botconfig.py`
 2) O facebook requer um certificado válido na máquina que receber o webHook

