import re
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer, SnowballStemmer
from bs4 import BeautifulSoup
import pandas as pd

class TextPreprocessor:
    
    # Prepare dataset
    def prepare(self, data, stopwords=list()):
        if(isinstance(data, (list, pd.Series))):
            data = [self.prepare(item) for item in data]                
        else:
            data = self.normalize(data)
            data = self.strip_all(data)
            data = self.tokenize(data)
            data = self.strip_alpha(data)
            data = self.remove_stopwords(data, stopwords)
            data = self.lemmatize(data)
        
        return data
        
    # Convert text to lowercase
    def normalize(self, text):
        return text.lower()
    
    # Split text into separate words
    def tokenize(self, text):
        return word_tokenize(text)
    
    # Remove most common English words from text
    def remove_stopwords(self, text, stopword_list=list()):
        stop = set(stopword_list) if stopword_list else set(stopwords.words('english'))
    
        return [word for word in text if word not in stop]
    
    # Remove word suffixes     
    def stem(self, text):
        stemmer = SnowballStemmer('english')
        
        return [stemmer.stem(word) for word in text]
    
    # Convert words into their root form    
    def lemmatize(self, text):
        wnl = WordNetLemmatizer()
        ds = self.get_word_pos(text)
        
        return [wnl.lemmatize(word[0], pos=word[1]) for word in ds]
    
    # Determine POS for each word             
    def get_word_pos(self, text):
        ds = pos_tag(text)
        
        return ((word[0], self.get_wordnet_pos(word[1])) for word in ds)
    
    # Transform POS tags from one implementation to another
    def get_wordnet_pos(self, treebank_tag):
        return {
                'J': wordnet.ADJ,
                'V': wordnet.VERB,
                'M': wordnet.VERB,
                'N': wordnet.NOUN,
                'R': wordnet.ADV
        }.get(treebank_tag[0], wordnet.NOUN)

    # Remove all non-alphabetic chars from text            
    def strip_alpha(self, text):
        return [word for word in text if word.isalpha()]

    # Remove HTML tags from text            
    def strip_html(self, text):
        return BeautifulSoup(text, 'lxml').get_text()
        
    # Replace chars in text using regex 
    def strip_chars(self, text, regex, replace=''):
        return re.sub(regex, replace, text)
    
    # Remove URL's
    def strip_url(self, text):
        regex = r'(((http|https):\/\/)|www\.)[A-Za-z0-9_?\-./+=#&%]+'
        
        return self.strip_chars(text, regex)
    
    # Remove emails
    def strip_email(self, text):
        regex = r'[A-Za-z0-9_.]+@[A-Za-z0-9_.]+\.[A-Za-z.]{2,}'
        
        return self.strip_chars(text, regex)
    
    # Remove duplicate characters
    def strip_duplicate(self, text):
        regex = r'(.)\1{2,}'
        replace = r'\1'
        
        return self.strip_chars(text, regex, replace)

    # Remove all unwanted characters
    def strip_all(self, text):
        ds = self.strip_html(text)
        ds = self.strip_url(ds)
        ds = self.strip_email(ds)
        ds = self.strip_duplicate(ds)
        
        return ds