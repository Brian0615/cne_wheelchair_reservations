import argparse

from admin_tools.src.create_schema import create_schema

parser = argparse.ArgumentParser(description='CNE Wheelchair Reservations - Admin Tools')
parser.add_argument('command', choices=['create_schema'], help='Command type')
parser.add_argument('--name', '-n', help='Name of the schema to create')

if __name__ == '__main__':
    args = parser.parse_args()
    match args.command:
        case "create_schema":
            create_schema(args.name)
        case _:
            raise ValueError(f"Unrecognized command {args.command}")
