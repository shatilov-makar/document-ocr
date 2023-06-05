import pygsheets
from os.path import exists
import streamlit as st
import json


class ExcelExport:
    '''
        Класс для экспорта данных в google sheets

        Параметры:
            df : датафрейм для экспорта в google sheets 
    '''

    def __init__(self, df):
        self.__df = df
        if (~exists('client_secret.json')):
            self.__create_client_secret()
        gc = pygsheets.authorize("client_secret.json")
        sheet = gc.open('my sheet')
        self.workspace = sheet.sheet1

    def __create_client_secret(self):
        service_account_info = {
            'web':
                st.secrets['web']
        }
        with open("client_secret.json", "w") as js:
            json.dump(service_account_info, js, default=dict)

    def export_to_google_sheet(self):
        counts = int(self.workspace[1][1]) + 3
        self.workspace.set_dataframe(self.__df, (counts, 1), copy_head=False)
