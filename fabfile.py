from fabricio import docker, tasks
from fabric import api

host = '195.201.27.44'
user = 'metric'
domain = 'metr.ddns.net'


@api.hosts(f'root@{host}')
@api.task
def install_docker():
    api.run('apt-get remove docker docker-engine docker.io')
    api.run('apt-get update')
    api.run(
        'apt-get install '
        'apt-transport-https '
        'ca-certificates '
        'curl '
        'software-properties-common '
    )
    api.run('curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -')
    api.run('apt-key fingerprint 0EBFCD88')
    api.run(
        'add-apt-repository '
        '"deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" '
    )
    api.run('apt-get update')
    api.run('apt-get install docker-ce')


@api.hosts(f'root@{host}')
@api.task
def user_add():
    api.run(f'useradd -u 1010 -d /home/{user} -s /bin/bash -p wrongpassword {user}')
    api.run(f'usermod -aG docker {user}')


@api.hosts(f'root@{host}')
@api.task
def install_certificates():
    api.run('apt-get install software-properties-common')
    api.run('add-apt-repository ppa:certbot/certbot')
    api.run('apt-get update')
    api.run('apt-get install python-certbot-nginx')
    api.run(f'certbot --nginx -d {domain}')


@api.hosts(f'root@{host}')
@api.task
def copy_nginx():
    api.put('etc/metric_nginx.conf', '/etc/nginx/sites-enabled/metric.conf')
    api.run('nginx -t')
    api.run('service nginx reload')


@api.hosts(f'root@{host}')
@api.task
def create_network():
    api.run(
        'docker network create --subnet 172.19.0.0/24 --gateway 172.19.0.1 metric',
    )


metric_app = tasks.ImageBuildDockerTasks(
    service=docker.Container(
        name='metric_app',
        image='metric_app',
        options=dict(
            publish='8181:8181',
            network='metric',
            ip='172.19.0.2'
        ),
    ),
    ssh_tunnel='5000:5000',
    registry='localhost:5000',
    hosts=[f'{user}@{host}'],
    build_path='.',
)


metric_pg = tasks.ImageBuildDockerTasks(
    service=docker.Container(
        name='metric_pg',
        image='metric_pg',
        options=dict(
            network='metric',
            ip='172.19.0.3',
            volume=f'/home/{user}/pgdata:/var/lib/postgresql/data',
        )
    ),
    registry='localhost:5000',
    ssh_tunnel='5000:5000',
    hosts=[f'{user}@{host}'],
    build_path='sql',
)