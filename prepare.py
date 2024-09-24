import yaml
import pandas as pd
import os
import shutil
from pathlib import Path

def load_config(config_path="config.yaml"):
    """
    Loads the configuration file.

    Keyword arguments:
    config_path -- the path to the configuration file (default "config.yaml")

    Returns:
    config -- the configuration file as a dictionary
    """
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config


def prepare():
    """
    Prepare the database files for working with ANNOVAR.
    """
    prepare_remove_del()
    prepare_convert_to_txt()
    prepare_clean()


def parse_detailed_vcf_line(line):
    """
    Parse a line from a detailed VCF file.

    Keyword arguments:
    line -- the line to parse
    """
    parts = line.strip().split('\t')
    if len(parts) < 8: 
        return None
    chrom, pos, _, ref, alt = parts[:5]
    info_fields = parts[7].split(';')
    info_dict = {}
    for field in info_fields:
        key, value = field.split('=', 1) if '=' in field else (field, '')
        info_dict[key] = value
    clnalleleid = info_dict.get('ALLELEID', '')
    clndn = info_dict.get('CLNDN', '').replace(',', '\\x2c')  
    clndisdb = info_dict.get('CLNDISDB', '').replace(',', '\\x2c') 
    clnrevstat = info_dict.get('CLNREVSTAT', '').replace(',', '\\x2c') 
    clnsig = info_dict.get('CLNSIG', '').replace(',', '\\x2c')
    alt = alt.replace('.', '-')
    return [chrom, pos, pos, ref, alt, clnalleleid, clndn, clndisdb, clnrevstat, clnsig]


def prepare_remove_del():
    """
    Replace the string "<DEL>" with "." in the VCF files.
    """
    for p in conf['removeDEL']:
        db = [x for x in conf['databasesTXT'] + conf['databasesVCF'] + conf['databasesGFF3'] if x['id'] == p['id']]
        # Duplicate the file in the temp folder
        db_filename = db[0]['file']
        db_extension = Path(db_filename).suffix
        name = Path(db_filename).stem
        dest = conf['db_path'] + "temp/"
        if not os.path.exists(dest):
            os.makedirs(dest)
        shutil.copy(conf['db_path'] + db_filename, dest + name + db_extension)
        
        # Open the file for reading
        with open(dest + name + ".vcf", 'r', encoding='utf-8') as file:
            # Open a new file for writing the modified VCF data
            with open(f"{conf['db_path']}{name}{db_extension}", 'w', encoding='utf-8') as output_file:
                for line in file:
                    if line.startswith('#'):
                        output_file.write(line)
                        continue
                    columns = line.split('\t')
                    alt_column = columns[4].replace('<DEL>', '.')
                    columns[4] = alt_column
                    columns = [col.replace('%3A', ':').replace('%3B', ';').replace('%3D', '=') for col in columns]
                    output_file.write('\t'.join(columns))
            
        shutil.rmtree(dest)
        print(f"Prepare {p['id']} - String \"<DEL>\" replacement complete!")


def prepare_convert_to_txt():
    """"
    Convert the selected databases from VCF to TXT format.
    """
    for p in conf['convertFromVCFToTxt']:
        db = [x for x in conf['databasesTXT'] + conf['databasesVCF'] + conf['databasesGFF3'] if x['id'] == p['id']]
        # Duplicate the file in the temp folder
        db_filename = db[0]['file']
        db_filename = [file for file in os.listdir(conf['db_path']) if file.startswith(db_filename)][0]
        name = Path(db_filename).stem

        # Build the new lines with the detailed format
        detailed_format_lines = []

        # Read the VCF file and parse the lines
        with open(conf['db_path'] + db_filename, 'r') as file:
            for line in file:
                if line.startswith('#'):  
                    continue
                parsed_line = parse_detailed_vcf_line(line)
                if parsed_line:  
                    detailed_format_lines.append(parsed_line)

        # New lines will be in the following format:
        # Chr	Start	End	Ref	Alt	CLNALLELEID	CLNDN	CLNDISDB	CLNREVSTAT	CLNSIG
        detailed_annovar_df = pd.DataFrame(detailed_format_lines, columns=['#Chr', 'Start', 'End', 'Ref', 'Alt', 'CLNALLELEID', 'CLNDN', 'CLNDISDB', 'CLNREVSTAT', 'CLNSIG'])
        
        output_file_path_detailed = f"{conf['db_path']}{name}.txt"  
        detailed_annovar_df.to_csv(output_file_path_detailed, sep='\t', index=False, header=True)
        print(f"Prepare {p['id']} - Format converted from vcf to txt!")


def prepare_clean():
    """"
    Clean the selected databases. It removes initial lines starting with a Sharp (#) character.
    """
    for p in conf['clean']:
        db = [x for x in conf['databasesTXT'] + conf['databasesVCF'] + conf['databasesGFF3'] if x['id'] == p['id']]
        # Duplicate the file in the temp folder
        db_filename = db[0]['file'] + ".txt"
        db_extension = Path(db_filename).suffix
        name = Path(db_filename).stem
        dest = conf['db_path'] + "temp/"
        if not os.path.exists(dest):
            os.makedirs(dest)
        shutil.copy(conf['db_path'] + db_filename, dest + name + db_extension)

        # Open the file for reading
        with open(dest + name + db_extension, 'r', encoding='utf-8') as file:
            # Open a new file for writing the modified VCF data
            with open(f"{conf['db_path']}{name}{db_extension}", 'w', encoding='utf-8') as output_file:
                for line in file:
                    if line.startswith('#'):
                        # identify the header string if it starts with one of the following strings
                        if line.startswith(('# Chromosome\t', '#Chromosome\t', '# Chr\t', '#Chr\t', '# CHROM\t', '#CHROM\t')):
                            output_file.write(line)
                        continue
                    output_file.write(line)
            
        shutil.rmtree(dest)
        print(f"Prepare {p['id']} - Cleane complete!")


# Load the configuration file while loading the module
conf = load_config()