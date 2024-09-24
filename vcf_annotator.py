import os
import argparse
from datetime import datetime, date
import yaml
import requests 
import shutil
from bs4 import BeautifulSoup
from packaging import version
import re
import pandas as pd
import prepare
from tabulate import tabulate
from dateutil.parser import parse
from pathlib import Path

# Name of Columns for the databases in TXT format to be merged
CLINVAR_COLUMNS = ['CLNALLELEID', 'CLNDN', 'CLNDISDB', 'CLNREVSTAT', 'CLNSIG']
OMIM_COLUMNS = ['MIM Number', 'Gene/Locus And Other Related Symbols', 'Gene Name', 'Approved Gene Symbol', 'Entrez Gene ID', 'Ensembl Gene ID', 'Comments', 'Phenotypes', 'Mouse Gene Symbol/ID']

# Name of Columns for the databases in VCF format to be split
HGMD_COLUMNS = ['CLASS', 'MUT', 'GENE', 'STRAND', 'DNA', 'PROT', 'DB', 'PHEN', 'RANKSCORE', 'SVTYPE', 'END', 'SVLEN']
GNOMAD_COLUMNS = ['AC', 'AN', 'AF']


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


def generate_temp(file_name, file_name_temp, destination_path):
    """"
    Generates temporary files in which to store the result of the annotation with each single database.
    
    Keyword arguments:
    file_name -- the name of the file to be copied
    file_name_temp -- the name of the temporary file to be created
    destination_path -- the path where the temporary files will be stored
    """
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
    if not os.path.exists(destination_path + "/temp/"):
        os.makedirs(destination_path + "/temp/")
    original = file_name + ".hg38_multianno.txt"
    destination = file_name_temp + ".hg38_multianno.txt"
    shutil.copy(original, destination)
    

def scrape(website_info):
    """
    Scrapes the website for the latest release date or version number.

    Keyword arguments:
    website_info -- a dictionary containing the website URL, the release date or version number to search for, the text to search for, and the tag to search for
    
    Returns:
    True if the release date or version number is greater than the one specified in the configuration file, i.e., if there is a new release
    """
    # The header is used to bypass anti-bot
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': website_info['website']
    }
    url = website_info['website']
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        items_with_searched_tag = soup.find_all(lambda tag: tag.name == website_info['tag'] and website_info['textToSearch'] in tag.text)
        for row in items_with_searched_tag:
            if ("release" in website_info.keys()):
                text = row.text.replace(website_info['textToSearch'], "").split(' ')[0]
                if (text and version.parse(text) > version.parse(website_info['release'])):
                    return True
            elif ("date" in website_info.keys()):
                text = row.text.strip().replace(website_info['textToSearch'], "")
                if (not is_date(text)):
                    text = text.split(' ')[0].split(".")[0].split("_")[0]
                if (text and is_date(text) and parse(text).date() > datetime.strptime(website_info['date'], '%Y-%m-%d').date()):
                    return True

        return False
    else:
        print("Failed to retrieve content: ", response.status_code)


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    Keyword arguments:
    string -- string to check for date
    fuzzy --  ignore unknown tokens in string if True

    Return: 
    True if the string is a date
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False
    

def scraping_mode(scraping):
    """"
    Executes the scraping mode.
    
    Keyword arguments:
    scraping -- a list of dictionaries containing the information needed to scrape the websites
    """
    scraping_result = {}
    for dt_to_check in scraping:
        scraping_result[dt_to_check['id']] = [dt_to_check['release'] if 'release' in dt_to_check.keys() else "/", 
                                              dt_to_check['date'] if 'date' in dt_to_check.keys() else "/",
                                              scrape(dt_to_check)]
    tabulate_updates(scraping_result)


def tabulate_updates(scraping_result):
    """"
    Tabulates the scraping results.

    Keyword arguments:
    scraping_result -- a dictionary containing the scraping results
    """
    data = []
    for key, value in scraping_result.items():
        data.append([key, value[0], value[1], "[!]" if value[2] else " "])
    headers = ["Database", "Release", "Date", "Update"]
    print(tabulate(data, headers=headers, tablefmt="fancy_grid"))


