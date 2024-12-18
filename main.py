from config import get_command_line_args
from api import get_auth_token, get_nodes
from data_processing import fetch_news_data, update_temperatures_in_nodes
import configparser

if __name__ == "__main__":
    args = get_command_line_args()  # Получаем параметры запуска
    server_url = args.server
    login = args.login
    password = args.password

    config = configparser.ConfigParser()
    config.read('settings.ini')
    # Загружаем последний индекс из файла
    start_index = int(config['News']['last_index']) + 1
    all_news_data, last_successful_index = fetch_news_data(start_index)

    if len(all_news_data) > 0:
        # Получаем токен
        auth_token = get_auth_token(server_url, login, password)
        if not auth_token:
            print("Не удалось получить токен аутентификации. Завершение работы.")
            exit(1)
        # Получаем список nodes
        nodes = get_nodes(server_url, auth_token)

        # Обновляем температуры в объектах
        update_temperatures_in_nodes(
            all_news_data, nodes, server_url, auth_token)
    else:
        print("Завершение работы.")
    # Сохраняем последний индекс только если он был успешным
    if last_successful_index is not None:
        with open('settings.ini', 'w') as config_file:
            config_file.write(
                f"[News]\nlast_index = {last_successful_index - 1}\n")
        pass
