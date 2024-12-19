import requests
from bs4 import BeautifulSoup
import re  # Импортируем модуль для работы с регулярными выражениями
from babel.dates import format_date  # Импортируем функцию для форматирования дат
from datetime import datetime
import aiohttp
import asyncio


def get_water_temperatures_from_html(html_content):
    print("Начинаем извлечение температур из HTML контента.")
    soup = BeautifulSoup(html_content, 'html.parser')

    temperatures = {}
    table = soup.find('table')  # Находим первую таблицу на странице
    rows = table.find_all('tr')[1:]  # Пропускаем заголовок таблицы

    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 2:
            source = cols[0].text.strip()  # Название источника
            temperature = cols[1].text.strip()  # Температура
            temperatures[source] = temperature
            print(
                f"Извлечена температура: {temperature} для источника: {source}")

    # Извлечение месяца и года из заголовка
    title = soup.find('h2', class_='font-special page-title').text
    match = re.search(r'за (\w+) (\d{4})', title)
    if match:
        month_year = f"{match.group(1)} {match.group(2)}".lower()
        print(f"Извлечены месяц и год: {month_year}")
    else:
        month_year = None  # Если не найдено, устанавливаем в None
        print("Месяц и год не найдены.")

    return temperatures, month_year  # Возвращаем только температуры и месяц/год


def fetch_news_data(start_index):
    all_temperatures = {}
    print(f"Начинаем проверку новостей, начиная с индекса {start_index}.")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    last_successful_index = None  # Переменная для хранения последнего успешного индекса
    index = start_index  # Начинаем с начального индекса

    while True:
        #        print(f"Проверяем новость с индексом: {index}")
        url = f'https://portal.tgc1.ru/directorate/news/{index}'
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                last_successful_index = index  # Обновляем индекс последней успешной страницы
                title = BeautifulSoup(response.content, 'html.parser').find(
                    'h2', class_='font-special page-title').text  # Получаем заголовок
#                print(f"Заголовок страницы: {title}")

                if "Температура холодной воды к отчету" in title:
                    temperatures, month_year = get_water_temperatures_from_html(
                        response.content)  # Теперь вызываем функцию для получения температур
                    print(
                        f"Извлечены данные: {temperatures}, месяц и год: {month_year}")

                    if month_year:
                        # Обновляем словарь температур
                        all_temperatures.update(temperatures)
#                else:
#                    print(
#                        f"Заголовок не содержит нужный текст: {title}. Продолжаем проверку новостей.")

                soup = BeautifulSoup(response.content, 'html.parser')
                news_item_date = soup.find('div', class_='news-item-date')
                if news_item_date and " я " in news_item_date.text:
                    #                    print(
                    #                        "Обнаружен элемент с классом 'news-item-date' и текстом 'я'. Завершаем проверку новостей.")
                    break  # Выходим из цикла, если элемент найден
            else:
                #                print(
                #                    f"Получен код статуса {response.status_code}. Завершаем проверку новостей.")
                break  # Выходим из цикла, если код ответа не 200

            index += 1  # Переходим к следующему индексу
        except Exception as e:
            #            print(f"Ошибка при обработке {url}: {e}")
            break  # Выходим из цикла в случае ошибки

    # Заменяем запятые на точки в значениях all_temperatures
    for key in all_temperatures:
        all_temperatures[key] = all_temperatures[key].replace(',', '.')

    # Возвращаем также последний успешный индекс
#    print(
#        f"Возвращаем все извлеченные температуры: {all_temperatures} и последний успешный индекс: {last_successful_index - 1}")
    return all_temperatures, last_successful_index


async def update_temperatures_in_nodes(all_temperatures, nodes, server_url, auth):
    if len(all_temperatures) > 0:
        print("Начинаем обновление температур в узлах.")
        async with aiohttp.ClientSession() as session:
            tasks = []  # Список для хранения задач
            for node in nodes['nodes']:
                if 'attributes' in node:
                    for attribute in node['attributes']:
                        if attribute['code'] == 'sourceName':
                            source_name = attribute['value']
                            if source_name in all_temperatures:
                                node['coldWaterSummerTemp'] = all_temperatures[source_name]
                                node['coldWaterWinterTemp'] = all_temperatures[source_name]
                                node_id = node.get('id')
                                print(
                                    f"Обновлены температуры для {source_name}: {all_temperatures[source_name]}")
                                push = [
                                    {
                                        "op": "replace",
                                        "value": all_temperatures[source_name],
                                        "path": "coldWaterSummerTemp"
                                    },
                                    {
                                        "op": "replace",
                                        "value": all_temperatures[source_name],
                                        "path": "coldWaterWinterTemp"
                                    }
                                ]

                                # Создаем асинхронную задачу для отправки данных
                                tasks.append(
                                    send_update(session, server_url,
                                                node_id, push, auth)
                                )
            # Ожидаем завершения всех задач
            await asyncio.gather(*tasks)
        print("Обновление температур завершено.")
    else:
        print("Нет новых температур.")


async def send_update(session, server_url, node_id, push, auth):
    async with session.patch(
        f"{server_url}/api/v1/Core/Nodes/{node_id}",
        json=push,
        headers={'Content-Type': 'application/json-patch+json',
                 'Authorization': f'Bearer {auth}'}
    ) as response:
        if response.status == 200:
            print(f"Температуры для узла {node_id} успешно обновлены.")
        else:
            print(f"Ошибка при обновлении узла {node_id}: {response.status} - {await response.text()}")
