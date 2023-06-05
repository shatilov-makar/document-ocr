import streamlit as st
from Ocr import Ocr
from JsonParser import JsonParser
from Ner import Ner
from ExcelExport import ExcelExport
import pdf2image
import aspose.words as aw
import io
import pandas as pd



if 'file_index' not in st.session_state:
    st.session_state['file_index'] = 0

if 'files_count' not in st.session_state:
    st.session_state['files_count'] = 0

def load_image():
    label_text = 'Выберите фотографию документа для распознавания'
    allowed_files = ['jpeg', 'jpg','png','pdf']
    uploaded_files = st.file_uploader(
        label=label_text, type=allowed_files, accept_multiple_files=True)
    if uploaded_files:
        st.session_state['files_count'] = len(uploaded_files)
        current_file = [uploaded_file for i, uploaded_file in enumerate(uploaded_files)
                        if i == st.session_state['file_index']][0]
        image_data = ''
        if current_file.type == "application/pdf":
            try:
                images = pdf2image.convert_from_bytes(current_file.read())
                st.image(images[0], use_column_width=True)

                doc = aw.Document(current_file)
                page = doc.extract_pages(0, 1)
                buf = io.BytesIO()
                saveOptions = aw.saving.ImageSaveOptions(aw.SaveFormat.JPEG)

                page.save(buf,save_options=saveOptions)
                image_data = buf.getvalue()
            except:
                st.warning('**Не удалось отбразить документ**')
                st.stop()
        else:
            image_data = current_file.getvalue()
            st.image(image_data)
        return image_data
    else:
        return None

st.title('Оцифровка уведомления о готовности к  \
         реализации арестовнного имущетсва')
img = load_image()

@st.cache_data(show_spinner=False,ttl=600)  
def get_recognized_data(img):
    ocr = Ocr()
    ocr_result = ocr.get_recognition(img)
    jsonParser = JsonParser(ocr_result)
    df = jsonParser.get_property()
    return jsonParser,df

@st.cache_data(show_spinner=False,ttl=600) 
def to_sheet(df, notif_number, notif_date, debtor, claimant, officer):
    try:
        df =  df[( df['property'].str.lower().str.find('итого') < 0)]    
        df.insert(0, "notif_number", notif_number)
        df.insert(1, "notif_date", notif_date)
        df.loc[:,'debtor' ] = debtor
        df.loc[:,'claimant' ] = claimant
        df.loc[:,'officer' ] = officer
        excel = ExcelExport(df)
        excel.export_to_google_sheet()
        return 'OK'
    except:
        return 'ERROR'
    




if img:
    with st.spinner('Идет обработка...'):
        jsonParser, df = get_recognized_data(img)
        if (len(df) == 0):
            st.warning('**Не удалось распознать документ**')
            st.stop()   
        try:
            ner = Ner(jsonParser.doc_text)
            st.success('**Результаты распознавания:**')
            notif_number = ner.get_notif_number()
            notif_date = ner.get_notif_date()
            st.write('Увед. № ' + notif_number + ' от ' + notif_date)
            st.dataframe(df, use_container_width=False)
            officer_dep = st.text_input('Отдел',ner.get_officer_dep())
            officer_name= st.text_input('Имя СПИ',ner.get_officer_name())
            debtor= st.text_input('Должник',ner.get_debtor_name())
            claimant = st.text_input('Взыскатель',ner.get_claimant())


            to_excel = st.button('Добавить в реестр',type="primary")
            if to_excel:
                result = to_sheet(df, notif_number, notif_date, debtor, claimant, officer_name)
                if 'ОК':
                    st.success('**Добавлено в реестр!**')
                else:
                    st.warning('**Не удалось добавить документ в реестр**')


        except:
            st.warning('**Не удалось распознать документ**')
            st.stop()



def flip_document():
    st.session_state['file_index'] += 1
    
if (st.session_state['file_index'] < st.session_state['files_count'] - 1):
   st.button('Далее', on_click=flip_document)