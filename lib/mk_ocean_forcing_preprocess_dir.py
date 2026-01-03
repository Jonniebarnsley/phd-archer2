import argparse
from pathlib import Path       

def main(args) -> None:
    
    MODEL = args.model
    model = MODEL.lower()

    directory = Path(model)
    templates = Path(args.templates)

    for util in ['error', 'output']:
        utilpath = directory / util
        utilpath.mkdir(parents=True, exist_ok=True)

    for template in templates.iterdir():
        content = template.read_text()
        content = content.replace('@MODEL', MODEL)
        content = content.replace('@model', model)
        content = content.replace('@SCENARIO', args.scenario)
        content = content.replace('@REALISATION', args.realisation)

        outfile_name = template.name.replace('template', model)
        outfile = directory / outfile_name
        outfile.write_text(content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process inputs"
    )

    # add arguments
    parser.add_argument("templates", type=str, help="path to templates directory")
    parser.add_argument("model", type=str, help="model name")
    parser.add_argument("scenario", type=str, help="scenario name")
    parser.add_argument("realisation", type=str, help="realisation name")

    args = parser.parse_args()
    main(args)
