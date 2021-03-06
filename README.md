# hdf5_corrupter
This tool takes an HDF5 file and tries to corrupt values with a fixed probability. 

The usage of the tool is as follows:
>\>python3 hdf5_corrupter.py *arguments*  

Where the possible arguments are:  
 - -h | --help, optional argument, prints the usage of the tool
 - -c | --configFile "path/to/config.yaml", mandatory argument (unless used with -h)
 - -f | --hdf5File "path/to/file.h5", path to the hdf5 file to corrupt. *Overwrites value from config file*
 - -l | --logFilePath "path/to/logs/", path where to save the log files. *Overwrites value from config file*
 - -g | --floatPrecision <value>, 64, 32 or 16, the number of bits to use for each float value")
 - -d | --firstBit <value>, first bit to inject errors (0-63), leftmost is sign-bit, next 11 are exp bits, and the rest is mantissa. it must be <= than last_bit. *Overwrites value from config file*
 - -e | --lastBit <value>, last bit to inject errors (0-63), it must be >= than first_byte. If both values are the same, injection will only happen on that bit. *Overwrites value from config file*
 - -b | --burst <value>, optional, default: 1, incompatible with scaling_factor, number of injection attempts per value *Overwrites value from config file*
 - -m | --bitMask <value>, optional, incompatible with scaling_factor or burst, uses a bit mask to corrupt the values, the first bit to apply the mask in each value is randomly selected from [0 to 63-bitMaskLength]
 - -p | --injectionProbability value, value of injection probability. *Overwrites value from config file*
 - -t | --injectionType type, where type can be either \"percentage\" or \"count\"". *Overwrites value from config file*
 - -k | --injectionTries value, is either a real number between [0-1] or an int > 0, depending if injection_type is "percentage" or "count", respectively. This value might not be the actual value of corruption, because the injection probability can be < 1. *Overwrites value from config file*
 - -a | --scalingFactor value, optional, if used it ignores the bit range and multiplies every value by this scaling factor
 - -s | --saveInjectionSequence, optional, incompatible with -i, it saves to json all the bits that were changed for each location specified.
 - -i | --injectionSequencePath "path/to/sequence.json", optional, incompatible with -s, loads the injection sequence from a json and uses those bits to corrupt the locations specified at the sequence. If used, it will ignore the probability, the injection type, the injection tries, the locations to corrupt. It will only corrupt what is specified at the injection sequence. 
 - -o | --onlyPrint, optional argument, prints the contents of the hdf5 file specified and exits

The .yaml configuration file must have the following entries:
- *hdf5_file*, the path to the hdf5 file to corrupt

- *injection_probability*, probability to inject an error at each value
- *injection_type*, is one of the following strings {"percentage", "count"}
- *injection_tries*,is either a real number between [0-1] or an int > 0, depending if injection_type is "percentage" or "count", respectively. This value might not be the actual value of corruption, because the injection probability can be < 1.

- *log_file_path*, path where to save the log files.
- *float_precision*, 64, 32 or 16, the number of bits to use for each float value.
- *first_bit*, first bit to inject errors (from 0 to float_precision-1), leftmost is sign-bit, next are exp bits and the rest is mantissa. it must be <= than last_bit.
- *last_bit*, last bit to inject errors (from 0 to float_precision-1), it must be >= than first_byte. If both values are the same, injection will only happen on that bit.
- *burst*, default: 1, number of bits to corrupt per value (chosen from the above range)
- *scaling_factor*, incompatible with bit range, burst, bit_mask, values will be scaled by this factor
- *bit_mask*, incompatible with bit range, burst, scaling factor. Corrupts using a bit mask. It pads a-zeros at start and b-zeros at the end of the mask where a+b+len(mask) = 64, a and b are chosen randomly, then it makes an xor with the binary representation of the val.
- *allow_sign_change*, True,   when corruption is on float value, even if the sign-bit (0) is not included, in the above range, it will also enable bit flips on it. False,  it respects the above range.
- *allow_NaN_values*, when flipping a bit of the in a double, the resulting binary can represent a NaN or Inf. If set to False, the corruption mechanism will never produce such values
- *save_injection_sequence*, If present, it saves to json all the bits that were changed for each location specified.
- *injection_sequence_path*, If used, loads the injection sequence from a json and uses those bits to corrupt the locations specified at the sequence.
- *use_random_locations*, choose random locations on the file to inject errors, if true it will ignore the locations_to_corrupt
- *locations_to_corrupt*, list of locations to try to inject errors

Example of a .yaml configuration file:  
>hdf5_file: "/home/someUser/Documents/hdf5_files/model_epoch_2_chainer.h5"  
>injection_probability: 1e-8  
>injection_type: "count"  
>log_file_path: "/home/someUser/Documents/logFiles/"  
>injection_tries: 5 
>float_precision: 64 
>first_bit: 0  
>last_bit: 63
>burst: 4  
>#scaling_factor: 100  
>#bit_mask: "101011"
>allow_sign_change: True  
>allow_NaN_values: True
>injection_sequence_path: "/path/to/injectionSequence.json"
>save_injection_sequence: False
>use_random_locations: False  
>locations_to_corrupt:  
>  \- "/predictor/conv1/W"  
>  \- "/predictor/conv1/b"  
>  \- "/predictor/res2/0/bn1/N"  
>  \- "/predictor/res2/0/bn4/avg_var"  
>  \- "/predictor/res3/2/conv2/W"  


Examples of ussage:
>\>python3 hdf5_corrupter.py -h  
>\>python3 hdf5_corrupter.py -c "config-pytorch.yaml"  
>\>python3 hdf5_corrupter.py -c "config-pytorch.yaml" -o
>\>python3 hdf5_corrupter.py -c "config-pytorch.yaml" -t "count" -k 34  
>\>python3 hdf5_corrupter.py -c "config-pytorch.yaml" -t "percentage" -k 0.00004
