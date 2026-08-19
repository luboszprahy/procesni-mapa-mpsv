# package init

Initializes a directory with a new Dataverse package project

## Arguments

- `--outputDirectory` (`-o`) - Output directory
- `--package-name` - Sets the default name of the package. Applies to the generation of ImportExtension.GetNameOfImport.
- `--package-type` (`-pt`) - Type of package project to scaffold. Allowed values: dataverse, erp. Default: dataverse.
- `--model` (`-m`) - Name(s) of the X++ model(s) to scaffold. Accepts a single name or a comma-separated list (e.g. ModelA,ModelB). Required when --package-type is erp.
- `--source-root` (`-sr`) - Source root path (relative to output directory) where models will live. Default: ./src.
- `--publisher` (`-pub`) - Publisher name written into the model descriptor. Default: Microsoft.
- `--layer` (`-l`) - X++ layer. Allowed values: USR, CUS, VAR, SL1, SL2, SL3, BUS, HFX, GLS, DIS, ISV. Default: ISV.

