��    M      �  g   �      �  6   �     �     �     �  	         8   #  $  \  �   �
  �   2  [  �  Y   "     |     �     �     �  #   �  (   �     "     @  1   _     �     �  9   �  &     #   (  2   L  C     @   �  1     .   6  *   e     �  *   �     �     �      �  ,        L  2   R  <   �  3   �  4   �  R   +  Y   ~  M   �  <   &  3   c  &   �  �   �  c   a  ?   �  #     4   )  �   ^  )     (   7  B   `  0   �  G   �  ?     [   \  Q   �  8   
  /   C  U   s  S   �  0     6   N  [   �  )   �  f     6   r  "   �  B   �  
          u   �  '     %   8  $   ^     �  9  �  o   �  K  <  e  �!  �   �"  �  �#  �   �%  6   [&  &   �&  &   �&     �&  ?   �&  B   2'  <   u'  ;   �'  O   �'  '   >(     f(  R   �(  C   �(  )   )  l   F)  t   �)  v   (*  b   �*  P   +  G   S+  5   �+  ;   �+  &   ,  #   4,  3   X,  p   �,     �,  T   
-  i   _-  Z   �-  e   $.  z   �.  �   /  {   �/  |   0  Y   �0  S   �0  >  21  �   q2  e   [3  5   �3  S   �3  -  K4  B   y5  p   �5  �   -6  �   �6  �   v7  h   @8  �   �8  �   S9  m   �9  M   c:  �   �:  �   K;  }   �;  ?   V<  �   �<  N   B=  �   �=  q   @>  C   �>  a   �>     X?         )   ?       $   F   &         #       1   9           :   H      ;       "   >   4   E      2      
                       ,      <           I   G   0   '             7       (       =   *   !      %           C       K   B                                                        6   .   3   5       D      -   8             @   L   M   +              /   	   J           A    

All set. Writing / updating your config files now... 
1. [u]General Setup[/] 
2. [u]Bot Setup[/] 
2. [u]Discord Setup[/] 
Aborted. 
For a successful installation, you need to fulfill the following prerequisites:

    1. Installation of PostgreSQL from https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
    2. A Discord TOKEN for your bot from https://discord.com/developers/applications

 
Please provide a channel ID for audit events (optional) 
The Status Channel should be readable by everyone and only writable by the bot.
The Chat Channel should be readable and writable by everyone.
The Admin channel - central or not - should only be readable and writable by Admin and DCS Admin users.

You can create these channels now, as I will ask for the IDs in a bit.
DCSServerBot needs the following permissions on them to work:

    - View Channel
    - Send Messages
    - Read Messages
    - Read Message History
    - Add Reactions
    - Attach Files
    - Embed Links
    - Manage Messages

 
The bot can either use a dedicated admin channel for each server or a central admin channel for all servers.
If you want to use a central one, please provide the ID (optional) 
We now need to setup your Discord roles and channels.
DCSServerBot creates a role mapping for your bot users. It has the following internal roles: 
[green]Your basic DCSServerBot configuration is finished.[/]

You can now review the created configuration files below your config folder of your DCSServerBot-installation.
There is much more to explore and to configure, so please don't forget to have a look at the documentation!

You can start DCSServerBot with:

    [bright_black]run.cmd[/]

 
[i]DCS server "{}" found.[/i]
Would you like to manage this server through DCSServerBot? 
{}. [u]DCS Server Setup[/] 
{}. [u]Database Setup[/] 
{}. [u]Node Setup[/] - Created {} Aborted: No DCS installation found. Aborted: No valid Database URL provided. Aborted: configuration exists Aborted: missing requirements. Adding instance {instance} with server {name} ... DCS-SRS installation path: {} DCS-SRS not configured. DCSServerBot uses up to {} channels per supported server: Directory not found. Please try again. Do you remember the password of {}? Do you want DCSServerBot to autostart this server? Do you want to run DCSServerBot with Discord support (recommended)? Do you want your DCS installation being auto-updated by the bot? Do you want your DCSServerBot being auto-updated? Enter the hostname of your PostgreSQL-database Enter the port to your PostgreSQL-database For admin commands. Have you fulfilled all these requirements? Installation finished. Instance {} configured. No configured DCS servers found. Normal user, can pull statistics, ATIS, etc. Other Please enter the ID of your [bold]Admin Channel[/] Please enter the ID of your [bold]Chat Channel[/] (optional) Please enter the ID of your [bold]Status Channel[/] Please enter the path to your DCS World installation Please enter the path to your DCS-SRS installation.
Press ENTER, if there is none. Please enter your Discord Guild ID (right click on your Discord server, "Copy Server ID") Please enter your Owner ID (right click on your discord user, "Copy User ID") Please enter your PostgreSQL master password (user=postgres) Please enter your discord TOKEN (see documentation) Please enter your password for user {} Please separate roles by comma, if you want to provide more than one.
You can keep the defaults, if unsure and create the respective roles in your Discord server. Please specify, which installation you want the bot to use.
Chose "Other", if it is not in the list SRS configuration could not be created, manual setup necessary. Searching for DCS installations ... Searching for existing DCS server configurations ... The bot can be set to the same language, which means, that all Discord and in-game messages will be in your language as well. Would you like me to configure the bot this way? To display the mission and player status. Users can delete data and change the bot Users can delete data, change the bot, run commands on your server Users can restart missions, kick/ban users, etc. Users can upload missions, start/stop DCS servers, kick/ban users, etc. Which role(s) in your discord should hold the [bold]{}[/] role? Which user(s) should get the [bold]{}[/] role?
Please enter a comma-separated list of UCIDs You now need to setup your users.
DCSServerBot uses the following internal roles: [bright_black]Optional:[/]: An in-game chat replication. [green]- Database user and database created.[/] [i]You can skip the Discord TOKEN, if you decide to do a non-Discord-installation.[/] [red]A configuration for this nodes exists already![/]
Do you want to overwrite it? [red]Master password wrong. Please try again.[/] [red]No PostgreSQL-database found on {host}:{port}![/] [red]SRS configuration could not be created.
Please copy your server.cfg to {} manually.[/] [red]Wrong password! Try again ({}/3).[/] [red]You need to give DCSServerBot write permissions on {} to desanitize your MissionScripting.lua![/] [yellow]Configuration found, adding another node...[/] [yellow]Existing {} user found![/] [yellow]You have entered 3x a wrong password. I have reset it.[/]' {} written Project-Id-Version: 1.0
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Language: ru
 

Все настроено. Записываем / обновляем конфигурационные файлы... 
1. [u]Общая настройка[/] 
2. [u]Установка бота[/] 
2. [u]Настройка Discord[/] 
Отмена. 
Для успешной установки Вам потребуется следующее:

    1. Установленная СУБД PostgreSQL https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
    2. Discord-TOKEN для Вашего бота https://discord.com/developers/applications

 
Пожалуйста укажите канал для сообщений аудита (опционально) 
Канал статуса должен быть доступен всем на чтение и на запись боту.
Канал чата должен быть доступен на чтение и на запись всем.
Административные каналы - общий или отдельные - должны быть доступны на чтение и запись только ролям Admin и DCS Admin.

Вы можете создать каналы сейчас, их ID нужно будет ввести чуть позже.
DCSServerBot для работы требуются следующие разрешения для каналов:

    - View Channel
    - Send Messages
    - Read Messages
    - Read Message History
    - Add Reactions
    - Attach Files
    - Embed Links
    - Manage Messages

 
Бот может использовать выделенные административные каналы для каждого сервера или общий админ-канал для всех серверов сразу.
Если вы хотите использовать общий канал, укажите его ID (опционально) 
Теперь необходимо настроить Discord роли и каналы.
DCSServerBot создаёт маппинг ролей для пользователей бота. Доступны следующие внутренние роли: 
[green]Базовая конфигурация DCSServerBot выполнена.[/]

Вы можете проверить созданную конфигурацию в папке config вашей установки DCSServerBot.
Бот содержит множество настроек, поэтому не забудьте ознакомиться с документацией!

Для запуска DCSServerBot используйте файл:

    [bright_black]run.cmd[/]

 
[i]DCS сервер "{}" найден.[/]
Вы хотите управлять этим сервером с помощью DCSServerBot? 
{}. [u]Конфигурация DCS сервера[/] 
{}. [u]Настройка СУБД[/] 
{}. [u]Настройка ноды[/] - {} Создан Отмена: Не найдена установка DCS World. Отмена: Не указан правильный СУБД URL. Отмена: конфигурация существует. Отмена. Требования не выполнены. Добавление инстанса {instance} с сервером {name} ... Путь установки DCS-SRS: {} DCS-SRS не настроен. DCSServerBot использует {} Discord-каналов на DCS сервер: Папка не найдена. Попробуйте ещё раз. Вы помните пароль от {}? Вы хотите чтобы DCSServerBot автоматически запускал этот сервер? Хотите ли вы запустить DCSServerBot с поддержкой Discord (рекомендуется)? Вы хотите чтобы бот автоматически обновлял вашу установку DCS World? Вы хотите включить автоматическое обновление DCSServerBot? Введите имя хоста вашего СУБД-сервера PostgreSQL Введите порт вашего СУБД-сервера PostgreSQL Для административных команд. Вы выполнили все эти требования? Установка завершена. Инстанс {} настроен. Нет настроенных DCS серверов. Обычный пользователь, может запрашивать статистику, ATIS, и т.д. Прочее Пожалуйста введите ID вашего [bold]админ-канала[/] Пожалуйста введите ID вашего [bold]чат-канала[/] (опционально) Пожалуйста введите ID вашего [bold]статус-канала[/] ein Пожалуйства введите путь до папки, где установлен DCS World Введите путь до установки DCS-SRS.
Нажмите ENTER, если DCS-SRS не установлен. Пожалуйста введите ваш Discord Guild ID (правый щелчок по Discord-серверу, "Copy Server ID") Пожалуйста введите ваш Owner ID (правый щелчок по Discord-серверу, "Copy User ID") Введите мастер-пароль вашего СУБД-сервера PostgreSQL (пользователь=postgres) Пожалуйста введите ваш Discord TOKEN (см. документацию) Пожалуйста введите пароль для пользователя {} Пожалуйста, при указании более одной роли, разделяйте их запятой.
Вы можете оставить значения по умолчанию если не уверены и создать необходимые роли на сервере Discord вручную. Пожалуйста, укажите, какую установку вы хотите, чтобы использовал бот.
Выберите "Другое", если подходящего варианта нет в списке SRS-конфигурация не создана, требуется ручная настройка. Поиск установленного DCS World ... Поиск существующих конфигураций сервера DCS ... Бот может быть настроен на ваш родной язык, что означает что все игровые и Discord сообщения будут показываться на вашем языке. Вы хотите использовать локализацию бота? Для показа статуса миссии и игроков. Пользователи с правом удалять данные и менять параметры бота Пользователи могут удалять данные, изменять настройки бота и выполнять команды на вашем сервере. Пользователи с правом перезапускать миссии, выгонять/банить пользователей и т. д. Пользователи могут заливать миссии, запускать и останавливать DCS серверы, кикать и банить пользователей и т.д. Какие роли на вашем Discord серверы должны быть [bold]{}[/] ролью? Какой пользователь(и) должен(ы) получить роль [bold]{}[/]?
Введите список UCID, разделенный запятыми Теперь вам нужно настроить пользователей.
DCSServerBot использует следующие внутренние роли: [bright_black]Опционально:[/]: Канал с репликацией игрового DCS чата. [green]- Пользователь и база данных созданы.[/] [i]Вы можете пропустить ввода токена Discord, если решите выполнить установку без Discord.[/] [red]Конфигурация для данной ноды уже существует!![/]
Вы хотите перезаписать её? [red]Неправильный пароль для пользователя "postgres". Попробуйте ещё раз.[/] [red]Не найдена БД PostgreSQL на {host}:{port}![/] [red]Не получилось создать SRS-конфигурацию.
Пожалуйста скопируйте файл server.cfg в папу {} вручную.[/] [red]Неверный пароль! Попробуйте снова ({}/3).[/] [red]Вам необходимо предоставить DCSServerBot права на запись {} для десанитизации вашего MissionScripting.lua![/] [yellow]Конфигурация найдена, добавление дополнительной ноды...[/] [yellow]Пользователь {} уже существует![/] [yellow]Вы ввели неверный пароль  3 раза . Я сбросил его.[/]' {} записан 