def annotate_file(path, conf):
    """
    Annotates the VCF file.

    Keyword arguments:
    path -- the path to the VCF file
    conf -- the configuration file
    """
    DATABASE_TYPES = ['databasesTXT', 'databasesVCF', 'databasesGFF3']
    for db_type in DATABASE_TYPES:
        if db_type in conf and conf[db_type]:
            for db in conf[db_type]:
                print(f"**** Annotating with {db['id']} ****")
                fileName = destination_path + db['id']+'_' + Path(path).stem + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
                fileNameTemp = destination_path + "temp/" + db['id'] + "_" + Path(path).stem + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
                # Execute the annovar command
                if db_type == 'databasesTXT':
                    if db['file'].startswith('hg38_'):
                        db['file'] = db['file'].replace('hg38_', '')
                    print(f"perl table_annovar.pl '{path}' {db_path} -buildver hg38 -out {fileName} -remove -protocol {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                    os.system(f"perl table_annovar.pl '{path}' {db_path} -buildver hg38 -out {fileName} -remove -protocol {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                elif db_type == 'databasesVCF':
                    print(f"perl table_annovar.pl '{path}' {db_path} -buildver hg38 -argument '-infoasscore' -out {fileName} -remove -protocol vcf -vcfdbfile {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                    os.system(f"perl table_annovar.pl '{path}' {db_path} -buildver hg38 -argument '-infoasscore' -out {fileName} -remove -protocol vcf -vcfdbfile {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                elif db_type == 'databasesGFF3':
                    print(f"perl table_annovar.pl '{path}' {db_path} -buildver hg38 -out {fileName} -remove -gff3dbfile {db['file']} -protocol gff3 -operation {db['operation']} -nastring . -vcfinput -polish")
                    os.system(f"perl table_annovar.pl '{path}' {db_path} -buildver hg38 -out {fileName} -remove -gff3dbfile {db['file']} -protocol gff3 -operation {db['operation']} -nastring . -vcfinput -polish")
                else:
                    print("Error: Invalid database type")
                    
                generate_temp(fileName, fileNameTemp, destination_path)
                
    # Create the merged file
    create_single_file(path, destination_path, conf)   


def merge_columns(path, destination_path, conf):
    """
    Merge columns from the temporary files and split columns from the merged file.
    
    Keyword arguments:
    path -- the path to the VCF file
    destination_path -- the path to the destination folder
    conf -- the configuration file
    """
    dest = destination_path + "temp/"
    combined_data = pd.DataFrame()
    print("Annotation results merging...")
    # Fetch all files in the temporary folder
    files = sorted([file for file in os.listdir(dest) if file.endswith('.txt')])
    for i, fname in enumerate(files):
        # Read the data from the selected temporary file
        data = pd.read_csv(dest + fname, sep='\t')
        # Use basic information from the first file. The others will be appended
        if i == 0:
            combined_data = data
             
        # Check if the file contains the VCF or GFF3 column, and thus if it comes from a VCF or GFF3 database
        if ('vcf' in data.columns or 'gff3' in data.columns):  
            column_name = 'vcf' if 'vcf' in data.columns else 'gff3' if 'gff3' in data.columns else ValueError("No column found")
            db_name = fname.split('_')[0]
            # Create the new column, named after the database
            combined_data[db_name] = data[column_name]
            if i == 0:
                combined_data.drop(columns=[column_name], inplace=True)   

        elif i != 0 and conf['databasesTXT']: 
            # Copy the columns of interest from the TXT databases, such as Clinvar e OMIM
            for cl_name in CLINVAR_COLUMNS + OMIM_COLUMNS:
                if cl_name in data.columns:
                    combined_data[cl_name] = data[cl_name]

    nameFile, _ = os.path.splitext(os.path.basename(path))
    file = destination_path + nameFile + '_result_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S') + '.txt'
    # Remove from combined_data columns with name starting with Otherinfo
    combined_data = combined_data[combined_data.columns.drop(list(combined_data.filter(regex='Otherinfo')))]
    combined_data.to_csv(file, sep='\t', index=False)
    shutil.rmtree(dest)
    return file


def create_single_file(path, destination_path, conf):
    """
    Merge columns from the temporary files and split columns from the merged file.
    
    Keyword arguments:
    path -- the path to the VCF file
    destination_path -- the path to the destination folder
    conf -- the configuration file
    """
    # First, create the file by merging all those previously created by the annotation process
    file = merge_columns(path, destination_path, conf)
    
    # Now, split the columns if necessary
    if conf['databasesVCF']:    
        # VCF databases require splitting the columns 
        for database in conf['databasesVCF']:
            df = pd.read_csv(file, sep="\t")
            NEW_COLUMN_NAME = database['id']
            # Create a new column with the name of the new columns
            for nc in GNOMAD_COLUMNS + HGMD_COLUMNS:
                df[nc] = '.'

            db_split = df[NEW_COLUMN_NAME].str.split(";", expand=True)
            for index, row in db_split.iterrows():
                for value in row.dropna():  # Use dropna() to ignore NaN values
                    if(value != '.' and value is not None) :
                        db_col_split = value.split("=")[0]
                        if db_col_split in GNOMAD_COLUMNS + HGMD_COLUMNS:
                            df.loc[index, db_col_split] = value.split("=")[1]

            df.drop(columns=[NEW_COLUMN_NAME], inplace=True)      
            df.to_csv(file, sep='\t',index=False)

    print("Merging and Splitting columns complete!") 
        
        
if __name__ == "__main__":
    # Load the configuration file
    conf = load_config()
    db_path = conf["db_path"]
    destination_path = conf["destination_path"]
    scraping = conf["scraping"] 

    # Parse the command line arguments    
    parser = argparse.ArgumentParser(description="VCFAnnotator - Annotates your VCF files")
    annotateVCF_group = parser.add_argument_group('option for --annotateVCF')
    parser.add_argument("--annotateVCF", "-a",help="Annotate VCF file", action="store", metavar="PATH")
    annotateVCF_group.add_argument("--DBPath", "-db", help="Database path for ANNOVAR", metavar="PATH DB", required=False)
    annotateVCF_group.add_argument("--DestinationPath", "-d", help="Destination path for annotated files", metavar="PATH DEST", required=False)
    parser.add_argument("--checkDB", "-c",help="Check if DB was updated", action="store_true")
    parser.add_argument("--prepare", "-p",help="Prepare Databases", action="store_true")
    args = parser.parse_args()

    # Annotation path
    path = ""

    # Check if folders have been rewritten
    if args.annotateVCF:
        path = args.annotateVCF
        if args.DBPath:
            db_path = args.DBPath
        if args.DestinationPath:
            destination_path = args.DestinationPath
        elif not os.path.exists(destination_path):
            os.makedirs(destination_path)
    else:
        if args.DBPath or args.DestinationPath:
            parser.error("--DBPath/-db and --DestinationPath/-d options can be set only if --annotateVCF is used")
            
    if args.annotateVCF:
        # Annotation mode
        
        if os.path.exists(path) and os.path.exists(db_path) and os.path.exists(destination_path):
            # Check if all path exist
            if(conf['autoCheck']):
                scraping_mode(scraping)

            print(f"Processing {path}...")

            if os.path.isfile(path):
                # Analyzing a single file
                annotate_file(path, conf)
            
            elif os.path.isdir(path):
                # Analyzing a directory
                for f in os.listdir(path):
                    if f.endswith(".vcf"):
                        full_file_path = os.path.join(path, f)
                        annotate_file(full_file_path, conf)

            else:
                parser.error("Error: Not a valid file or directory")

    elif args.checkDB:
        # Scraping mode
        scraping_mode(scraping)
    elif args.prepare:
        # Prepare mode
        prepare.prepare()
    else:
        parser.error("Error: Invalid command line input. Please check your syntax or path and try again.")