import yaml

def load_config(config_path="config.yaml"):
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config
conf = load_config()



# Prepare HGMD
for p in conf['prepare']:
    with open(p['path'], 'r', encoding='utf-8') as file:
        nome = p['path'].split('/')[-1].split('.')[0]
        # Open a new file for writing the modified VCF data
        with open(f'result/{nome}.txt', 'w', encoding='utf-8') as output_file:
            for line in file:
                if line.startswith('#'):
                    output_file.write(line)
                    continue
                
                columns = line.split('\t')
                
                # Replace "<DEL>" with "." in the ALT column
                alt_column = columns[4].replace('<DEL>', '.')
                columns[4] = alt_column
                
                output_file.write('\t'.join(columns))

print("String \"<DEL>\" replacement complete!")

# Convert Clinvar DB from VCF to TXT
#TODO: ...