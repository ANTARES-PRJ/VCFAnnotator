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

#Name of Columns for the databases in TXT format to be merged
ClinvarColumns = ['CLNALLELEID', 'CLNDN', 'CLNDISDB', 'CLNREVSTAT', 'CLNSIG']
OmimColumns = ['MIM Number', 'Gene/Locus And Other Related Symbols', 'Gene Name', 'Approved Gene Symbol', 'Entrez Gene ID', 'Ensembl Gene ID', 'Comments', 'Phenotypes', 'Mouse Gene Symbol/ID']
#Name of Columns for the databases in VCF format to be split
HGMDColumns = ['CLASS', 'MUT', 'GENE', 'STRAND', 'DNA', 'PROT', 'DB', 'PHEN', 'RANKSCORE', 'SVTYPE', 'END', 'SVLEN']
gnomADColumns = ['AC', 'AN', 'AF']


def generateTemp(fileName, fileNameTemp):
    dest = destination_path + "temp/"
    if not os.path.exists(dest):
        os.makedirs(dest)
    shutil.copy(fileName + ".hg38_multianno.txt", fileNameTemp + ".hg38_multianno.txt")
    # the names of the files will be the names of the columns
    
#TODO: Colonne Dei TXT Dinamiche da config(?) 
def mergeColumns(path):
    #! conf['databasesTXT']  #! non dovrebbe essere in una variabile?
    dest = destination_path + "temp/"
    files = sorted([file for file in os.listdir(dest) if file.endswith('.txt')])
    combined_data = pd.DataFrame()
    #print(enumerate(files))
    print("Merging columns...")
    column_name = ''
    for i, fname in enumerate(files):
        data = pd.read_csv(dest + fname, sep='\t')
        if i == 0:
            combined_data = data
             
        if not column_name and ('vcf' in data.columns or 'gff3' in data.columns):  
            column_name = 'vcf' if 'vcf' in data.columns else 'gff3' if 'gff3' in data.columns else ValueError("No column found")
            combined_data[fname] = data[column_name]
            if i == 0:
                combined_data.drop(columns=[column_name], inplace=True)   
        elif i != 0:
            if conf['databasesTXT']: #if there are databasesTXT in the config file
                #Clinvar e OMIM
                for cl_name in ClinvarColumns + OmimColumns:
                    if cl_name in data.columns:
                        combined_data[cl_name] = data[cl_name]
                        #! if i == 0:
                            #! combined_data.drop_duplicates(keep='last',subset=cl_name) 
        column_name = ''
        nameFile,ext = os.path.splitext(os.path.basename(path))
    file = destination_path+nameFile+'_result_'+datetime.now().strftime('%Y-%m-%d_%H_%M_%S')+'.txt'
    combined_data.to_csv(file, sep='\t', index=False)
    shutil.rmtree(dest)
    
    #TODO: prendere il nome colonna dinamicamente --> magari con una varibile globale per ogni DB in modo da modificarla una sola volta
    #? Split DatabasesVCF
    # se la lista non è vuota
    if conf['databasesVCF']:
        for database in conf['databasesVCF']:
            #è attivo HGMD
            if 'id' in database and database['id'] == 'HGMD':
                print("Split HGMD columns...")
                df = pd.read_csv(file, sep="\t")              
                nameColumb = 'HGMD.hg38_multianno.txt'
                # create a new column with the name of the new columns
                for nc in HGMDColumns:
                    df[nc] = '.'    # None charter for empty cells
                hgmd_split = df[nameColumb].str.split(";", expand=True)
                
                for index, row in hgmd_split.iterrows():
                    for value in row.dropna():  # Usa dropna per ignorare i valori NaN
                        if(value != '.' and value is not None) :
                            hgmdColSplit = value.split("=")[0]
                            df.loc[index, hgmdColSplit] = value.split("=")[1]

                df.drop(columns=[nameColumb], inplace=True)      
                df.to_csv(file, sep='\t',index=False)
            
            elif 'id' in database and database['id'] == 'gnomAD':
                print("Split gnomAD columns...")
                df = pd.read_csv(file, sep="\t")              
                nameColumb = 'gnomAD.hg38_multianno.txt'
                # create a new column with the name of the new columns
                for nc in gnomADColumns:
                    df[nc] = '.'    # None charter for empty cells
                gnomAD_split = df[nameColumb].str.split(";", expand=True)
                
                for index, row in gnomAD_split.iterrows():
                    for value in row.dropna():  # Usa dropna per ignorare i valori NaN
                        if(value != '.' and value is not None) :
                            gnomADColSplit = value.split("=")[0]
                            if gnomADColSplit in gnomADColumns:
                                df.loc[index, gnomADColSplit] = value.split("=")[1]

                df.drop(columns=[nameColumb], inplace=True)      
                df.to_csv(file, sep='\t',index=False)
    print("Merging and Splitting columns complete!")


    
