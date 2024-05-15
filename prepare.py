import yaml
import pandas as pd
import os
import shutil

def load_config(config_path="config.yaml"):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config

def parse_detailed_vcf_line(line):
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

conf = load_config()

def prepareHGMD():
    for p in conf['removeDEL']:
    #duplicate a file
        name = p['path'].split('/')[-1].split('.')[0]
        dest = conf['db_path'] + "temp/"
        if not os.path.exists(dest):
            os.makedirs(dest)
        shutil.copy(p['path'], dest+name+".vcf")
            
        with open(dest+name+".vcf", 'r', encoding='utf-8') as file:
            # Open a new file for writing the modified VCF data
            with open(f"{conf['db_path']}{name}.vcf", 'w', encoding='utf-8') as output_file:
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
        
# Convert Clinvar DB from VCF to TXT
def prepareClinvar():
    detailed_format_lines = []
    file_path = conf['pathClinvar']
    name = conf['pathClinvar'].split('/')[-1].split('.')[0]
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#'):  
                continue
            parsed_line = parse_detailed_vcf_line(line)
            if parsed_line:  
                detailed_format_lines.append(parsed_line)

    detailed_annovar_df = pd.DataFrame(detailed_format_lines, columns=['#Chr', 'Start', 'End', 'Ref', 'Alt', 'CLNALLELEID', 'CLNDN', 'CLNDISDB', 'CLNREVSTAT', 'CLNSIG'])
    #Chr	Start	End	Ref	Alt	CLNALLELEID	CLNDN	CLNDISDB	CLNREVSTAT	CLNSIG

    output_file_path_detailed = f"{conf['db_path']}{name}.txt"  
    detailed_annovar_df.to_csv(output_file_path_detailed, sep='\t', index=False, header=True)
    print("Prepare Clinvar - Format converted from vcf to txt!")
    
def prepareOMIM():
    # Remove All # comment exclude the "#Chr ..." line
    for p in conf['clean']:
        #duplicate a file
        name = p['path'].split('/')[-1].split('.')[0]
        dest = conf['db_path'] + "temp/"
        if not os.path.exists(dest):
            os.makedirs(dest)
        shutil.copy(p['path'], dest+name+".txt")
            
        with open(dest+name+".txt", 'r', encoding='utf-8') as file:
            # Open a new file for writing the modified VCF data
            with open(f"{conf['db_path']}{name}.txt", 'w', encoding='utf-8') as output_file:
                for line in file:
                    if line.startswith('#'):
                        # identify the header string if it starts with one of the following strings
                        if line.startswith(('# Chromosome\t', '#Chromosome\t', '# Chr\t', '#Chr\t', '# CHROM\t', '#CHROM\t')):
                            output_file.write(line)
                        continue
                    output_file.write(line)
        shutil.rmtree(dest)
        print(f"Prepare {p['id']} - Cleaner complete!")


def prepare():
    prepareHGMD()
    prepareClinvar()
    prepareOMIM()
