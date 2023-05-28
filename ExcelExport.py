import string
import xlsxwriter
from io import BytesIO

class ExcelExport:
    '''
        Класс для экспорта данных в excel

        Параметры:
            df : датафрейм для экспорта в excel 
    '''
    def __init__(self, df):
        self.__df = df
        self.__headers_count = 19
        self.__headers = ['Вх. дата', 'Номер увед-я', 'Дата увед-я','Форма реал-и', 'Вид имущ-ва', 'Имущество','Кол-во',
                'Стоимость', 'Должник', 'Взыскатель', 'СПИ','Контактные данные СПИ, о/х',
                'Дата истечения срока действия отчета об оценке','Дата уведомления о снижении',
                'Дата посупления постановления на 15%','Статус залогового имущества',
                'Дата пост-я о передаче','Дата пост-я об оценке','Фото','Доп информация']

    def export_to_excel(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
      #  workbook = xlsxwriter.Workbook('example.xlsx')
        worksheet = workbook.add_worksheet()
        self.__add_headers(worksheet,workbook)
        self.__add_body(worksheet,workbook)
        workbook.close()
        return output
    
    def __add_headers(self, worksheet, workbook):
        '''
            Функция определяет заголовок таблицы
        '''
    
        worksheet.set_column(0,5, 15) 
        worksheet.set_column(5,5, 30) 
        worksheet.set_column(6,18, 20)

        header_format = workbook.add_format()
        header_format.set_bg_color('#00FFFF')
        header_format.set_align('center')
        header_format.set_align('vcenter')
        header_format.set_border(1)
        header_format.set_text_wrap()        
        header_coords = [letter+'1' for letter in string.ascii_uppercase[:self.__headers_count]]

        for header, coords in zip(self.__headers,header_coords):
            worksheet.write(coords, header, header_format)


    
    def __add_body(self, worksheet,workbook):
        '''
            Функция определяет тело таблицы
        '''
        properties = [list(i.values()) for i in self.__df.to_dict(orient='records')]
        columns_with_data=['B','C','F','G','H','I','J','K']
        columns = string.ascii_uppercase[:self.__headers_count]
        cell_format = workbook.add_format()
        cell_format.set_align('center')
        cell_format.set_align('vcenter')
        cell_format.set_border(1)
        cell_format.set_text_wrap()
        for i, prop_items in enumerate(properties):
            for col in columns: #zip(columns_with_data, prop_items.values()):
                coords = f'{col}{i+2}'
                if col in columns_with_data:
                    worksheet.write(coords, prop_items.pop(0), cell_format)
                else:
                    worksheet.write(coords, '', cell_format)



