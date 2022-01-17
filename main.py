import argparse
from pathlib import Path
import mimetypes
import os

import requests
import pandas as pd


EMAIL = 'test@huntflow.ru'
PASSWORD = 'jasdf8JSd8fj'
ACCESS_TOKEN = '71e89e8af02206575b3b4ae80bf35b6386fe3085af3d4085cbc7b43505084482'
ENDPOINT = 'https://dev-100-api.huntflow.dev/'
DERAULT_HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}'}


def parse_excel(filename):
    """Парсит excel"""
    data = pd.read_excel(filename)
    return data


def get_account_id():
    """Возвращает account id"""

    account_id = requests.get(
        f'{ENDPOINT}accounts', 
        headers=DERAULT_HEADERS
    ).json().get('items', [])

    return account_id


def get_statuses(account_id):
    """Возвращает список статусов"""

    statuses = requests.get(
        f'{ENDPOINT}account/{account_id}/vacancy/statuses', 
        headers=DERAULT_HEADERS
    ).json().get('items', [])

    return statuses


def get_vacancies(account_id):
    """Возвращает список вакансий"""

    vacancies = requests.get(
        f'{ENDPOINT}account/{account_id}/vacancies', 
        headers=DERAULT_HEADERS
    ).json().get('items', [])

    return vacancies


def add_candidate(account_id, fio, money, position):
    """Добавляет кандидата в базу и возвращает его id"""

    fio = fio.strip().split()

    candidate_data = {
        'last_name': fio[0],
        'first_name': fio[1],
        'money': money,
        'position': position
    }

    if len(fio) > 2:
        candidate_data['middle_name'] = fio[2]

    candidate_id = requests.post(
        f'{ENDPOINT}account/{account_id}/applicants',
        json=candidate_data,
        headers=DERAULT_HEADERS
    ).json().get('id', '')

    return candidate_id


def add_candidate_to_vacancy(account_id, applicant_id, status_id, vacancy_id, file_id, comment):
    """Добавляет кандидата на вакансию"""
    data = {
        'vacancy': vacancy_id,
        'status': status_id,
        'comment': comment,
        'files': [ { 'id': file_id } ]
    }

    print(requests.post(
        f'{ENDPOINT}account/{account_id}/applicants/{applicant_id}/vacancy',
        json=data,
        headers=DERAULT_HEADERS
    ))


def upload_file(account_id, cv_files_path, subfolder, name):
    cv_files = os.listdir(os.path.join(cv_files_path, subfolder))

    for cv in cv_files:
        if Path(cv).stem == name.strip():
            cv_file = cv
            break

    mt = mimetypes.guess_type(os.path.join(cv_files_path, subfolder, cv_file))[0]

    with open(os.path.join(cv_files_path, subfolder, cv_file), 'rb') as f:
        files = {'file': (cv_file, f, mt, {'Expires': '0'})}
    

        file_id = requests.post(
            f'{ENDPOINT}account/{account_id}/upload',
            headers={**DERAULT_HEADERS},
            files=files
        ).json().get('id', '')

    return file_id


def upload_data(data, cv_files_path):

    res_account_id = get_account_id()
    
    if res_account_id:
        account_id = res_account_id[0].get('id', '')
    else:
        print('Invalid access token')
        return

    statuses = get_statuses(account_id)
    vacancies = get_vacancies(account_id)

    # Должность | ФИО | Ожидания по ЗП | Комментарий | Статус
    for ind, row in data.iterrows():

        applicant_id = add_candidate(account_id, row['ФИО'], row['Ожидания по ЗП'], row['Должность'])

        file_id = upload_file(account_id, cv_files_path, row['Должность'], row['ФИО'])

        for vacancy in vacancies:
            if vacancy.get('position', '') == row['Должность']:
                vacancy_id = vacancy.get('id')

        for status in statuses:
            if status.get('name', '') == row['Статус'].strip():
                status_id = status.get('id')

        add_candidate_to_vacancy(account_id, applicant_id, status_id, vacancy_id, file_id, row['Комментарий'])
        

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--e', type = str, help='enter path to excel -excel')
    parser.add_argument('--t', type = str, help='enter token -token')
    parser.add_argument('--cv', type = str, help='enter dir of cv -cv')
    args = parser.parse_args()

    DERAULT_HEADERS = {'Authorization': f'Bearer {args.t}'} if args.t else DERAULT_HEADERS

    data = parse_excel(args.e)
    upload_data(data=data, cv_files_path=args.cv)
