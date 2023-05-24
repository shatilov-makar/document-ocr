import scipy.cluster.hierarchy as hcluster
import pandas as pd
import operator


class JsonParser:
    '''
        Класс для обработки результата ocr от сервиса yandex.cloud.

        Параметры:
            ocr_result : вернувшийся от yandex.cloud результат распознавания
                         текста документа в формате JSON

        Аттрибуты:
            doc_text: текст документа
    '''

    def __init__(self, ocr_result):
        self.__lines = self.__extract_lines(ocr_result['pages'][0])
        self.doc_text = ' '.join([line['text'] for line in self.__lines])

    def __extract_lines(self, recognized_text):
        '''
            Функция возвращает строки документа в формате
                text: текст строки
                x1: левая верхняя координата по X
                x2: правая нижняя координата по X
                y1: левая верхняя координата по Y
                y2: правая нижняя координата по Y

            Параметры:
                json : результат распознавания текста на определенной странице
                       документа в формате JSON
        '''
        lines = []
        for block in recognized_text['blocks']:
            for line in block['lines']:
                text_str = ' '.join(
                    [word['text'] for word in line['words']
                     if word['confidence'] > 0.5])
                line = line['boundingBox']['vertices']
                if ('x' in line[0] and 'y' in line[0]
                        and 'x' in line[2] and 'y' in line[2]):
                    lines.append({'text': text_str,
                                  'x1': int(line[0]['x']),
                                  'y1': int(line[0]['y']),
                                  'x2': int(line[2]['x']),
                                  'y2': int(line[2]['y'])})

        return sorted(lines, key=lambda line: line['y1'])

    def __get_table_lines(self):
        '''
            Функция возвращает строки таблицы
        '''
        stop_words = ['вышеуказанное', 'передано', 'судебным', 'приставом',
                      'исполнителем', 'ареста']
        start_words = ['описание', 'наименование', 'количество',
                       'измерения', '(руб', 'п/', 'n/', 'характеристики']
        table_begin = False
        table_lines = []
        for row in self.__lines:
            text = row['text'].strip()
            if text == '':
                continue
            if list(filter(lambda stop_word:
                           stop_word in text.lower(), stop_words)):
                break
            if list(filter(lambda start_word:
                           start_word in text.lower(), start_words)):
                table_begin = True
            elif table_begin:
                table_lines.append(row)
        return table_lines

    def __get_items_and_attributes(self, table_rows):
        '''
            Возвращает список строк имущества и список кол-ва и цены имущества

            Параметры:
                table_rows : строки таблицы
        '''
        df = pd.DataFrame(table_rows)
        df['cluster'] = hcluster.fclusterdata(
            df[['x1']], t=35, criterion="distance")
        # удаляем случайные кластеры
        df = df[df.groupby(['cluster'])['cluster'].transform('size') > 1]
        # кластер стоимости должен быть самым "правым" и содержать цифры
        prices = df[(df.groupby(['cluster'])['x1'].transform('mean') == max(
            df.groupby(['cluster'])['x1'].mean()))
            & (df['text'].str.contains('\\d'))]
        prices_cluster = prices['cluster'].mean()
        # кластер наименований - самый "длинный" кластер
        items_cluster = max(df.groupby(['cluster'])['text']
                            .apply(','.join)
                            .agg(lambda x: len(x))
                            .items(), key=operator.itemgetter(1))[0]
        items = df[(df['cluster'] == items_cluster) &
                   (df['text'].transform(len) > 3)]
        # удаляем кластеры с ценами и наименованиями
        df = df[(df['cluster'] != prices_cluster) &
                (df['cluster'] != items_cluster)]
        # находим вероятные клаcтеры с количеством имущества
        amount_coords = df.groupby('cluster')['x1'].transform('mean')
        amount_candidates = df[(amount_coords > items['x2'].mean())
                               & (amount_coords < prices['x1'].mean())]
        # кластер с кол-вом имущества должен - самый "короткий" среди них
        amount_cluster = min(amount_candidates.groupby(['cluster'])['text']
                             .apply(','.join)
                             .agg(lambda x: len(x))
                             .items(), key=operator.itemgetter(1))[0]

        amount = df[(df['cluster'] == amount_cluster)
                    & (df['text'].str.contains('\\d'))].to_dict('records')
        attributes = []
        # связываем цену и количество
        if (len(prices) == len(amount)):
            attributes = [{'price': price['text'], 'amount': amount[i]['text'],
                           'x1': amount[i]['x1'], 'x2': amount[i]['x2'],
                           'y1': amount[i]['y1'], 'y2': amount[i]['y2']}
                          for i, price in enumerate(prices.to_dict('records'))]
        else:
            attributes = [{'price': price['text'], 'amount': '-',
                           'x1': price['x1'], 'x2': price['x2'],
                           'y1': price['y1'], 'y2': price['y2']}
                          for price in prices.to_dict('records')]
        return items.to_dict('records'), attributes

    def get_property(self):
        '''
            Возвращает таблицу имущества в формате датафрейма
        '''
        lines = self.__get_table_lines()
        if (len(lines) == 0):
            return pd.DataFrame()
        items, attrs = self.__get_items_and_attributes(lines)
        attr_i = 0
        pairs = []
        total = {}
        if ("итого" in items[-1]['text'].lower()):
            total = {"property": items[-1]['text'].upper(),
                     "amount": attrs[-1]['amount'],
                     "price": attrs[-1]['price']}
            attrs = attrs[:-1]
            items = items[:-1]
        for i, item in enumerate(items):
            if (i == 0):
                pairs.append({"property": item['text'].lstrip('0123456789.- '),
                              "amount": attrs[attr_i]['amount'],
                              "price": attrs[attr_i]['price']})
                continue

            if (len(attrs) == attr_i+1):
                rests = ' '.join(list(map(lambda it: it['text'], items[i::])))
                pairs[attr_i]["property"] += ' ' + rests
                break

            if (item['text'].lstrip('0123456789.- ').split(' ')[0].istitle()) \
                and ((item['y1'] >= attrs[attr_i+1]['y1']
                      and item['y1'] <= attrs[attr_i+1]['y2'])
                     or (item['y2'] >= attrs[attr_i+1]['y1']
                         and item['y2'] <= attrs[attr_i+1]['y2'])
                     or (item['y1'] - attrs[attr_i]['y2'] >=
                         attrs[attr_i+1]['y1'] - item['y2'])):
                attr_i += 1
                pairs.append({"property": item['text'].lstrip('0123456789.- '),
                              "amount": attrs[attr_i]['amount'],
                              "price": attrs[attr_i]['price']})
            else:
                pairs[attr_i]["property"] += ' ' + item['text']
        if (total):
            pairs.append(total)
        df = pd.DataFrame(pairs)
        return df
