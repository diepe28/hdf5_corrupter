# hdf5_corrupter
This tool takes an HDF5 file and tries to corrupts values with a fixed probability. 

The ussage of the tool is as follows:
>\>python3 hdf5_corrupter.py *arguments*  

Where the possible arguments are:  
 - -h | -help, optional argument, prints the ussage of the tool
 - -c | -configFile "path/to/config.yaml", mandatory argument (unless used with -h)
 - -p | -printOnly, optional argument, prints the contents of the hdf5 file specified at the config file

The .yaml configuration file must have the following entries:
- *hdf5_file*, the path to the hdf5 file to corrupt
- *prob*, probability to inject corruption
- *corruption_percentage*, value between 0-100, it represents the percentage of entries to corrupt (based on the HDF5 amount of entries)
- *byte*, which byte is faulty (0-7) -1 random
- *bit*, which bit is faulty (0-7) -1 random
- *use_random_locations*, choose random locations on the file to inject errors, if true it will ignore the locations_to_corrupt
- *locations_to_corrupt*, list of locations to try to inject errors

Example of a .yaml configuration file:  
>hdf5_file: "/home/someUser/Documents/hdf5_files/model_epoch_2_chainer.h5"  
>prob: 1e-8  
>max_corruption_percentage: 1e-3  
>byte: -1  
>bit: -1  
use_random_locations: False  
>locations_to_corrupt:  
>  \- "/predictor/conv1/W"  
>  \- "/predictor/conv1/b"  
>  \- "/predictor/res2/0/bn1/N"  
>  \- "/predictor/res2/0/bn4/avg_var"  
>  \- "/predictor/res3/2/conv2/W"  


Examples of ussage:
>\>python3 hdf5_corrupter.py -h  
>\>python3 hdf5_corrupter.py -c "config-pytorch.yaml"  
>\>python3 hdf5_corrupter.py -c "config-pytorch.yaml" -p  

