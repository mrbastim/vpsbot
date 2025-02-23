# My Aiogram Bot

This project is a Telegram bot built using the Aiogram framework. It provides various functionalities such as file management, system information retrieval, and command handling.

## Project Structure

```
my-aiogram-bot
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── bot.py
│   ├── handlers
│   │   ├── __init__.py
│   │   ├── commands.py
│   │   └── callbacks.py
│   ├── modules
│   │   ├── __init__.py
│   │   └── file_manager.py
│   └── utils
│       ├── __init__.py
│       └── system_info.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd my-aiogram-bot
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your bot by editing the `src/config.py` file to include your `API_TOKEN` and `ADMIN_ID`.

## Usage

To run the bot, execute the following command:
```
python src/main.py
```

## Features

- **Command Handling**: Responds to commands like `/start` and `/files`.
- **File Management**: Lists and sends files from the server.
- **System Information**: Retrieves and displays CPU and RAM usage.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.