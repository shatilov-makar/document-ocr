from requests import post
import json
import base64
import streamlit as st


connection_data = {
    'iam_url':  st.secrets['IAM_URL'],
    'vision_url':  st.secrets['VISION_URL'],
    'folder_id':  st.secrets['FOLDER_ID'],
    'oauth_token': st.secrets['OAUTH_TOKEN']
}


class Ocr:
    '''
        Класс для запроса на yandex.cloud с целью
        распознавания текста на изображении
    '''

    def __init__(self):
        self.vision_url = connection_data['vision_url']
        self.folder_id = connection_data['folder_id']
        self.oauth_token = connection_data['oauth_token']
        self.iam_token = self.__get_iam_token(connection_data['iam_url'])

    def __get_iam_token(self, iam_url):
        '''
            Функция возвращает IAM-токен для аккаунта на Яндексе
        '''
        response = post(iam_url, json={
                        "yandexPassportOauthToken": self.oauth_token})
        json_data = json.loads(response.text)
        if json_data is not None and 'iamToken' in json_data:
            return json_data['iamToken']
        return None

    def __request_analyze(self, image_data):
        '''
            Функция отправляет на сервер запрос на распознавание
            изображения и возвращает ответ сервера.
        '''
        features = [{
            'type': 'TEXT_DETECTION',
            'textDetectionConfig': {'languageCodes': ['en', 'ru']}
        }]
        response = post(self.vision_url,
                        headers={'Authorization': 'Bearer ' + self.iam_token},
                        json={
                            'folderId': self.folder_id,
                            'analyzeSpecs': [
                                {
                                    'content': image_data,
                                    'features': features,
                                }
                            ]}
                        )
        return response.text

    def get_recognition(self, image):
        '''
            Функция кодирует изображение, отправляет его на распознавание
            текста и возвращает результат распознавания в формате json.

            Параметры:
                image : изображение, из которого нужно извлечь текст
        '''
        image_data = base64.b64encode(image).decode('utf-8')
        response_text = self.__request_analyze(image_data)
        json_object = json.loads(response_text)
        return json_object['results'][0]['results'][0]['textDetection']
