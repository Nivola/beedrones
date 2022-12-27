# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import jsonDumps

from beedrones.cmp.client import CmpBaseService


class CmpCatalogAbstractService(CmpBaseService):
    """Cmp catalog service
    """
    SUBSYSTEM = 'auth'
    PREFIX = 'ncs'
    VERSION = 'v1.0'

    def get_uri(self, uri):
        return '/%s/%s/%s' % (self.VERSION, self.PREFIX, uri)


class CmpCatalogService(CmpCatalogAbstractService):
    """Cmp catalog service
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

    #
    # catalog request
    #
    def get_catalogs(self):
        """Get catalogs

        :param uid: identity id
        :param seckey: identity secret key
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('catalogs')
        res = self.api_get(uri, data='').get('catalogs', [])
        self.logger.debug('Get catalogs')
        return res

    def get_catalog(self, catalog_id):
        """Get catalogs

        :param catalog_id: id of the catalog
        :param uid: identity id
        :param seckey: identity secret key
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('catalogs/%s' % catalog_id)
        res = self.api_get(uri, data='').get('catalog', {})
        self.logger.debug('Get catalog %s' % catalog_id)
        return res

    def create_catalog(self, name, zone):
        """Create catalogs

        :param name: catalog name
        :param zone: catalog zone
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'name': name,
            'desc': 'catalog %s' % name,
            'zone': zone
        }
        uri = self.get_uri('catalogs')
        res = self.api_post(uri, data={'catalog': data})
        self.logger.debug('Create catalog %s' % name)
        return res

    def delete_catalog(self, catalog_id):
        """Delete catalogs

        :param catalog_id: id of the catalog
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('catalogs/%s' % catalog_id)
        self.api_delete(uri, data='')
        self.logger.debug('Delete catalog %s' % catalog_id)

    #
    # endpoint request
    #
    def get_endpoints(self):
        """Get endpoints

        :param uid: identity id
        :param seckey: identity secret key
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('endpoints')
        res = self.api_get(uri, data='').get('endpoints', [])
        self.logger.debug('Get endpoints')
        return res

    def get_endpoint(self, endpoint_id):
        """Get endpoints

        :param endpoint_id: id of the endpoint
        :param uid: identity id
        :param seckey: identity secret key
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('endpoints/%s' % endpoint_id)
        res = self.api_get(uri, data='').get('endpoints', [])
        self.logger.debug('Get endpoint %s' % endpoint_id)
        return res

    def create_endpoint(self, catalog_id, name, service, uri,
                        uid=None, seckey=None):
        """Create endpoints

        :param catalog_id: id of the catalog
        :param name: endpoint name
        :param service: endpoint service
        :param uri: endpoint uri
        :param uid: identity id
        :param seckey: identity secret key
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {
            'endpoint': {
                'catalog': catalog_id,
                'name': name,
                'desc': 'Endpoint %s' % name,
                'service': service,
                'uri': uri,
                'active': True
            }
        }
        uri = self.get_uri('endpoints')
        res = self.api_post(uri, data=data)
        self.logger.debug('Create endpoint %s' % name)
        return res

    def update_endpoint(self, oid, catalog_id=None, name=None, service=None, uri=None):
        """Update endpoints

        :param oid: endpoint id/name
        :param catalog_id: id of the catalog
        :param name: endpoint name
        :param service: endpoint service
        :param uri: endpoint uri
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        data = {}
        if catalog_id is not None:
            data['catalog'] = catalog_id
        if name is not None:
            data['name'] = name
        if service is not None:
            data['service'] = service
        if uri is not None:
            data['uri'] = uri

        data = {
            'endpoint': data
        }
        uri = self.get_uri('endpoints/%s' % oid)
        res = self.api_put(uri, data=data)
        self.logger.debug('Create endpoint %s' % name)
        return res

    def delete_endpoint(self, endpoint_id):
        """Delete endpoints

        :param endpoint_id: id of the endpoint
        :param uid: identity id
        :param seckey: identity secret key
        :return:
        :raises CmpApiClientError: raise :class:`CmpApiClientError`
        """
        uri = self.get_uri('endpoints/%s' % endpoint_id)
        self.api_delete(uri, data='')
        self.logger.debug('Delete endpoint %s' % endpoint_id)
