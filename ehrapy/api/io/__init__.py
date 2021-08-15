from pathlib import Path
from typing import List, Optional, Union

from anndata import AnnData

from ehrapy.api.io.read import DataReader
from ehrapy.api.io.write import DataWriter


def read(
    filename: Union[Path, str],
    extension: Optional[str] = None,
    delimiter: Optional[str] = None,
    index_column: Union[str, Optional[int]] = None,
    columns_obs_only: Optional[List[Union[str]]] = None,
    cache: bool = False,
    backup_url: Optional[str] = None,
    suppress_warnings: bool = False,
) -> AnnData:
    """Read file and return :class:`~anndata.AnnData` object.

    To speed up reading, consider passing ``cache=True``, which creates an hdf5 cache file.

    Parameters:
         filename
             Name of the input file to read

         extension
             Extension that indicates the file type. If ``None``, uses extension of filename.

         delimiter
             Delimiter that separates data within text file. If ``None``, will split at arbitrary number of white spaces,
             which is different from enforcing splitting at any single white space ``' '``.

         index_column
             Name or Index of the column that should be set as index (obs_names in later :class:`~anndata.AnnData` object)
             If the a string was passed, the so called column is set as index, if it is an integer, the column at that index is set as index.
             If None was passed, the column at index 0 will be examined if it is the "patient_id" column. If not, a warning will be raised.

         columns_obs_only
             If passed, this list contains the name of columns that should be excluded from X, but stored in obs. This may be useful for columns
             that contain free text information, which may not be useful to perform some algorithms and tools on.

         cache
             If `False`, read from source, if `True`, read from fast 'h5ad' cache.

         backup_url
             Retrieve the file from an URL if not present on disk.

         suppress_warnings
             Whether to suppress warnings or not

    Returns:
         An :class:`~anndata.AnnData` object
    """
    return DataReader.read(
        filename, extension, delimiter, index_column, columns_obs_only, cache, backup_url, suppress_warnings
    )
