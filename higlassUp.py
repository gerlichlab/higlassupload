"""Command line interface for HiGlass-upload and preprocessing"""
import click
import subprocess
import logging
import tempfile
import random
import shlex
import os
import sys

# define filetype mapping
FILETYPES = {".bed": "bedfile",
             ".mcool": "mcoolfile",
             ".bedpe": "bedpe",
             ".bw": "bigwig",
             ".bigwig": "bigwig"}
# Define chromsizes filenames
CHROMSIZES = {"hg19": "hg19.chrom.sizes",
              "hg38": "hg38.chrom.sizes",
              "mm9": "mm9.chrom.sizes"}
# define Clodius templates
CLODIUSTEMPLATES = {
    "bedfile": "clodius aggregate bedfile --chromsizes-filename {} -o {} {}",
    "bedpe": "clodius aggregate bedpe --chromsizes-filename {}\
                                      --chr1-col 1 --from1-col 2 --to1-col 3 \
                                      --chr2-col 4 --from2-col 5 --to2-col 6 \
                                      --output-file {} {}"}
# define CLODIUS extensions
CLODIUSEXTENSIONS = {"bedfile": "beddb",
                     "bedpe": "bed2ddb",
                     "mcoolfile": "cooler",
                     "bigwig": "bigwig"}
# define upload template
UPLOADTEMPLATE = 'curl -u {}:{}\
                    -F "datafile=@{}"\
                    -F "filetype={}"\
                    -F "datatype={}"\
                    -F "coordSystem={}"\
                    -F "name={}"\
                    -F "project={}"\
                    --verbose {}'
# Higlass datatypes
DATATYPES = {"bedfile": "bedlike",
             "bedpe": "2d-rectangle-domains",
             "mcoolfile": "matrix",
             "bigwig": "vector"}


def parseFile(filep):
    """Decides which filetype the filepath
    points to based on the file-ending"""
    extension = os.path.splitext(filep)[-1]
    return FILETYPES.get(extension, None)


def aggregateFile(filep, fileType, chromsizes):
    """runs Clodius on the fileType, if that is necessary.
    If clodius ran, the path to the tempfile if returned, if not,
    the original file path is returned."""
    # Note: at this stage it is assumed that if there is no clodius command
    # that the file can be directly uploaded
    commandTemplate = CLODIUSTEMPLATES.get(fileType, None)
    if commandTemplate is None:
        return filep
    logging.info(" Aggregating file...")
    # create tempfile
    hashVal = random.getrandbits(128)
    tempPath = os.path.join(
        tempfile.mkdtemp(), f'{hex(hashVal)[2:]}.{CLODIUSEXTENSIONS[fileType]}')
    # fill in command
    command = commandTemplate.format(chromsizes, tempPath, filep)
    # print command for logging
    logging.debug(f"Clodius command: {command}")
    # dispatch command
    process = subprocess.run(shlex.split(
        command), check=False, capture_output=True)
    # check whether command completed succesfully
    if process.returncode != 0:
        for line in process.stderr.decode("UTF-8").split("\n"):
            logging.error(line)
            logging.error("\n\n")
        for line in process.stdout.decode("UTF-8").split("\n"):
            logging.error(line)
            logging.error("\n\n")
        raise subprocess.CalledProcessError(process.returncode, command)
    else:
        for line in process.stdout.decode("UTF-8").split("\n"):
            logging.debug(line)
    return tempPath


def uploadFile(tempFile, fileType, server, name, project, assembly, username, password):
    """takes a file and uploads
    it to the higlass server"""
    # stitch together upload script
    uploadCommand = UPLOADTEMPLATE.format(username, password,
                                          tempFile, CLODIUSEXTENSIONS[fileType],
                                          DATATYPES[fileType],
                                          assembly,
                                          name,
                                          project,
                                          server)
    logging.debug(uploadCommand)
    # dispatch command
    process = subprocess.run(shlex.split(uploadCommand),
                             check=True, capture_output=True)
    if process.returncode != 0:
        for line in process.stderr.decode("UTF-8").split("\n"):
            logging.error(line)
            logging.error("\n\n")
            raise subprocess.CalledProcessError(process.returncode, uploadCommand)
    # TODO check whether upload actually succeeded, curl will return with error code 0 if for example the project id did not exit
    else:
        for line in process.stdout.decode("UTF-8").split("\n"):
            logging.debug(line)


@click.command()
@click.option('--higlass', '-h', 'server', default="https://gerlich.higlass.vbc.ac.at/api/v1/tilesets/",
              help='Path to HiGlass Server',
              show_default=True)
# TODO At the moment, specifying another server would not work because the login would fail in the template...
@click.option('--name', '-n', 'name', default=None,
              help='Name to be shown for the specific file on Higlass',
              show_default=True)
@click.option('--project', '-p', 'project', default="Misc",
              help='Project on Higlass that the file should be assigned to. This needs to be the uuid of the project!',
              show_default=True)
@click.option('-v', 'verbose', is_flag=True,
              help='Verbose mode',
              show_default=True)
@click.option('--assembly', '-a', 'assembly', default="hg19", type=click.Choice(['hg19', 'hg38', 'mm9'], case_sensitive=False),
                help="Assembly that was used to generate the data to be uploaded.")
@click.option('--username', prompt=False,
             default=lambda: os.environ.get("HIGLASSUSER", ""))
@click.option('--password', prompt=False, hide_input=True,
             default=lambda: os.environ.get("HIGLASSPWD", ""))
@click.argument('fileP', type=click.Path(exists=True))
def main(filep, name, server, verbose, project, assembly, username, password):
    # set logging level
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    # set name to filepath if it is not defined
    if name is None:
        name = filep
    # Parse filetype
    filetype = parseFile(filep)
    if filetype is None:
        raise ValueError(
            f"Filetype '{os.path.splitext(filep)[-1]}' is not implemented!")
    # handle chromsizes selection
    chromsizes = os.path.join(sys.prefix, CHROMSIZES[assembly])
    # run clodius
    tempFile = aggregateFile(filep, filetype, chromsizes)
    logging.info(" Uploading file...")
    # upload file
    uploadFile(tempFile, filetype, server, name, project, assembly, username, password)
    logging.info(" Upload complete!")