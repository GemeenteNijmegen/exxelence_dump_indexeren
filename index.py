
from io import TextIOWrapper
import json
import os
import sys

def index(dump_root):
    print('Indexeren van dump op locatie: {}'.format(dump_root))
    dirs = os.listdir(dump_root)
    for dir in dirs:
        path = os.path.join(dump_root, dir)
        create_zaak_index(path, dir)

def create_zaak_index(path, zaak_nummer):
    csv_file = '{}.csv'.format(zaak_nummer)
    try: 
        # Clear the existing index file if running the script multiple times
        os.remove(csv_file)
    except OSError:
        pass
    print('Index voor zaak type {} wordt gemaakt in {}'.format(zaak_nummer, csv_file))
    with open(csv_file, 'w') as csv:
        csv.write('datum,naam,locatie\n')
        write_entries_to_index(path, csv)

def write_entries_to_index(zaak_path, csv: TextIOWrapper):
    entries = os.listdir(zaak_path)
    for entry in entries:
        print('... processing {}'.format(entry))
        path = os.path.join(zaak_path, entry)
        metadata = load_metadata(path, entry)
        datum = metadata['registratiedatum']

        if metadata['initiator'] == None:
            name = metadata['toelichting']
        else:
            name = get_name(metadata)

        csv.write('{},{},{}\n'.format(datum, name, path))


def get_name(metadata):
    firstname = metadata['initiator']['person']['firstNames']
    lastname = metadata['initiator']['person']['lastName']
    tussenvoegsel = metadata['initiator']['person']['lastNamePrefix']
    if tussenvoegsel == None:
        return firstname + ' ' + lastname
    return firstname + ' ' + tussenvoegsel + ' ' + lastname
        

def load_metadata(path, case_nr):
    filename = '{}_case.meta'.format(case_nr)
    metadata_file = os.path.join(path, filename)
    f = open(metadata_file)
    metadata = json.load(f)
    f.close()
    return metadata

if __name__ == "__main__":
    dump_root = os.path.abspath( sys.argv[1] )
    index(dump_root)