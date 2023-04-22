from requests import post
import json
import base64


class Ocr:
    '''
        Класс для запроса на yandex.cloud с целью распознавания текста на изображении 

        Параметры:
            API : словарь с данными, необходимыми для подключения к сервису 
    '''

    def __init__(self, API):
        self.vision_url = API['vision_url']
        self.folder_id = API['folder_id']
        self.oauth_token = API['oauth_token']
        self.iam_token = self.__get_iam_token(API['iam_url'])

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
            Функция отправляет на сервер запрос на распознавание изображения и возвращает ответ сервера.
        '''
        response = post(self.vision_url, headers={'Authorization': 'Bearer ' + self.iam_token}, json={
            'folderId': self.folder_id,
            'analyzeSpecs': [
                {
                    'content': image_data,
                    'features': [
                        {
                            'type': 'TEXT_DETECTION',
                            'textDetectionConfig': {'languageCodes': ['en', 'ru']}
                        }
                    ],
                }
            ]})
        return response.text

    def get_recognition(self, image):
        '''
            Функция кодирует изображение, отправляет его на распознавание текста и возвращает результат распознавания в формате json.

            Параметры:
                image : изображение, из которого нужно извлечь текст 
        '''
        image_data = base64.b64encode(image).decode('utf-8')
        response_text = self.__request_analyze(image_data)
        json_object = json.loads(response_text)
        return json_object['results'][0]['results'][0]['textDetection']
