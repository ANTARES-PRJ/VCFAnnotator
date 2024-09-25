# VCFAnnotator

VCFAnnotator is a wrapper tool for the ANNOVAR software, which enables batch processing of VCF files for DNA genome annotation, comparing various biomedical databases containing scientific notations.
This tool can annotate an entire folder of VCF files in a single command and can convert and adapt databases to be compatible with ANNOVAR.
Additionally, it can check for database updates by scraping their own websites.

The tool has been tested by using the following databases: GnomAD, ClinVar, GENCODE, HGMD, OMIM.

Our tool automatically implements a merge of the output files, so that all the annotations performed for each DB, even in different formats (.txt, .vcf, .gff3), are available in a single file. This is not possible with the stock ANNOVAR software, where each format will lead to a single file.

## Prerequisites

- Python
- Perl
- ANNOVAR (https://annovar.openbioinformatics.org/en/latest/user-guide/download/). We provide a modified version of some ANNOVAR files, to solve some of its limitations.

## Installation

To install the tool, simply clone the repository and install the required dependencies:

```
git clone https://github.com/ANTARES-PRJ/VCFAnnotator.git
cd VCFAnnotator
```


## Configuration

The tool uses a YAML configuration file named `config.yaml` to specify the default paths for the database and the destination folder for the annotated VCF files. You can modify these paths to suit your needs. Please note that the final `/` character must be inserted.

In the following section, databases needed for annotation should be inserted into their respective lists (databasesTXT, databasesVCF, databasesGFF3) according to the database format. The Python code will automatically recognize the quantity and extension, and perform annotation autonomously using the provided databases.

There are two fields to fill in for each database:
- `id` to differentiate it from others;
- `file` is the name of the database file;
- `operation` indicates the type of operation with which you want to use the specific database (*the following values can be used as operation:
g means gene-based, gx means gene-based with cross-reference annotation, r means region-based and f means filter-based*)

Here's how to specify the value of the file for each type:
- **databasesTXT**: Write the file name without extension and the Human genome reference hg38.
Example: `file = "clinvar"` will refer to hg38_clinvar.txt.
- **databasesVCF** and **databasesGFF3**: Specify the full file name with the Human genome reference (hg38_, ...) and the extension.
Example: `file: "hg38_gnomad.vcf"` or `file: "hg38_hgmd.gff3"`.

In the **Prepare DB** section, you need to indicate the paths of the databases to be modified with the `--prepare` command to remove the DEL, convert from .vcf to .txt, and clean the databases from comments (#).

In the last section of the configuration file config.yaml, there is a **Scraping section** where the user must insert, and constantly update, the latest version of the DBs in order to always be notified in case there are new updates on the sites.

For each DB, you need to insert in the changes of the scraping list: `release`, `date` or `genVersion` as indicated in the file. In this way, all the necessary variables are provided to perform a DB update check.

There is also a boolean variable `autoCheck` to automatically request the verification of updates for the above mentioned databases when annotating one or more VCF files.

## Usage

### Check Update DB

To check for DB updates, just use the `--checkDB` (`-c`) option to print a table where updates are indicated with a `[!]`.
If you download the new databases, you need to update the config file with the new information required by the "scraping" list,in this way, the web scraping update check will work correctly. Here's how you can do it:
```
python annovar_tool.py --checkDB
``` 

### Prepare DB
If you have downloaded the new databases, you will need to prepare them to be used correctly by Annovar for annotation.

You should use the `--prepare` command.
```
python annovar_tool.py --prepare
```

### Annotate VCF file

To annotate a VCF file, simply run the tool with the `--annotateVCF` (`-a`) option and specify the path to the VCF file. 
```
python annovar_tool.py --annotateVCF /path/to/input.vcf
```

You can also specify the database path and destination path using the `--DBPath` (`-db`) and `--DestinationPath` (`-d`) options, respectively.
Please insert `/` at the end of the path.

Here's an example command:

```
python annovar_tool.py --annotateVCF /path/to/input.vcf --DBPath /path/to/database/ --DestinationPath /path/to/output_folder/
```

If you don't specify the database path and destination path, the tool will use the default paths specified in the `config.yaml` file.

If you change the default paths within `config.yaml`, remember to put the "/" character at the end of the folder path.

The results of the annotation of one or more VCF files, for each individual Database, will be available in the `destination_path` folder named as follows:

*`DBName_VCFInputName_YYYY-mm-dd_HH_MM_SS(.avinput/.txt/.vcf)`*

Available in all three output formats of Annovar, namely: avinput, txt, and vcf.

In addition, for each annotation, a unique .txt file is also generated for all the DBs with which you wanted to annotate, and it will be named:

*`VCFInputName_result_YYYY-mm-dd_HH_MM_SS.txt`*

It will gather all the annotations into a single file, adding a column for each DB, called as the same, to differentiate the various annotations.

For the Clinvar hgmd, GenomAD and Omim annotations, we have made sure to **divide** the annotation into **different columns**


## Step-by-Step Explanation of the Code

Here's a step-by-step explanation of the code:

1. **Load the configuration file:** The tool starts by loading the configuration file `config.yaml` using the `load_config()` function. This function reads the YAML file and returns a dictionary containing the configuration options.

2. **Parse the command-line arguments:** The tool then parses the command-line arguments using the `argparse` module. It defines two groups of arguments: one for the `--annotateVCF` option and one for the `--DBPath` and `--DestinationPath` options.

    Add another argument group for the `--checkDB` option

3. **Annotate Files:** Check if the `--annotateVCF` argument was provided. If it was, set the VCF file path. If `--DBPath` and `--DestinationPath` were also provided, set these paths as well.

    Check if all three paths exist. If they do, proceed with annotating the VCF file using the ANNOVAR database. The annotation is performed using ANNOVAR's table_annovar.pl command, which is run as a system command.

    If the path is a directory, iterate over all files in the directory. If the file is a VCF file, perform the annotation as above.

4. **Check Update:** If the `--checkDB` option was provided, the functions that perform scraping for each DB site will be executed, and the `tabulateUpdates` function prints a table in the command line. When `autoCheck` is true, they are automatically executed without `--checkDB` but with any annotation command `--annotateVCF`.

5. **Merge:** When the annotation files for each DB are created, copies are also created in `result/temp/`, where the files with .txt extension will be read to extract the column of interest, the annotation column, and they will all be concatenated at the end in a final merge .txt file. In the end, the temporary folder is deleted.

6. **Split Columns:** If the HGMD id is present in the config.yaml file then it means that there will be a column in the file obtained from the merge of DBs (previous step), new columns will be created, initially filled with the None “.” character, then by cycling all rows in the column `HGMD.hg38_multiyear.txt` the correct values in the respective row/column will be substituted by performing a stand for “;” and “=”.
The new columns are as follows:
`['CLASS', 'MUT', 'GENE', 'STRAND', 'DNA', 'PROT', 'DB', 'PHEN', 'RANKSCORE', 'SVTYPE', 'END', 'SVLEN']`
are taken from the 2024/01 HGMD DB, if there are more columns in the new DBs just add them to this list called `HGMDColumns` in the `annorar_tool.py` file.
    The same thing is done for the GnomAD DB, of which only the columns `['AC', 'AN', 'AF']` will be kept. These columns are stored in a variable `gnomADColumns`. If necessary, you can increase the number of columns by adding the name of the columns to be kept in the `gnomADColumns` variable.

7. **Prepare:** A database preparation procedure is executed with the  `--prepare` command. This will perform thee main functions:
    
    Convert the Clinvar DB from .VCF to .TXT, thus bypassing some reading errors by Annovar;
    
    Automatic replacement of the error string "" with "." in the ALT column of the HGMD DB, this because Annovar recognizes the character "." as a missing value and not other characters;
    
    Another operation is remove comments, *e.g. #version 4.1 ...*, in the .txt format DB file, Omim and Clinvar, leaving only the header line starting with #. The paths of these original DBs must be reported in the appropriate section of config.yaml. The result of the conversion will be saved in  `db_path`.



## Link and References

 You can follow the instructions in the Annovar documentation to download and set up the database. Here's the link to the Annovar download page:
 https://annovar.openbioinformatics.org/en/latest/user-guide/download/.
