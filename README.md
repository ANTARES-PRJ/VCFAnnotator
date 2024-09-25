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

Here's how to specify the value for the `file` parameter for each type:
- **databasesTXT**: Write the file name without extension and the Human genome reference hg38.
Example: `file = "clinvar"` will refer to hg38_clinvar.txt.
- **databasesVCF** and **databasesGFF3**: Specify the full file name with the Human genome reference (hg38_, ...), if available in the name, and the extension.
Example: `file: "hg38_gnomad.vcf"` or `file: "hg38_hgmd.gff3"`.

In the **Prepare DB** section, you need to indicate the `id` of the databases to be modified with the `--prepare` command to remove the DEL, convert from .vcf to .txt, and clean the databases from comments (#).

In the last section of the configuration file config.yaml, there is a **Scraping section** where the user must insert, and constantly update, the latest version of the DBs in order to be always notified in case there are new updates on the databases' websites.

For each DB, you need to insert the information of the scraping list: `release` or `date` as indicated in the file. In this way, all the necessary variables are provided to perform a DB update check.
Additionally, you need to specify the `website` to be scraped, the HTML `tag` containing the version information, and the possible `textToSearch` in that tag.

There is also a boolean variable `autoCheck` to automatically request the verification of updates for the above-mentioned databases when annotating one or more VCF files.

## Usage

### Set-up

In this section, we report how to setup the tool, in order to be used in practice.

- Clone the VCFAnnotator tool
- Download ANNOVAR from https://annovar.openbioinformatics.org/en/latest/user-guide/download/
- Extract ANNOVAR files in the same folder where files coming from VCFAnnotator are
- Substitute the `annotate_variation.pl` file with that provided in our repository
- Download the databases in the folder specified in the `db_path` property of the `config.yaml` file.

In the following, we report the specific files to be used for the database we tested.

- **OMIM**: Ask for the link to OMIM (https://www.omim.org/downloads). The required file for annotation is `genemap2.txt` and it should be renamed in `hg38_genemap2.txt` (if no change is made to the current `config.yaml` file)
- **Clinvar**: Download the file from https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/. The required file for annotation is `clinvar_yyyymmdd.vcf.gz` and, after being extracted, it should be renamed in `hg38_clinvar.vcf` (if no change is made to the current `config.yaml` file)
- **HGMD**: We cannot give the file, as it is subscription-only. Please, ask HGMD owners for your own copy. In our experiments, we used the file named `HGMD_Pro_2024.1_hg38.vcf`
- **gnomAD**: Download the files you are interested in from https://gnomad.broadinstitute.org/downloads.
- **Gencode**: Download the GFF3 file from https://www.gencodegenes.org/human/ 

### Check Update DB

To check for DB updates, just use the `--checkDB` (`-c`) option to print a table where updates are indicated with a `[!]`.
If you download the new databases, you need to update the config file with the new information required by the "scraping" list, in this way, the web scraping update check will work correctly. Here's how you can do it:
```
python annovar_tool.py --checkDB
``` 

### Prepare DB
If you have downloaded the new databases, you will need to prepare them to be used correctly by ANNOVAR for annotation.

You should use the `--prepare` command.
```
python annovar_tool.py --prepare
```

### Annotate VCF file

To annotate a VCF file, simply run the tool with the `--annotateVCF` (`-a`) option and specify the path to the VCF file. 
```
python annovar_tool.py --annotateVCF /path/to/input.vcf
```

You can also specify the database path and destination path using the `--DBPath` (`-db`) and `--DestinationPath` (`-d`) options, respectively, if those specified by the `config.yaml` file are different from those you want to use for this single annotation.
Please insert `/` at the end of the path.

Here's an example command:

```
python annovar_tool.py --annotateVCF /path/to/input.vcf --DBPath /path/to/database/ --DestinationPath /path/to/output_folder/
```

If you don't specify the database path and destination path, the tool will use the default paths specified in the `config.yaml` file.

If you change the default paths within `config.yaml`, remember to put the "/" character at the end of the folder path.

The results of the annotation of one or more VCF files, for each individual database, will be available in the `destination_path` folder named as follows:

*`DBName_VCFInputName_YYYY-mm-dd_HH_MM_SS(.avinput/.txt/.vcf)`*

Available in all three output formats of Annovar, namely: avinput, txt, and vcf.

In addition, for each annotation, a unique .txt file is also generated for all the DBs with which you wanted to annotate, and it will be named:

*`VCFInputName_result_YYYY-mm-dd_HH_MM_SS.txt`*

It will gather all the annotations into a single file, adding a column for each DB, called as the same, to differentiate the various annotations.

For the Clinvar hgmd, GenomAD and Omim annotations, we have made sure to **divide** the annotation into **different columns**

## Link and References

 You can follow the instructions in the Annovar documentation to download and set up the database. Here's the link to the Annovar download page:
 https://annovar.openbioinformatics.org/en/latest/user-guide/download/.
