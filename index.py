import streamlit as st
from Ocr import Ocr
from JsonParser import JsonParser
from Ner import Ner
import pdf2image
import io
ocr = Ocr()


def load_image():
    label_text = 'Выберите фотографию документа для распознавания'
    allowed_files = ['jpeg', 'jpg','png','pdf']
    uploaded_file = st.file_uploader(label=label_text, type=allowed_files)
    if uploaded_file is not None:
        image_data = ''
        if uploaded_file.type == "application/pdf":
            images = pdf2image.convert_from_bytes(uploaded_file.read(),
                                                  fmt='jpeg', dpi=600)
            page = images[0]
            st.image(page, use_column_width=True)
            buf = io.BytesIO()
            page.save(buf, format='JPEG')
            image_data = buf.getvalue()
        else:
            image_data = uploaded_file.getvalue()
            st.image(image_data)
        return image_data
    else:
        return None


st.title('Оцифровка уведомления о готовности к  \
         реализации арестовнного имущетсва')
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
        st.success('**Результаты распознавания:**')
        notif_number = ner.get_notif_number()
        notif_data = ner.get_notif_date()
        st.write('Увед. № ' + notif_number + ' от ' + notif_data)
        st.dataframe(df, use_container_width=False)
        st.write(f'**Отдел** : { ner.get_officer_dep()}')
        st.write(f'**Имя СПИ** : { ner.get_officer_name()}')
        st.write(f'**Должник** : { ner.get_debtor_name()}')
        st.write(f'**Взыскатель** : { ner.get_claimant()}')