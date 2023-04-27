from requests import post
import pandas as pd
import json
import base64
import streamlit as st
from Ocr import Ocr
from PIL import Image
from JsonParser import JsonParser
from Ner import Ner


ocr = Ocr()


def load_image():
    uploaded_file = st.file_uploader(
        label='Выберите фотографию документа для распознавания')
    if uploaded_file is not None:
        image_data = uploaded_file.getvalue()
        st.image(image_data)
        return image_data
    else:
        return None


st.title('Оцифровка уведомления о готовности к реализации арестовнного имущетсва ')
img = load_image()
result = st.button('Распознать документ')
if result:
    with st.spinner('Идет обработка...'):

        ocr_result = ocr.get_recognition(img)
        jsonParser = JsonParser(ocr_result)

        df = jsonParser.get_property()

        if (len(df) == 0):
            st.warning('**Не удалось распознать документ**')
            st.stop()
        ner = Ner(jsonParser.doc_text)

        notifNumber = ner.get_notif_number()

        st.success('**Результаты распознавания:**')
        st.write('Увед. № ' + ner.get_notif_number() + ' от ' + ner.get_notif_date())
        st.dataframe(df,use_container_width=False)
        st.write(f'**Отдел** : { ner.get_bailiff_org()}' )
        st.write(f'**Имя СПИ** : { ner.get_bailiff_name()}' )
        st.write(f'**Должник** : { ner.get_claimant_name()}' )
        st.write(f'**Взыскатель** : { ner.get_debtor()}' )
