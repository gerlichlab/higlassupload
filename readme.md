# Installation


The script needs [clodius](https://github.com/higlass/clodius), which has a lot of requiremens. So the best way to install is to create a conda environment and install the most important requirements uisng conda and then install this pacakge into the conda environment via pip:

```pip install git+https://github.com/gerlichlab/higlassupload```

This will set up a command called ```higlassUp``` in your environment that is the entry point for usage of this script.

# Usage

At the moment the script can handle bedfiles (.bed extension), bedpe files (.bedpe extension),mcooler files (.mcool) and biwig files (.bw). It will recognize how to dispatch clodius based on the extension and then upload the resulting file to a higlass server. The login credentials need to be available as environment variabels with your username being stored in `HIGLASSUSER` and your password being stored in `HIGLASSPWD`.

On linux this can be done by:
```
export HIGLASSUSER=username
export HIGLASSPWD=supersecretpassword
```
Note: The username and your password should not contain `$` signs if you add it to your `.bashrc` file, since they will be interpreted by `bash`.

The upload command will then be the following:

```higlassUp file```

This will preprocess the file (if necessary) with clodius and upload to the default higlass instance using the filename as name. If you want to specify a different name:

```higlassUp --name TEST file```

If you want to specify a specific projet onto which to upload to file you can do it as follows:

```higlassUp --project PROJECT file```

Moreover, you can specify the genome assembly to be used for the specific file. Currently, assembly hg19 and hg38 are available. The specification is done as follows:

```higlassUp --assemblh hg19|hg38 file```

## Dockerhub container:
This tool can be found ready to use in our main container on [dockerhub](https://hub.docker.com/repository/docker/gerlichlab/scshic_docker).

# Defaults for Clodius

To automate the upload process, the chromsizes for hg19 in this repo will be used for all aggregation scripts. Moreover, .bedpe files need to have a certain format:

| chrom1  | start1 | end1 | chrom2 | start2 | end2 |
| ------------- | ------------- | ------------- | ------------- | ------------- | ------------- |
| chr2  | 1  | 2  | chr2  | 1  | 2  |

For rectangle domains , the .bedpe file needs to specify the upper left corner of the rectangle by (start1, start2) and the lower left corner by (end1, end2). So for rectangle domains centered on the diagonal, start1 = start2 and end1 = end2.
