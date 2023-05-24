import re
from datetime import datetime as dt
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
        self.persons, self.orgs, self.entities = self.__get_named_entities()

    def get_notif_number(self):
        '''
            Функция возвращает номер уведомлений
        '''
        notif = re.findall(r"\d\d-\d+/\d\d", self.text)
        if (len(notif) > 0):
            return notif[0]
        return '-'

    def get_notif_date(self):
        '''
            Функция возвращает дату уведомления
        '''
        if (len(self.dates) > 0):
            date = self.dates[0].fact
            return dt(date.year, date.month, date.day).strftime("%d.%m.%y")
        return '-'

    def __get_named_entities(self):
        '''
            Функция возвращает массивы сущностей типа ORG и PER
        '''
        start_index = self.text.lower().find('передано')
        end_index = self.text.lower().find('приложение')
        if start_index == -1:
            return [], [], []
        self.span_text = self.text[start_index:end_index]
        doc = Doc(self.span_text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)
        doc.tag_ner(self.ner_tagger)
        for span in doc.spans:
            span.normalize(self.morph_vocab)
        orgs = list(filter(lambda r: r.type == 'ORG', doc.spans))
        persons = list(filter(lambda r: r.type == 'PER', doc.spans))
        entities = list(filter(lambda r: r.type == 'PER'
                               or r.type == 'ORG', doc.spans))
        return persons, orgs, entities

    def get_officer_dep(self):
        '''
            Функция возвращает название отдела СПИ
        '''
        if (len(self.orgs) > 0 and
                self.orgs[0].start < len(self.span_text)/2 and
                len(self.orgs[0].normal) > 3):
            return self.orgs[0].normal
        return '-'

    def get_officer_name(self):
        '''
            Функция возвращает имя СПИ
        '''
        if (len(self.persons) > 0 and
                self.persons[0].start < len(self.span_text)/2 and
                len(self.persons[0].normal) > 3):
            return self.persons[0].normal
        return '-'

    def get_debtor_name(self):
        '''
            Функция возвращает имя/название компании должника
        '''
        if (len(self.entities) < 3):
            return '-'
        named_entities = self.entities[-2:]
        if (named_entities[0].start > len(self.span_text)/2 and
                named_entities[1].start > len(self.span_text)/2 and
                len(named_entities[0].normal) > 3):
            return named_entities[0].normal
        elif (named_entities[0].start < len(self.span_text)/2 and
                named_entities[1].start > len(self.span_text)/2 and
                len(named_entities[1].normal) > 3):
            return named_entities[1].normal
        return '-'

    def get_claimant(self):
        '''
            Функция возвращает имя/название компании взыскателя
        '''
        if (len(self.entities) < 3):
            return '-'
        named_entities = self.entities[-2:]
        if (named_entities[0].start > len(self.span_text)/2 and
                named_entities[1].start > len(self.span_text)/2 and
                len(named_entities[1].normal) > 3):
            return named_entities[1].normal
        return '-'