def scrapeGencode(scraping):
    url = 'https://www.gencodegenes.org/human/releases.html'
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr', class_="toggleable")
        for row in rows:
            cells = row.find_all('td', class_="center")
            if len(cells) > 1:
                link = cells[1].find('a')
                if link and version.parse(link.text) > version.parse(scraping[0]['release']) and (datetime.strptime(cells[3].text, "%m.%Y") > datetime.strptime(scraping[0]['date'], "%m.%Y")) and scraping[0]['genVersion'] in cells[4].text:
                    return True
                break
        else:
            return False
    else:
        print("Failed to retrieve content: ", response.status_code)
        os.system("python prepare.py")    

def scrapeClinvar(scraping):
    url = 'https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/'
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            if link.text == scraping[1]['name']:    
                if not link['href'].endswith('/'):
                    date = link.next_sibling.strip()
                    if date and " " in date:
                        date = date.split(" ")[0] 
                        if(datetime.strptime(date, "%Y-%m-%d") > datetime.strptime(scraping[1]['date'], "%Y-%m-%d")):
                            return True
                        else:
                            return False
    else:
        print("Failed to retrieve content: ", response.status_code)


def scrapeGnomad(scraping):
    try:
        url = 'https://gnomad.broadinstitute.org/news/category/release/'
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        last_article_title = soup.select('h2.article-title')[0].get_text().strip()
        version_number = last_article_title.split("v")[-1]   
        if(version.parse(version_number) > version.parse(scraping[2]['release'])):
            return True
        else:
            return False    
    except Exception as e:
        print("Failed to retrieve GnomAD content", e)
        return -1
    
def scrapeOMIM(scraping):
    url = 'https://www.omim.org/statistics/update'
    #baypass anti-bot
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.omim.org/'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        year = soup.find('table').find('tr').find_all('td')[0].get_text().strip()
        month = soup.find('table').find('tr').find_all('td')[-1]
        if month.find('a'):
            url = month.find('a')['href'] 
            month = url.split('/')[-1]
            remoteDate = date(int(year), int(month), 1)
            localDate = datetime.strptime(scraping[3]['date'], '%Y-%m-%d').date()
            if(remoteDate>localDate):
                return True
            else:
                url = f'https://www.omim.org/statistics/updates/{year}/{month}'                
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                # Trovare l'elemento h4 e ottenere il testo
                remoteLastDate = soup.find('h4').get_text().strip()
                cleanedRemote = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', remoteLastDate)
                remoteLastDate = datetime.strptime(cleanedRemote, "%B %d, %Y").date()
                if(remoteLastDate>localDate):
                    return True
                else:
                    return False
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error occurred: {e.response.status_code}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
        
def tabulateUpdates(scraping, gencode, clinvar, gnomad, omim):
    data = [
    [scraping[0]['id'], scraping[0]['date'] , scraping[0]['release'] , "[!]" if gencode else " "],
    [scraping[1]['id'], scraping[1]['date'], "/",  "[!]" if clinvar else " "],
    [scraping[2]['id'], "/", scraping[2]['release']  ,  "[!]" if gnomad else " "],
    [scraping[3]['id'], scraping[3]['date'] , "/",  "[!]" if omim else " "]
    ]
    headers = ["Database", "Date", "Version", "Update"]
    print(tabulate(data, headers=headers, tablefmt="fancy_grid"))
    
    
def load_config(config_path="config.yaml"):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config

conf = load_config()
db_path = conf["db_path"]
destination_path = conf["destination_path"]
scraping = conf["scraping"]
parser = argparse.ArgumentParser(description="Tool per l'annotazione di file VCF")
annotateVCF_group = parser.add_argument_group('option for --annotateVCF')
parser.add_argument("--annotateVCF", "-a",help="Annotate VCF file with VEP", action="store", metavar="PATH")
annotateVCF_group.add_argument("--DBPath", "-db", help="Database path for ANNOVAR", metavar="PATH DB", required=False)
annotateVCF_group.add_argument("--DestinationPath", "-d", help="Destination path for annotated files", metavar="PATH DEST", required=False)

