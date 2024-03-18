import os
import argparse
from datetime import datetime
import yaml

def load_config(config_path="config.yaml"):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config

# Carica le configurazioni predefinite dal file YAML
conf = load_config()
db_path = conf["db_path"]
destination_path = conf["destination_path"]

parser = argparse.ArgumentParser(description="Tool per l'annotazione di file VCF")
annotateVCF_group = parser.add_argument_group('option for --annotateVCF')
parser.add_argument("--annotateVCF", "-a", help="Annotate VCF file with VEP", action="store", metavar="PATH")
# Aggiunge -DBPath e -DestinationPath al gruppo di argomenti specifici per --annotateVCF
annotateVCF_group.add_argument("--DBPath", "-db", help="Database path for ANNOVAR", metavar="PATH DB", required=False)
annotateVCF_group.add_argument("--DestinationPath", "-d", help="Destination path for annotated files", metavar="PATH DEST", required=False)

args = parser.parse_args()

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
        os.system(f"perl table_annovar.pl {path} {db_path} -buildver hg19 -out {destination_path + os.path.basename(path) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')} -remove -protocol refGene,cytoBand,exac03,avsnp147,dbnsfp30a -operation g,r,f,f,f -nastring . -vcfinput -polish")
    elif os.path.isdir(path):
        for f in os.listdir(path):
            if f.endswith(".vcf"):
                full_file_path = os.path.join(path, f)
                os.system(f"perl table_annovar.pl {full_file_path} {db_path} -buildver hg19 -out {destination_path + os.path.basename(f) + '_' + datetime.now().strftime('%Y-%m-%d_%H_%M_%S')} -remove -protocol refGene,cytoBand,exac03,avsnp147,dbnsfp30a -operation g,r,f,f,f -nastring . -vcfinput -polish")
            else:
                print(f"Error: {f} is not a .vcf file")
    else:
        print("Error: Not a valid file or directory")
else:
    print("Error: Path not found")
    