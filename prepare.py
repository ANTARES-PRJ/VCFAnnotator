def prepare_vcf():
    # Prepare HGMD
    with open('/path/to/your/vcf/file.vcf', 'r') as file:
        # Open a new file for writing the modified VCF data
        with open('/path/to/your/output/file.vcf', 'w') as output_file:
            for line in file:
                if line.startswith('#'):
                    output_file.write(line)
                    continue
                
                columns = line.split('\t')
                
                # Replace "<DEL>" with "." in the ALT column
                alt_column = columns[4].replace('<DEL>', '.')
                columns[4] = alt_column
                
                output_file.write('\t'.join(columns))

    print("String replacement complete!")

    # Convert Clinvar DB from VCF to TXT
    #TODO: ...