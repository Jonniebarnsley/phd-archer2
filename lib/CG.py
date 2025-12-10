import re
import argparse
import matplotlib.pyplot as plt

def get_fm_fp(file):

    misfit_pattern = r"\|\|fm\(x\)\|\|\^2 = ([\d.e+-]+)"
    penalty_pattern = r"\|\|fp\(x\)\|\|\^2 = ([\d.e+-]+)"
    
    with open(file, "r") as f:
        data = f.read()
    fm = re.findall(misfit_pattern, data)
    fp = re.findall(penalty_pattern, data)
    fm = list(map(float, fm))
    fp = list(map(float, fp))
    
    return fm, fp

def plot_CG(filepath):
    
    fm, fp = get_fm_fp(filepath)
    
    print("Plotting...")
    x = range(len(fm))
    plt.plot(x, fm, label='fm')
    plt.plot(x, fp, label='fp')
    plt.yscale('log')
    plt.legend()
    plt.show()

def setup_x11_forwarding():
    print("Setting up X11 forwarding...")
    import matplotlib
    matplotlib.use("Qt5Agg")

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    return parser

def main():
    
    parser = create_parser()
    args = parser.parse_args()
    setup_x11_forwarding()
    try:
        plot_CG(args.file)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")

if __name__=="__main__":
    main()