parser.add_argument("--checkDB", "-c",help="Check if DB was updated", action="store_true")
parser.add_argument("--prepare", "-p",help="Prepare Databases", action="store_true")


args = parser.parse_args()

path = ""

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
        parser.error("Le opzioni -DBPath/-db e -DestinationPath/-d sono obbligatorie con --annotateVCF.")
        
# if exists all three paths
if os.path.exists(path) and os.path.exists(db_path) and os.path.exists(destination_path):
    if(conf['autoCheck']):
        tabulateUpdates(scraping, scrapeGencode(scraping), scrapeClinvar(scraping) , scrapeGnomad(scraping), scrapeOMIM(scraping))
    print(f"Processing {path}...")
    if os.path.isfile(path):
        #fileName = destination_path + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
        # ?txt version
        if 'databasesTXT' in conf and conf['databasesTXT']:
            for db in conf['databasesTXT']:
                fileName = destination_path + db['id']+'_' + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
                fileNameTemp = destination_path + "temp/" + db['id']
                os.system(f"perl table_annovar.pl {path} {db_path} -buildver hg38 -out {fileName} -remove -protocol {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                generateTemp(fileName, fileNameTemp)
        # ?vcf version
        if 'databasesVCF' in conf and conf['databasesVCF']:
            for db in conf['databasesVCF']:
                fileName = destination_path + db['id']+'_' + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
                fileNameTemp = destination_path + "temp/" + db['id']
                os.system(f"perl table_annovar.pl {path} {db_path} -buildver hg38 -argument '-infoasscore' -out {fileName} -remove -protocol vcf -vcfdbfile {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                generateTemp(fileName, fileNameTemp)
        # ?gff3 version
        if 'databasesGFF3' in conf and conf['databasesGFF3']:
            for db in conf['databasesGFF3']:
                fileName = destination_path + db['id']+'_' + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
                fileNameTemp = destination_path + "temp/" + db['id']
                os.system(f"perl table_annovar.pl {path} {db_path} -buildver hg38 -out {fileName} -remove -gff3dbfile {db['file']} -protocol gff3 -operation {db['operation']} -nastring . -vcfinput -polish")
                generateTemp(fileName, fileNameTemp)
        mergeColumns(path)
    elif os.path.isdir(path):
        for f in os.listdir(path):
            if f.endswith(".vcf"):
                full_file_path = os.path.join(path, f)
                if 'databasesTXT' in conf and conf['databasesTXT']:
                    for db in conf['databasesTXT']:
                        fileName = destination_path + db['id']+'_' + os.path.basename(f) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
                        fileNameTemp = destination_path + "temp/" + db['id']
                        os.system(f"perl table_annovar.pl {full_file_path} {db_path} -buildver hg38 -out {fileName}  -remove -protocol {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                        generateTemp(fileName, fileNameTemp)
                # ?vcf version
                if 'databasesVCF' in conf and conf['databasesVCF']:
                    for db in conf['databasesVCF']:
                        fileName = destination_path + db['id']+'_' + os.path.basename(f) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
                        fileNameTemp = destination_path + "temp/" + db['id']
                        os.system(f"perl table_annovar.pl {full_file_path} {db_path} -buildver hg38 -argument '-infoasscore' -out {fileName} -remove -protocol vcf -vcfdbfile {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                        generateTemp(fileName, fileNameTemp)
                # ?gff3 version
                if 'databasesGFF3' in conf and conf['databasesGFF3']:
                    for db in conf['databasesGFF3']:
                        fileName = destination_path + db['id']+'_' + os.path.basename(f) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
                        fileNameTemp = destination_path + "temp/" + db['id']
                        os.system(f"perl table_annovar.pl {full_file_path} {db_path} -buildver hg38 -out {fileName} -remove -gff3dbfile {db['file']} -protocol gff3 -operation {db['operation']} -nastring . -vcfinput -polish")
                        generateTemp(fileName, fileNameTemp)
                mergeColumns(f)
            else:
                print(f"Error: {f} is not a .vcf file")
    else:
        parser.error("Error: Not a valid file or directory")
elif args.checkDB:
    tabulateUpdates(scraping, scrapeGencode(scraping), scrapeClinvar(scraping), scrapeGnomad(scraping), scrapeOMIM(scraping))
elif args.prepare:
    prepare.prepare()
else:
    parser.error("Error: Invalid command line input. Please check your syntax or path and try again.")


