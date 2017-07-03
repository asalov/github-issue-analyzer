from nltk.corpus import stopwords

class DataCleaner:
    
    # Clean dataset
    def clean(self, data, fields, null='any'):
        data = self.remove_null(data, fields, null)
        data = self.remove_empty(data, fields)
        
        return data
    
    # Remuve NULL values
    def remove_null(self, data, fields, null='any'):                 
        return data.dropna(subset=fields, how=null)

    # Remove empty strings
    def remove_empty(self, data, fields):
        for field in fields:
            not_empty = data[field].str.strip() != ''
            data = data[not_empty]
            
        return data
    
    # Remove duplicate values
    def remove_duplicates(self, data, fields, duplicate_each=False, keep='first'):
        if duplicate_each:
            for field in fields:
                data = data.drop_duplicates(field, keep=keep)
        else:
            data = data.drop_duplicates(fields, keep=keep)
        
        return data
    
    # Remove non English entries
    def filter_english(self, data, fields):
        english = set(stopwords.words('english'))
        is_english = dict()
        column_names = list()
        
        for field in fields:
            is_english[field] = list()
            entries = data[field].str.split(' ')
            
            for text in entries:
                word_count = 0
                
                for word in text:
                    if word.lower() in english: word_count += 1
            
                is_english[field].append(word_count > 0)
                          
            column_name = field + '_is_english'
            column_names.append(column_name)
            data.loc[:, column_name] = is_english[field]
        
        filtered = data.filter(items=column_names)
        has_english = filtered.isin([True]).sum(axis=1) > 0
        
        data = data[has_english]
        data = data.drop(column_names, axis=1)
        
        return data