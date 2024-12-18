import argparse


def get_command_line_args():
    parser = argparse.ArgumentParser(
        description='Запуск приложения для извлечения температур.')
    parser.add_argument('--server', required=True, help='Адрес сервера API')
    parser.add_argument('--login', required=True,
                        help='Логин для доступа к API')
    parser.add_argument('--password', required=True,
                        help='Пароль для доступа к API')
    return parser.parse_args()
