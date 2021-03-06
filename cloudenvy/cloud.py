# vim: tabstop=4 shiftwidth=4 softtabstop=4
import functools

import novaclient.exceptions
import novaclient.client


def not_found(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except novaclient.exceptions.NotFound:
            return None
    return wrapped


class CloudAPI(object):
    def __init__(self, name, config):
        self._client = None
        self.name = name
        self.config = config
        section = 'cloud:%s' % name
        self.user = self.config.get(section, 'OS_USERNAME')
        self.password = self.config.get(section, 'OS_PASSWORD')
        self.tenant_name = self.config.get(section, 'OS_TENANT_NAME')
        self.auth_url = self.config.get(section, 'OS_AUTH_URL')
        self.service_name = self.config.get(section, 'OS_SERVICE_NAME')
        self.region_name = self.config.get(section, 'OS_REGION_NAME')

    @property
    def client(self):
        if not self._client:
            self._client = novaclient.client.Client(
                    '2',
                    self.user,
                    self.password,
                    self.tenant_name,
                    self.auth_url,
                    service_name=self.service_name,
                    region_name=self.region_name,
            )
        return self._client

    @not_found
    def find_server(self, name):
        return self.client.servers.find(name=name)

    @not_found
    def get_server(self, server_id):
        return self.client.servers.get(server_id)

    def create_server(self, *args, **kwargs):
        return self.client.servers.create(*args, **kwargs)

    def find_free_ip(self):
        fips = self.client.floating_ips.list()
        for fip in fips:
            if not fip.instance_id:
                return fip.ip
        raise exceptions.NoIPsAvailable()

    def find_ip(self, server_id):
        fips = self.client.floating_ips.list()
        for fip in fips:
            if fip.instance_id == server_id:
                return fip.ip

    def assign_ip(self, server, ip):
        server.add_floating_ip(ip)

    @not_found
    def find_image(self, name):
        return self.client.images.find(name=name)

    @not_found
    def get_image(self, image_id):
        return self.client.images.get(image_id)

    def snapshot(self, server, name):
        return self.client.servers.create_image(server, name)

    @not_found
    def find_flavor(self, name):
        return self.client.flavors.find(name=name)

    def find_security_group(self, name):
        try:
            return self.client.security_groups.find(name=name)
        except novaclient.exceptions.NotFound:
            return None

    def create_security_group(self, name):
        try:
            return self.client.security_groups.create(name, name)
        except novaclient.exceptions.NotFound:
            return None

    def create_security_group_rule(self, security_group, rule):
        return self.client.security_group_rules.create(
                security_group.id, *rule)

    def allocate_floating_ip(self):
        return self.client.floating_ips.create()

    @not_found
    def find_keypair(self, name):
        return self.client.keypairs.find(name=name)

    def create_keypair(self, name, key_data):
        return self.client.keypairs.create(name, public_key=key_data)


