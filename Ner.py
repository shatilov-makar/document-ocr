import re
from datetime import datetime
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    NewsNERTagger,
    DatesExtractor,
    Doc
)


class Ner:
    def __init__(self, text):
        '''
        Класс для поиска интересующих нас одиночных сущностей

        Параметры:
            text : текст в формате строки
        '''
        self.morph_vocab = MorphVocab()
        emb = NewsEmbedding()
        self.segmenter = Segmenter()
        self.morph_tagger = NewsMorphTagger(emb)
        self.ner_tagger = NewsNERTagger(emb)
        self.text = text
        self.dates_extractor = DatesExtractor(self.morph_vocab)
        self.dates = list(self.dates_extractor(self.text))
        self.spans = self.__get_spans()

    def get_notif_number(self):
        '''
            Функция возвращает номер уведомлений
        '''
        return re.search(r"\d\d-\d+/\d\d",  self.text).group(0)

    def get_notif_date(self):
        '''
            Функция возвращает дату уведомления
        '''
        if (len(self.dates) > 0):
            date = self.dates[0].fact
            return datetime(date.year, date.month, date.day).strftime("%d.%m.%y")
        return '-'

    def __get_spans(self):
        '''
            Функция возвращает массив сущностей типа ORG и PER
        '''
        start_index = self.text.lower().find('передано')
        end_index = self.text.lower().find('приложение')
        if start_index == -1:
            return []#start_index = 0
        self.span_text = self.text[start_index:end_index]
        doc = Doc(self.span_text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)
        doc.tag_ner(self.ner_tagger)
        for span in doc.spans:
            span.normalize(self.morph_vocab)
        return list(filter(lambda r: r.type == 'ORG' or r.type == 'PER', doc.spans))

    def get_bailiff_org(self):
        '''
            Функция возвращает название отдела СПИ
        '''
        spans = list(filter(lambda r: r.type == 'ORG', self.spans))
        if (len(spans) > 0 and spans[0].start < len(self.span_text)/2 and len(spans[0].normal) > 3):
            return spans[0].normal
        return '-'

    def get_bailiff_name(self):
        '''
            Функция возвращает имя СПИ
        '''
        spans = list(filter(lambda r: r.type == 'PER', self.spans))
        if (len(spans) > 0 and spans[0].start < len(self.span_text)/2 and len(spans[0].normal) > 3) :
            return spans[0].normal
        return '-'

    def get_claimant_name(self):
        '''
            Функция возвращает имя/название компании должника
        '''
        if (len(self.spans) < 3):
            return '-'
        spans = self.spans[-2:]
        if (spans[0].start > len(self.span_text)/2 and spans[1].start > len(self.span_text)/2 and len(spans[0].normal) > 3):
            return spans[0].normal
        elif (spans[0].start < len(self.span_text)/2 and spans[1].start > len(self.span_text)/2 and len(spans[1].normal) > 3):
            return spans[1].normal
        return '-'


    def get_debtor(self):
        '''
            Функция возвращает имя/название компании взыскателя
        '''
        if (len(self.spans) < 3):
            return '-'
        spans = self.spans[-2:]
        if (spans[0].start > len(self.span_text)/2 and spans[1].start > len(self.span_text)/2 and len(spans[1].normal) > 3) :
            return spans[1].normal
        return '-'