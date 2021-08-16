#!/usr/bin/env python

import sys
import csv
import traceback
from splunklib.searchcommands import \
    dispatch, EventingCommand, Configuration, Option, validators


@Configuration()
class LookupSearch(EventingCommand):

    lookup_name = Option(
        doc='''
        **Syntax:** **lookup_name=***<lookup_name>*
        **Description:** Name or path of lookup file.''',
        require=True)
    

    exact_match = Option(
        doc='''
        **Syntax:** **exact_match=***<true-false>*
        **Description:** Exact match for comparing fields.''',
        require=False, validate=validators.Boolean(), default=True)
    
    case_sensitive = Option(
        doc='''
        **Syntax:** **case_sensitive=***<true-false>*
        **Description:** Case sensitivity.''',
        require=False, validate=validators.Boolean(), default=True)

    search_field = Option(
        doc='''
        **Syntax:** **search_field=***<search_field>*
        **Description:** Field from main search.''',
        require=True, validate=validators.Fieldname())

    lookup_field = Option(
        doc='''
        **Syntax:** **lookup_field=***<lookup_field>*
        **Description:** Field from lookup''',
        require=True, validate=validators.Fieldname())
    
    def csv_to_json(self, csv_file_path):
        json = []
        with open(csv_file_path, "r") as csvlookup:
            data = csv.DictReader(csvlookup)
            for i in data:
                json.append(i)
        return json



    def transform(self, events):

        if not self.lookup_name.startswith("/"):
            self.lookup_name = "../lookups/" + self.lookup_name
        
        lookup_data = self.csv_to_json(self.lookup_name)
        if self.case_sensitive:
            lookup_data_list = [i[self.lookup_field] for i in lookup_data if i[self.lookup_field].strip() != '']
        else:
            lookup_data_list = [i[self.lookup_field].lower() for i in lookup_data if i[self.lookup_field].strip() != '']

        for event in events:
            try:
                if event[self.search_field] == '':
                    continue
            except KeyError:
                break
            if self.exact_match == True and self.case_sensitive == True:
                if event[self.search_field] in lookup_data_list:
                    yield event
            elif self.exact_match == True and self.case_sensitive == False:
                if event[self.search_field].lower() in lookup_data_list:
                    yield event
            elif self.exact_match == False and self.case_sensitive == False:
                if any(event[self.search_field].lower() in i.lower() for i in lookup_data_list) or any(i.lower() in event[self.search_field].lower() for i in lookup_data_list):
                    yield event
            else:
                if any(event[self.search_field] in i for i in lookup_data_list) or any(i in event[self.search_field] for i in lookup_data_list):
                    yield event
try:
    dispatch(LookupSearch, sys.argv, sys.stdin, sys.stdout, __name__)
except:
    open("/tmp/error.log", "a").write(str(traceback.format_exc()) + "\n\n\n")
