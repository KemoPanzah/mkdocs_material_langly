import json, re
from deepl import Translator
from pathlib import Path
from mkdocs.utils import log
from bs4 import BeautifulSoup

# entries = {
#     'en-us': {
#         'decore Base | UI fastly': 'decore Base | UI fastly',
#     },
#     'es': {
#         'decore Base | UI fastly': 'decore Base | UI fastly',
#     },
#     'it': {
#         'decore Base | UI fastly': 'decore Base | UI fastly',
#     },
#     'ru': {
#         'decore Base | UI fastly': 'decore Base | UI fastly',
#     },
#     'fr': {
#         'decore Base | UI fastly': 'decore Base | UI fastly',
#     }
# }

class DeepL(Translator):
    auth_key = json.load(open('auth_key.json'))['deepl']

    def __init__(self):
        Translator.__init__(self, auth_key=self.auth_key)

    # def get_gloss(self):
    #     t_glossary = None
    #     if self.source_lang != self.target_lang:
    #         for i_glossary in self.list_glossaries():
    #             if i_glossary.name == self.target_lang:
    #                 if self.get_glossary_entries(i_glossary) != entries[self.target_lang]:
    #                     self.delete_glossary(i_glossary)
    #                     t_glossary = None
    #                 else:
    #                     t_glossary = i_glossary

    #         if not t_glossary:
    #             t_glossary = self.create_glossary(
    #                 self.target_lang,
    #                 source_lang=self.source_lang,
    #                 target_lang=self.target_lang,
    #                 entries=entries[self.target_lang],
    #             )

    #         return t_glossary

    # def add_tag_ids(self, p_text):
    #     p_text = re.sub(r'<code>(.*?)</code>', r'<code id="\1">\1</code>', p_text)
    #     return p_text
    
    # def remove_tag_ids(self, p_text):
    #     p_text = re.sub(r'<code id="(.*?)">(.*?)</code>', r'<code>\1</code>', p_text)
    #     return p_text

    def add_tag_attr(self, p_text):
        soup = BeautifulSoup(p_text, 'html.parser')
        for code_tag in soup.find_all('code'):
            code_content = code_tag.string
            code_tag['fixed-text'] = code_content
        return str(soup)
    
    def remove_tag_attr(self, p_text):
        soup = BeautifulSoup(p_text, 'html.parser')
        for code_tag in soup.find_all('code'):
            if code_tag.has_attr('fixed-text'):
                code_tag.string = code_tag['fixed-text']
                del code_tag['fixed-text']
        return str(soup)

    def translate(self, p_text, p_source_lang, p_target_lang):
        p_text = self.add_tag_attr(p_text)
        p_text = self.translate_text(p_text, source_lang=p_source_lang, target_lang=p_target_lang, preserve_formatting=True, tag_handling='html').text
        p_text = self.remove_tag_attr(p_text)
        return p_text

class Localizer:
    def __init__(self, p_src_path, p_source_lang, p_target_lang):
        self.__data__ = {}
        self.file_path  = Path('locales').joinpath(p_target_lang).joinpath((p_src_path)).with_suffix('.json')
        self.source_lang = p_source_lang
        self.target_lang = p_target_lang
        self.deepl = DeepL()
        self.load_data()
        # self.gloss = self.get_gloss()

    def load_data(self):
        try:
            with open(self.file_path, 'r') as t_file:
                self.__data__ = json.load(t_file)
        except FileNotFoundError:
            self.__data__ = {}
        
        for i_key in self.__data__:
            self.__data__[i_key]['__active__'] = False

    def save_data(self):
        
        t_key_s = []

        for i_key in self.__data__:
            if not self.__data__[i_key]['__active__']:
                t_key_s.append(i_key)
        
        for i_key in t_key_s:
            del self.__data__[i_key]

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, 'w') as t_file:
            json.dump(self.__data__, t_file, indent=4)


    def translate(self, serve, p_text):
        
        if p_text in self.__data__:
            self.__data__[p_text]['__active__'] = True
        else:
            self.__data__[p_text] = {'__active__': True}
        
        if self.target_lang in self.__data__[p_text]:
            return self.__data__[p_text][self.target_lang]
        
        else:
            
            if self.source_lang == self.target_lang:
                self.__data__[p_text][self.target_lang] = p_text
                return self.__data__[p_text][self.target_lang]
            
            else:
                if not serve:
                    log.info(f'Translating: {p_text} to {self.target_lang}')
                    self.__data__[p_text][self.target_lang] = self.deepl.translate(p_text, self.source_lang, self.target_lang)
                    return self.__data__[p_text][self.target_lang]
                else:
                    return "##DRAFT-MODE##"