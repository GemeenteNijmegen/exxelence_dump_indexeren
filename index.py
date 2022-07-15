
import json
from operator import contains
import os
import shutil
import sys
from time import time
from dataclasses import dataclass
import traceback

@dataclass
class Statistics:
    """Class for keeping track of dump statistics."""
    zaak_types: int = 0
    zaken: int = 0
    files: int = 0
    time: int = time()
    fails: int = 0

    def new_zaak_type(self):
        self.zaak_types += 1

    def new_zaak(self):
        self.zaken += 1

    def new_file(self):
        self.files += 1

    def new_fail(self):
        self.fails += 1

    def print_statistics(self):
        duration = (time() - self.time)
        print("Dump statistics:")
        print("Er zijn {} zaak types.".format(self.zaak_types))
        print("Er zijn {} zaken.".format(self.zaken))
        print("De zaken hebben {} files.".format(self.files))
        print("Het indexeren heeft {} seconden geduurd (dat is {} uur).".format(duration, duration/3600))
        print("Het indexeren van {} zaken is fout gegaan.".format(self.fails))
        print("\n\n")


class Indexer:

    def __init__(self, dump_root, zaak_type) -> None:
        self.stats = None
        self.dump_root = dump_root
        self.failed = None
        self.csv = None 
        self.zaak_type = zaak_type

    def index(self):
        print('Indexeren van dump op locatie: {}'.format(self.dump_root))
        self.failed = self.create_failed_file()
        self.stats = Statistics()

        dirs = os.listdir(dump_root)
        for dir in dirs:
            if contains(dir, 'Zoekmap'):
                print('Skip zoekmap')
                continue
            if self.zaak_type == None or (self.zaak_type != None and dir == self.zaak_type):
                path = os.path.join(dump_root, dir)
                self.create_zaak_index(path, dir)
        
        self.failed.close()

    def create_zaak_index(self, path, zaak_nummer):
        self.csv = self.create_csv_file(zaak_nummer)
        self.stats.new_zaak_type()
        self.write_entries_to_index(path)
        self.stats.print_statistics()
        self.csv.close()

    def write_entries_to_index(self, zaak_path):
        entries = os.listdir(zaak_path)
        print("Processing entries...")
        for entry in entries:
            self.stats.new_zaak()
            path = os.path.join(zaak_path, entry)
            sys.stdout.write('... processing {} \r'.format(entry))
            sys.stdout.flush()
            try:
                self.process_entry(entry, path)
            except Exception as e:
                self.failed.write('{},{},{}\n'.format(entry, str(e), path))
                self.failed.flush()
                self.stats.new_fail()
                print(traceback.format_exc())
        print("Klaar met zaak type {}\n".format(zaak_path))

    def process_entry(self, entry, path):
        self.create_index(path, entry)
        self.rename_files(path)

    def rename_files(self, path):
        files = os.listdir(path)
        files = filter(lambda file: file.endswith('.bin'), files)
        for file in files:
            self.stats.new_file()
            filename = file[:-3] + 'meta'
            # print(filename)
            metadata = self.load_metadata(path, filename)
            original_filename_extension = metadata['bestandsnaam'][-3:]
            new_filename = file[:-3] + original_filename_extension
            shutil.move(os.path.join(path, file), os.path.join(path, new_filename))

    def create_index(self, path, entry):
        filename = '{}_case.meta'.format(entry)
        metadata = self.load_metadata(path, filename)
        datum = metadata['registratiedatum']
        name = self.get_name(metadata)
        self.csv.write('{},{},{}\n'.format(datum, name, path))


    def get_name(self, metadata):
        firstname = ''
        tussenvoegsel = ''
        lastname = ''
        toelichting = ''
        bsn = ''

        if self.is_filled(metadata, 'toelichting'):
            toelichting = metadata['toelichting']

        if self.is_filled(metadata, 'initiator'):
            if self.is_filled(metadata['initiator'], 'person'): 
                firstname = metadata['initiator']['person']['firstNames']
                lastname = metadata['initiator']['person']['lastName']
                bsn = metadata['initiator']['person']['citizenNumber']
                tussenvoegsel = metadata['initiator']['person']['lastNamePrefix']
                if tussenvoegsel == None: 
                    tussenvoegsel = ''
                
            if 'employee' in metadata['initiator']:
                toelichting += ' (medewerker)'
            elif 'organization' in metadata['initiator']:
                toelichting += ' (organization)'

        return '{},{},{},{},{}'.format(toelichting, bsn, firstname, tussenvoegsel, lastname)

    def is_filled(self, dict, tag):
        return tag in dict and dict[tag] != None

    def load_metadata(self, path, filename):
        metadata_file = os.path.join(path, filename)
        f = open(metadata_file)
        metadata = json.load(f)
        f.close()
        return metadata

    def create_failed_file(self):
        failed_file = 'failed_{}.csv'.format(time())
        failed = open(failed_file, 'w')
        failed.write('zaak,reason,locatie\n')
        return failed

    def create_csv_file(self, zaak_nummer):
        csv_file = '{}.csv'.format(zaak_nummer)
        print('Index voor zaak type {} wordt gemaakt in {}'.format(zaak_nummer, csv_file))

        try: # Remove if exists 
            os.remove(csv_file)
        except OSError:
            pass

        csv = open(csv_file, 'w')
        csv.write('datum,toelichting,bsn,voornamen,tussenvoegsel,achternaam,locatie\n')
        return csv
    

if __name__ == "__main__":
    dump_root = os.path.abspath( sys.argv[1] )
    
    zaak_type = None
    if len(sys.argv) == 3:
        zaak_type = sys.argv[2]
    
    indexer = Indexer(dump_root, zaak_type)
    indexer.index()