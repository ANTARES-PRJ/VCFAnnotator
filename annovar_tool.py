import os
import argparse
from datetime import datetime
import yaml
import requests 
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def scrapeGencode(scraping):
# URL della pagina
    url = 'https://www.gencodegenes.org/human/releases.html'

    # Effettua la richiesta HTTP al sito web
    response = requests.get(url)

    # Assicuriamoci che la richiesta sia andata a buon fine
    if response.status_code == 200:
        # Utilizza BeautifulSoup per analizzare il contenuto HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Trova tutte le righe della tabella che potrebbero contenere le informazioni delle release
        rows = soup.find_all('tr', class_="toggleable")
        
        for row in rows:
            cells = row.find_all('td', class_="center")
            # Assicurati che ci siano abbastanza celle per evitare errori
            if len(cells) > 1:
                link = cells[1].find('a')
                if link and link.text > scraping[0]['release'] and (datetime.strptime(cells[3].text, "%m.%Y") > datetime.strptime(scraping[0]['data'], "%m.%Y")) and scraping[0]['genVersion'] in cells[4].text:
                    return True
                break
        else:
            return False
    else:
        print("Failed to retrieve content: ", response.status_code)


def scrapeClinvar(scraping):
    url = 'https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/'
    # Effettua la richiesta HTTP al sito web
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            if link.text == scraping[1]['name']:    
                if not link['href'].endswith('/'):
                    date = link.next_sibling.strip()
                    if date and " " in date:
                        date = date.split(" ")[0] 
                        if(datetime.strptime(date, "%Y-%m-%d") > datetime.strptime(scraping[1]['data'], "%Y-%m-%d")):
                            return True
                        else:
                            return False
    else:
        print("Failed to retrieve content: ", response.status_code)

#TODO: verify if is possible to scrape the page with selenium because must be have a chrome driver installed

def seleniumScrape():
# Setup del WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # Vai alla pagina web
    driver.get('https://gnomad.broadinstitute.org/')

    # Aspetta che il JavaScript carichi il contenuto, puoi aumentare il tempo se necessario
    driver.implicitly_wait(10)  # aspetta 10 secondi

    # Ora puoi usare BeautifulSoup per analizzare la pagina
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Trova gli elementi desiderati, per esempio, estraendo testo o attributi
    elements = soup.select('select.Select-sc-1lkyg9e-0')

    # Esempio di stampa dei risultati
    for element in elements:
        for select in element.find_all('select.Select-sc-1lkyg9e-0'):
            print(select.text.strip())
    driver.quit()

    
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

checkDB_group = parser.add_argument_group('option for --checkDB')
parser.add_argument("--checkDB", "-c",help="Check if DB was updated", action="store_true")

args = parser.parse_args()

path = ""

if args.annotateVCF:
    path = args.annotateVCF
    if args.DBPath:
        db_path = args.DBPath
    if args.DestinationPath:
        destination_path = args.DestinationPath
else:
    if args.DBPath or args.DestinationPath:
        parser.error("Le opzioni -DBPath/-db e -DestinationPath/-d sono obbligatorie con --annotateVCF.")
        
# if exists all three paths
if os.path.exists(path) and os.path.exists(db_path) and os.path.exists(destination_path):
    print(f"Processing {path}...")
    if os.path.isfile(path):
        #fileName = destination_path + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
        # ?txt version
        if 'databasesTXT' in conf and conf['databasesTXT']:
            for db in conf['databasesTXT']:
                os.system(f"perl table_annovar.pl {path} {db_path} -buildver hg38 -out {destination_path + db['id']+'_' + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')} -remove -protocol {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                #path = fileName
        # ?vcf version
        if 'databasesVCF' in conf and conf['databasesVCF']:
            for db in conf['databasesVCF']:
                os.system(f"perl table_annovar.pl {path} {db_path} -buildver hg38 -argument '-infoasscore' -out {destination_path + db['id']+'_' + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')} -remove -protocol vcf -vcfdbfile {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                #path = fileName
        # ?gff3 version
        if 'databasesGFF3' in conf and conf['databasesGFF3']:
            for db in conf['databasesGFF3']:
                os.system(f"perl table_annovar.pl {path} {db_path} -buildver hg38 -out {destination_path + db['id']+'_' + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')} -remove -gff3dbfile {db['file']} -protocol gff3 -operation {db['operation']} -nastring . -vcfinput -polish")
                #path = fileName
    elif os.path.isdir(path):
        for f in os.listdir(path):
            if f.endswith(".vcf"):
                full_file_path = os.path.join(path, f)
                #fileName = destination_path + os.path.basename(f) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
                if 'databasesTXT' in conf and conf['databasesTXT']:
                    for db in conf['databasesTXT']:
                        os.system(f"perl table_annovar.pl {full_file_path} {db_path} -buildver hg38 -out {destination_path + db['id']+'_' + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')} -remove -protocol {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                        #full_file_path = fileName
                # ?vcf version
                if 'databasesVCF' in conf and conf['databasesVCF']:
                    for db in conf['databasesVCF']:
                        os.system(f"perl table_annovar.pl {full_file_path} {db_path} -buildver hg38 -argument '-infoasscore' -out {destination_path + db['id']+'_' + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')} -remove -protocol vcf -vcfdbfile {db['file']} -operation {db['operation']} -nastring . -vcfinput -polish")
                        #full_file_path = fileName
                # ?gff3 version
                if 'databasesGFF3' in conf and conf['databasesGFF3']:
                    for db in conf['databasesGFF3']:
                        os.system(f"perl table_annovar.pl {full_file_path} {db_path} -buildver hg38 -out {destination_path + db['id']+'_' + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')} -remove -gff3dbfile {db['file']} -protocol gff3 -operation {db['operation']} -nastring . -vcfinput -polish")
                        #full_file_path = fileName
            else:
                print(f"Error: {f} is not a .vcf file")
    else:
        parser.error("Error: Not a valid file or directory")
elif checkDB_group:
    gencode=scrapeGencode(scraping)
    clinvar = scrapeClinvar(scraping)   
    #seleniumScrape()
    
else:
    parser.error("Path not found")
