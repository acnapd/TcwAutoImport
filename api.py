import requests


def get_auth_token(server_url, login, password):
    # Используем метод GET для получения токена
    response = requests.post(
        f"{server_url}/api/v1/Login", json={"login": login, "password": password, "code": "", "application": ""})
    if response.status_code == 200:
        # Предполагается, что токен возвращается в поле 'token'
        return response.json().get('token')
    else:
        print(
            f"Ошибка при получении токена: {response.status_code} - {response.text}")
        return None


def get_nodes(server_url, auth):
    response = requests.get(f"{server_url}/api/v1/Core/Nodes?getAttributes=true",
                            headers={'Authorization': f'Bearer {auth}'})
    if response.status_code == 200:
        return response.json()  # Возвращаем данные в формате JSON
    else:
        print(
            f"Ошибка при получении списка nodes: {response.status_code} - {response.text}")
        return []
