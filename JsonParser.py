import json
import numpy as np
import re


class JsonParser:
    '''
        Класс для обработки результата ocr от сервиса yandex.cloud.

        Параметры:
            ocr_result : вернувшийся от yandex.cloud результат распознавания текста на изображении в формате JSON
    '''

    def __init__(self, ocr_result):
        self.height = int(ocr_result['pages'][0]['height'])
        self.width = int(ocr_result['pages'][0]['width'])
        self.lines, self.text = self.__extract_data(ocr_result['pages'][0])

    def __extract_data(self, json):
        '''

        '''
        lines = []
        text = []
        for block in json['blocks']:
            for line in block['lines']:
                text_in_block = []
                for word in line['words']:
                    if word['confidence'] > 0.8:
                        text_in_block.append(word['text'])
                        text.append(word['text'])
                text_str = ' '.join(text_in_block).strip()
                line = line['boundingBox']['vertices']
                if ('x' in line[0] and 'y' in line[0] and 'x' in line[2] and 'y' in line[2]):
                    lines.append({'text': text_str,
                                  'x1': int(line[0]['x']), 'y1': int(line[0]['y']),
                                  'x2': int(line[2]['x']), 'y2': int(line[2]['y'])})

        return sorted(lines, key=lambda line: line['y1']),   ' '.join(text).strip()

    def __get_prices_and_property(self):
        stop_words = ['вышеуказанное', 'передано', 'судебным', 'приставом',
                      'приставом- исполнителем', 'приставом-исполнителем', 'ареста']

        property_list_coords = {}
        prices = []
        property_list = []

        for row in self.lines:
            text = row['text']

            if list(filter(lambda stop_word: stop_word in text, stop_words)):
                break
            if not property_list_coords and 'количество' in text.lower():
                property_list_coords = {
                    'x1': int(row['x1']), 'y2': int(row['y2'])}

            elif re.findall(r'[\d ]+[\,\. ]\d{1,3}\s?р?p?у?б?\.?', text) and row['x1'] > (self.width/2):
                prices.append(row)

            elif property_list_coords and row['x1'] < (self.width/2) and row['y1'] > property_list_coords['y2']\
                    and not 'описание' in text.lower() and not 'наименование' in text.lower() and len(text) > 3:
                property_list.append(row)

        prices = self.__correct_prices(prices)
        return prices, property_list

    def __correct_prices(self, inp_prices):
        prices = []
        it = iter(inp_prices)
        if (len(inp_prices) > 1):
            for x, y in zip(it, it):
                if abs(x['x1'] - y['x1']) > 20 and abs(x['y1'] - y['y1']) < 20:
                    if x['x1'] < y['x1']:
                        prices.append(y)
                    else:
                        prices.append(x)
                else:
                    prices.extend([x, y])
        if len(inp_prices) % 2 == 1:
            prices.append(inp_prices[-1])
        return prices

    def get_prices_and_property_pairs(self):
        prices, property_list = self.__get_prices_and_property()
        price_i = 0
        pairs = []
        if len(property_list) == 0 or len(prices) == 0:
            return prices, property_list

        for i, item in enumerate(property_list):
            if (i == 0):
                pairs.append({"rows": [item], "price": prices[price_i]})
                continue

            if (len(prices) == price_i+1):
                pairs[price_i]["rows"].append(item)
                break

            if (item['text'].lstrip('0123456789.- ').split(' ')[0].istitle() or "итого" in item['text'].lower())\
                and ((item['y1'] >= prices[price_i+1]['y1'] and item['y1'] <= prices[price_i+1]['y2']) or
                     (item['y2'] >= prices[price_i+1]['y1'] and item['y2'] <= prices[price_i+1]['y2']) or
                     (item['y1'] - prices[price_i]['y2'] >= prices[price_i+1]['y1'] - item['y2'])):
                price_i += 1
                pairs.append({"rows": [item], "price": prices[price_i]})
            else:
                pairs[price_i]["rows"].append(item)
        return pairs
