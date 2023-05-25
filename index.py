import streamlit as st
from Ocr import Ocr
from JsonParser import JsonParser
from Ner import Ner
import pdf2image
import aspose.words as aw
import io


but = False
def load_image():
    label_text = 'Выберите фотографию документа для распознавания'
    allowed_files = ['jpeg', 'jpg','png','pdf']
    uploaded_file = st.file_uploader(label=label_text, type=allowed_files)
    if uploaded_file is not None:
        image_data = ''
        if uploaded_file.type == "application/pdf":
            try:
                images = pdf2image.convert_from_bytes(uploaded_file.read())
                st.image(images[0], use_column_width=True)

                doc = aw.Document(uploaded_file)
                page = doc.extract_pages(0, 1)
                buf = io.BytesIO()
                saveOptions = aw.saving.ImageSaveOptions(aw.SaveFormat.JPEG)

                page.save(buf,save_options=saveOptions)
                image_data = buf.getvalue()
            except:
                st.warning('**Не удалось отбразить документ**')
                st.stop()
        else:
            image_data = uploaded_file.getvalue()
            st.image(image_data)
        return image_data
    else:
        return None

st.title('Оцифровка уведомления о готовности к  \
         реализации арестовнного имущетсва')
img = load_image()

@st.cache_data(show_spinner=False)  
def get_data(img):
    ocr = Ocr()
    ocr_result = ocr.get_recognition(img)
    jsonParser = JsonParser(ocr_result)
    df = jsonParser.get_property()
    return jsonParser,df

if img:
    with st.spinner('Идет обработка...'):
        jsonParser, df = get_data(img)
        if (len(df) == 0):
            st.warning('**Не удалось распознать документ**')
            st.stop()   
        try:
            ner = Ner(jsonParser.doc_text)
            st.success('**Результаты распознавания:**')
            notif_number = ner.get_notif_number()
            notif_data = ner.get_notif_date()
            st.write('Увед. № ' + notif_number + ' от ' + notif_data)
            st.dataframe(df, use_container_width=False)
            officer_dep = st.text_input('Отдел',ner.get_officer_dep())
            officer_name= st.text_input('Имя СПИ',ner.get_officer_name())
            debtor= st.text_input('Должник',ner.get_debtor_name())
            claimant = st.text_input('Взыскатель',ner.get_claimant())
            print(officer_dep, officer_name,debtor,claimant)
        except:
            st.warning('**Не удалось распознать документ**')
            st.stop()
