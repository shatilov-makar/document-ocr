# Оцифровка уведомления о готовности к реализации арестованного имущества

## Описание приложения
Цель приложения - перевод  в текстовый вид фотографии/скана документа определенного формата.

Алгоритм работы:
1. Загрузка скана фотографии, из которой необходимо получить данные в цифровом виде. 
2. Обработка, распознавание текста с помощью yandex vision https://cloud.yandex.ru/services/vision  
3. Вывод результата на UI

Приложение развернуто на платформе Streamlit: https://ocr-documents.streamlit.app
