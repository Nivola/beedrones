# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import truncate
from beedrones.cmp.client import CmpBaseService


class CmpBusinessAbstractService(CmpBaseService):
    """Cmp business service
    """
    SUBSYSTEM = 'service'
    PREFIX = 'nws'
    VERSION = 'v1.0'


class CmpBusinessService(CmpBusinessAbstractService):
    """Cmp business service
    """
    def __init__(self, manager):
        CmpBaseService.__init__(self, manager)

        from .business_service import CmpBusinessServiceService
        from .business_capability import CmpBusinessCapabilityService
        from .business_account import CmpBusinessAccountService
        from .business_division import CmpBusinessDivisionService
        from .business_organization import CmpBusinessOrganizationService
        from .business_cpaas import CmpBusinessCpaasService
        from .business_netaas import CmpBusinessNetaasService

        self.service = CmpBusinessServiceService(self.manager)
        self.capability = CmpBusinessCapabilityService(self.manager)
        self.account = CmpBusinessAccountService(self.manager)
        self.div = CmpBusinessDivisionService(self.manager)
        self.org = CmpBusinessOrganizationService(self.manager)
        self.cpaas = CmpBusinessCpaasService(self.manager)
        self.netaas = CmpBusinessNetaasService(self.manager)
