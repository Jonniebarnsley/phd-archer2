import h5py
import os
import sys
import glob

def check_hdf5_files(directory):

    '''
    Simply checks if all hdf5 files in a directory can be opened. 
    Useful for instances where BISICLES has been cut off whilst 
    writing to plot or checkpoint files, resulting in corrupted 
    files.
    '''

    h5_files = glob.glob(os.path.join(directory, '*.hdf5'))
    for fname in h5_files:
        try:
            with h5py.File(fname, 'r'):
                pass
        except Exception as e:
            print(f"Corrupted or unreadable file: {fname} — {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_hdf5.py /path/to/h5/files")
        sys.exit(1)
    check_hdf5_files(sys.argv[1])
