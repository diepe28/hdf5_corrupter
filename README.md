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

- *injection_probability*, probability to inject an error at each value
- *injection_type*, is one of the following strings {"percentage", "count"}
- *injection_tries*,is either a real number between [0-1] or a int > 0, depending if injection_type is "percentage" or "count", respectively. This value might not be the actual value of corruption, because the injection probability can be < 1.

- *first_byte*, first byte to inject errors (0-7) -1 random, it must be <= than last_byte.
- *last_byte*, last byte to inject errors (0-7) -1 random, it must be >= than first_byte. If it's the same, injection will only happen on that byte. Note that first_byte = 0, it's the same as first_byte = -1. Note that last_byte = 7,  it's the same as last_byte = -1
- *bit*, which bit is faulty (0-7) -1 random
- *allow_NaN_values*, when flipping a bit of the in a double, the resulting binary can represent a NaN or Inf. If set to False, the corruption mechanism will never produce such values
- *use_random_locations*, choose random locations on the file to inject errors, if true it will ignore the locations_to_corrupt
- *locations_to_corrupt*, list of locations to try to inject errors

Example of a .yaml configuration file:  
>hdf5_file: "/home/someUser/Documents/hdf5_files/model_epoch_2_chainer.h5"  
>injection_probability: 1e-8  
>injection_type: "count"  
>injection_tries: 5  
>first_byte: -1  
>last_byte: -1  
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

