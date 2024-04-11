# Annovar-Tool

We have developed a tool for the Annovar software, which enables batch processing of VCF files for DNA genome annotation, comparing various databases and scientific notations.
Using the following databases: GnomAD, ClinVar, GENCODE, HGMD, OMIM.

Upcoming implementations:
Checking for more recent versions of the databases used (database links...)
TO DO


## Prerequisites

- Python
- Perl
- ANNOVAR (https://annovar.openbioinformatics.org/en/latest/user-guide/download/)


## Installation

To install the tool, simply clone the repository and install the required dependencies:

```
git clone https://github.com/YourGithub/annovar_tool.git
cd annovar_tool
```


## Configuration

The tool uses a YAML configuration file named `config.yaml` to specify the default paths for the database and the destination folder for the annotated VCF files. You can modify these paths to suit your needs.

In the following section, databases needed for annotation should be inserted into their respective lists (databasesTXT, databasesVCF, databasesGFF3) according to the database format. The Python code will automatically recognize the quantity and extension, and perform annotation autonomously using the provided databases.

There are two fields to fill in for each database: id (to differentiate it from others) and file (the name of the database file). Here's how to specify the value of file for each type:

- **databasesTXT**: Write the file name without extension and the Human genome reference hg38.
Example: `file = "clinvar"` will refer to hg38_clinvar.txt.
- **databasesVCF** and **databasesGFF3**: Specify the full file name with the Human genome reference (hg38_, ...) and the extension.
Example: `file: "hg38_gnomad.vcf"` or `file: "hg38_hgmd.gff3"`.


## Usage

To annotate a VCF file, simply run the tool with the `--annotateVCF` (`-a`) option and specify the path to the VCF file. You can also specify the database path and destination path using the `--DBPath` (`-db`) and `--DestinationPath` (`-d`) options, respectively.

Here's an example command:

```
python annovar_tool.py --annotateVCF path/to/input.vcf --DBPath path/to/database --DestinationPath path/to/output_folder
```

If you don't specify the database path and destination path, the tool will use the default paths specified in the `config.yaml` file.


## Step-by-Step Explanation of the Code

Here's a step-by-step explanation of the code:

1. **Load the configuration file:** The tool starts by loading the configuration file `config.yaml` using the `load_config()` function. This function reads the YAML file and returns a dictionary containing the configuration options.

2. **Parse the command-line arguments:** The tool then parses the command-line arguments using the `argparse` module. It defines two groups of arguments: one for the `--annotateVCF` option and one for the `--DBPath` and `--DestinationPath` options.

3. ****...


## Link and References

 You can follow the instructions in the Annovar documentation to download and set up the database. Here's the link to the Annovar download page:
 https://annovar.openbioinformatics.org/en/latest/user-guide/download/.