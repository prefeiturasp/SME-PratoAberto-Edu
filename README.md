# Edu

O Edu é o robô de atendimento virtual da SME.

Atualmente, o robô permite aos usuários:

 * saber o cardápio das escolas;
 * fornecer feedback sobre a refeição; e
 * se cadastrar para receber notificações


# Arquitetura

![arquitetura](https://github.com/PratoAberto/edu/blob/master/assets/arquitetura.png?raw=true)


# Dependências

 * [rabbitmq](https://www.rabbitmq.com/)
 * [mongodb](https://www.mongodb.com/)
 * [python 3](https://www.python.org/)
 * pacotes python (listados em `conf/requirements.txt`)
 * [api pratoaberto](https://github.com/PratoAberto/api)

O Edu usa também:

 * [miniconda](https://conda.io/miniconda.html), como gestor de pacotes e ambientes python
 * [nginx](https://nginx.org/en/), como servidor web
 * [supervisor](http://supervisord.org/), como gestor de processos


# Plataformas de chat

O edu suporta as seguintes plataformas:

 * [Telegram](https://core.telegram.org/bots#3-how-do-i-create-a-bot)
 * [Facebook](https://developers.facebook.com/docs/messenger-platform/guides/quick-start)

Note que:

 1) Será necessário gerar tokens de acesso à plataforma que desejar suportar, e adicionar ao arquivo `conf/bot.conf`
 2) O facebook requer um certificado válido na máquina que receber o webHook


# Coleções do mongodb

O Edu possui três coleções:

 * *messages_meta*, guarda informações das mensagens armazenadas nas filas
 * *chats*, guarda informações dos perfis que já interagiram com o robo
 * *interacoes*, guarda informações sobre as interações dos usuários


# Monitoria

O rabbitmq dispõe de um plugin de administração que também inclui uma interface web. Mais informações na [documentação](https://rabbitmq.docs.pivotal.io/35/rabbit-web-docs/management.html).

As filas de tarefa do Celery podem ser monitoradas através do [flower](http://flower.readthedocs.io/en/latest/).


# Rodando localmente

Atualize `conf/bot.conf` com os apontamentos locais e tokens necessários e gerencie os status dos componentes com o supervisor (um arquivo de configuração está disponível em `conf/supervisor.edu.conf`)

Os webHooks podem ser servidos diretamente do gUnicorn localmente através do [ngrok](https://ngrok.com/).

A API serve os dados sobre escolas e refeições. Veja mais sobre a API no [repositório do projeto](https://github.com/PratoAberto/api)
