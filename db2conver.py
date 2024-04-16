import pandas as pd

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

detailed_format_lines = []

file_path = '/Users/simoneronzoni/Documents/Projects/tesi/Annovar-Tool/humandb/hg38_clinvar.vcf' 
with open(file_path, 'r') as file:
    for line in file:
        if line.startswith('#'):  
            continue
        parsed_line = parse_detailed_vcf_line(line)
        if parsed_line:  
            detailed_format_lines.append(parsed_line)

detailed_annovar_df = pd.DataFrame(detailed_format_lines, columns=['#Chr', 'Start', 'End', 'Ref', 'Alt', 'CLNALLELEID', 'CLNDN', 'CLNDISDB', 'CLNREVSTAT', 'CLNSIG'])
#Chr	Start	End	Ref	Alt	CLNALLELEID	CLNDN	CLNDISDB	CLNREVSTAT	CLNSIG

output_file_path_detailed = 'fileConverted.txt'  
detailed_annovar_df.to_csv(output_file_path_detailed, sep='\t', index=False, header=True)
