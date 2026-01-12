import pandas as pd
import argparse
from numpy import inf
from pathlib import Path

def format_value(value) -> str:

	if type(value) == float:
		return format(value, 'e')
	elif type(value) == int:
		return str(value)
	elif type(value) == str:
		return value
	else:
		raise ValueError('Value is not int, string or float.')
        

def main(args) -> None:

    templates = Path(args.templates)
    ppe = Path(args.PPE)
    ensemble_path = Path(args.ensemble_path)
    imax = args.max if args.max else inf
    imin = args.min if args.min else 0

    df = pd.read_csv(ppe)
    columns = df.columns

    if 'name' not in columns:
        raise KeyError("PPE requires a 'name' column in order to make directories")
    
    for i, row in df.iterrows():
        if i + 1 < imin:
            continue
        if i + 1 > imax:
            break

        name = row['name']
        run_dir = ensemble_path / name

        for util in ['ctrl', 'plot', 'chk', 'pout', 'output', 'error']:
            dirpath = run_dir / util
            dirpath.mkdir(parents=True, exist_ok=True)

        for template in templates.iterdir():
            template_content = template.read_text()

            script = template_content
            for col in columns:
                placeholder = f'@{col}'
                value = row[col]
                script = script.replace(placeholder, format_value(value))
            
            outfile_name = template.name.replace('template', name)
            outfile = run_dir / outfile_name
            outfile.write_text(script)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process inputs"
    )

    # add arguments
    parser.add_argument("templates", type=str, help="path to templates directory")
    parser.add_argument("PPE", type=str, help="path to PPE csv")
    parser.add_argument("ensemble_path", type=str, help="destination path for ensemble")
    parser.add_argument("--min", type=int, help="Only make runs from this index")
    parser.add_argument("--max", type=int, help="Only make runs up to this index")

    args = parser.parse_args()
    main(args)
