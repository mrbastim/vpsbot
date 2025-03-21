# VPSBot

VPSBot — это Telegram-бот, который позволяет управлять файлами, получать системную информацию и контролировать сервисы через Telegram.

## Структура проекта

- **bot.py** – основной файл для запуска бота.
- **config.py** – настройки бота (API токен, ID администратора, путь к рабочей директории).
- **handlers/commands.py** – обработчики команд (например, `/start`, `/files`).
- **handlers/callbacks.py** – обработчики callback-запросов для inline-клавиатуры.
- **keyboards.py** – генерация inline-клавиатур.
- **utils/service_manager.py** – управление сервисами с использованием утилиты `systemctl`.
- **utils/system_info.py** – сбор информации о системе (CPU, RAM, дисковое пространство).
- **openvpn-config-tg.sh** – Bash-скрипт для управления OpenVPN клиентами (создание и отзыв сертификатов).
- **requirements.txt** – зависимости проекта.

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

1. Отредактируйте файл [`config.py`](config.py):
   - Укажите ваш API токен в переменной `API_TOKEN`.
   - Укажите ID администратора в переменной `ADMIN_ID`.
   - При необходимости измените рабочую директорию `path_pc_global`.

2. Убедитесь, что система поддерживает работу с `systemctl` и что OpenVPN установлен для корректной работы скрипта [`openvpn-config-tg.sh`](openvpn-config-tg.sh).

## Запуск бота

Запустите бота с помощью команды:
   ```sh
   python bot.py
   ```

При запуске бот отправит сообщение о старте на указанный `ADMIN_ID` и будет готов к взаимодействию.

## Использование

- **Команды в чате:**
  - `/start` или `/help` — вывод приветственного сообщения и основной клавиатуры.
  - `/files list [путь]` — отображение списка файлов в указанной директории.
  - `/files get [путь]` — получение файла по указанному пути.

- **Инлайн-клавиатура:**
  - Кнопки для вывода списка файлов, получения системной информации и управления сервисами.
  - Навигация по файловой системе осуществляется через соответствующие callback-запросы.

- **Управление сервисами:**
  - Получение статуса сервиса и запуск/остановка сервисов через кнопки.
  - Список сервисов генерируется на основании файлов с расширением `.service` в системе.

- **OpenVPN:**
  - Скрипт [`openvpn-config-tg.sh`](openvpn-config-tg.sh) управляет созданием и отзывом сертификатов для клиентов OpenVPN.

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
