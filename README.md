# VPSBot

VPSBot — это Telegram-бот, который позволяет управлять файлами, получать системную информацию и контролировать сервисы через Telegram.

## Структура проекта

- **bot.py** – основной файл для запуска бота.
- **setup_config.py** - установка конфигурационного файла config.py
- **config.py** – настройки бота (API токен, ID администраторов, путь к рабочей директории).
- **handlers/commands.py** – публичные команды (`/start`) и admin-команды (`/files`, `/vpn`, `/add_admin`, `/del_admin`).
- **handlers/callbacks.py** – обработчики callback-запросов для inline-клавиатуры (публичные и admin-роутеры).
- **keyboards.py** – генерация inline-клавиатур.
- **middlewares/access.py** – `AccessMiddleware` (белый список) и `AdminMiddleware` (только админы).
- **utils/admin_service.py** – хранение пользователей и ролей в SQLite.
- **utils/path_utils.py** – защита от path traversal (`safe_join`, `safe_filename`).
- **utils/callback_paths.py** – токены для callback_data длиннее 64 байт.
- **utils/service_manager.py** – управление сервисами с использованием утилиты `systemctl`.
- **utils/docker_manager.py** – управление Docker-контейнерами.
- **utils/system_info.py** – сбор информации о системе (CPU, RAM, дисковое пространство).
- **openvpn-config-tg.sh** – Bash-скрипт для управления OpenVPN клиентами (создание и отзыв сертификатов).
- **list-vpn-clients.sh** – Bash-скрипт для вывода списка активных клиентов OpenVPN.
- **tests_security.py**, **tests_access_control.py**, **tests_keyboard.py**, **tests_formatting.py** – тесты безопасности, разграничения доступа, клавиатур и форматирования сообщений.
- **requirements.txt** – зависимости проекта.

## Модель доступа

Доступ разделён на два уровня, оба хранятся в SQLite (`/root/access.db`):

- **Пользователь** (`is_admin = 0`) — только `/start`, `/help` и список команд.
- **Администратор** (`is_admin = 1`) — файлы, Docker, systemd, системная информация, OpenVPN, управление администраторами.

Администраторы из `config.py` получают роль админа автоматически при каждом запуске.

```sh
/add_admin <user_id>   # выдать роль администратора
/del_admin <user_id>   # снять роль (админов из config.py удалить нельзя)
```

Все файловые операции ограничены каталогом `path_pc_global`: выход за его пределы
(`..`, абсолютные пути, symlink наружу) отклоняется. Загрузка файлов очищает имя
от путей и ограничена 512 МБ.

## Установка

1. Клонируйте репозиторий:
   ```sh
   git clone <URL_репозитория>
   cd VPNBot
   ```

2. Установите зависимости:
   ```sh
   pip install -r requirements.txt
   ```

## Настройка

1. Запустите установку конфигурационного файла:
   ```sh
   python setup_config.py
   ```

2. Убедитесь, что система поддерживает работу с `systemctl` и что OpenVPN установлен для корректной работы скрипта [`openvpn-config-tg.sh`](openvpn-config-tg.sh).

## Запуск бота

Запустите бота с помощью команды:
   ```sh
   python bot.py
   ```

При запуске бот отправит сообщение о старте на указанные `ADMIN_IDS` и будет готов к взаимодействию.

## Использование

- **Команды в чате (любой пользователь из белого списка):**
  - `/start` или `/help` — вывод приветственного сообщения и основной клавиатуры.

- **Команды в чате (только администратор):**
  - `/files list [путь]` — отображение списка файлов в указанной директории.
  - `/files get [путь]` — получение файла по указанному пути.
  - `/vpn list`, `/vpn add <клиент> [1|2]`, `/vpn revoke <клиент>` — управление OpenVPN.
  - `/add_admin <user_id>`, `/del_admin <user_id>` — управление доступом.
  - `/del_admin` не удаляет администраторов из `config.py`.

- **Инлайн-клавиатура:**
  - Кнопки для вывода списка файлов, получения системной информации и управления сервисами.
  - Навигация по файловой системе осуществляется через соответствующие callback-запросы.

- **Управление сервисами:**
  - Получение статуса сервиса и запуск/остановка сервисов через кнопки.
  - Список сервисов генерируется на основании файлов с расширением `.service` в системе.

- **OpenVPN:**
  - Скрипт [`openvpn-config-tg.sh`](openvpn-config-tg.sh) управляет созданием и отзывом сертификатов для клиентов OpenVPN.
  - Имя клиента ограничено регулярным выражением `^[A-Za-z0-9_-]{1,32}$` — проверка выполняется и в боте, и в скрипте.

- **Docker:**
  - Просмотр списка контейнеров, запуск, остановка и перезапуск по кнопкам.

## Запуск тестов

```sh
python tests_security.py        # path traversal, роли, callback_data, валидация
python tests_access_control.py  # проверка, что admin-хендлеры закрыты middleware
python tests_keyboard.py        # лимит 64 байта, навигация, Back
python tests_formatting.py      # экранирование текста (Bad Request: can't parse entities)
```

## Форматирование сообщений

Динамический текст (имена файлов, вывод команд, ошибки) отправляется как HTML
`<pre>` с `html.escape(..., quote=False)`. MarkdownV2 не используется: там
зарезервированные символы (`.`, `!`, `-`, `[`) в обычном тексте вызывают
`Bad Request: can't parse entities` при любом имени файла с точкой.

## Лицензия

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
## Контакты

[Telegram](https://t.me/mrbastim)

[ВКонтакте](https://vk.com/mrbastim)
