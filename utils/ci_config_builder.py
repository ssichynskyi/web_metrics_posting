import argparse
import yaml


if __name__ == '__main__':
    cmd_args = argparse.ArgumentParser()
    cmd_args.add_argument(
        '--sample',
        dest='sample',
        type=str,
        required=True
    )
    cmd_args.add_argument(
        '--name',
        dest='name',
        type=str,
        required=True
    )
    cmd_args.add_argument(
        '--kafkaurl',
        dest='kafkaurl',
        type=str,
        required=True
    )
    cmd_args.add_argument(
        '--kafkaport',
        dest='kafkaport',
        type=int,
        required=True
    )
    cmd_args.add_argument(
        '--postgresurl',
        dest='postgresurl',
        type=str,
        required=True
    )
    cmd_args.add_argument(
        '--postgresport',
        dest='postgresport',
        type=int,
        required=True
    )
    args = cmd_args.parse_args()
    config = {'Metrics endpoint': {}}
    config_member = {
        'upload every': 60,
        'Kafka': {
            'host': '',
            'port': None
        },
        'Postgres': {
            'host': '',
            'port': None
        }
    }
    config['Metrics endpoint'][args.name] = config_member
    config['Metrics endpoint'][args.name]['Kafka']['host'] = args.kafkaurl
    config['Metrics endpoint'][args.name]['Kafka']['port'] = args.kafkaport
    config['Metrics endpoint'][args.name]['Postgres']['host'] = args.postgresurl
    config['Metrics endpoint'][args.name]['Postgres']['port'] = args.postgresport

    with open(args.sample.replace('.example', ''), 'w+') as f:
        yaml.safe_dump(config, f)
