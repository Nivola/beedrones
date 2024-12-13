# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2024 CSI-Piemonte

from pyVmomi import vmodl
from beecell.types.type_date import format_date
from beedrones.vsphere.client import VsphereObject, VsphereError
from beedrones.vsphere.hardware import VsphereServerHardware


class VsphereServerSnapshot(VsphereObject):
    """
    Get and modify Vsphere server snapshot.
    """

    def __init__(self, server):
        VsphereObject.__init__(self, server.manager)
        self.server = server

    def __get_childs(self, snapshots, childs):
        """
        Recursive function to visit all childs, sub-childs, and so on for a given snapshot.

        :param snapshots: list of snapshot details to populate
        :param childs: list of childs of a given snapshot
        """
        if len(childs) == 0:
            return snapshots
        for item in childs:
            snapshot = {
                "id": VsphereServerSnapshot.get_mo_id(item.snapshot),
                "name": item.name,
                "desc": item.description,
                "creation_date": format_date(item.createTime),
                "state": item.state,
                "quiesced": item.quiesced,
                "backup_manifest": item.backupManifest,
                "replaysupported": item.replaySupported,
                "childs": [],
            }
            for child in item.childSnapshotList:
                snapshot["childs"].append(VsphereServerSnapshot.get_mo_id(child.snapshot))
            snapshots.append(snapshot)
            self.__get_childs(snapshots, item.childSnapshotList)
        return snapshots

    def list(self, server):
        """
        List server snapshots.

        :param server: server instance
        :return: list of dictionary with snapshot info
        """
        try:
            snapshots = []
            if server.snapshot is not None:
                for item in server.snapshot.rootSnapshotList:
                    snapshot = {
                        "id": VsphereServerSnapshot.get_mo_id(item.snapshot),
                        "name": item.name,
                        "desc": item.description,
                        "creation_date": format_date(item.createTime),
                        "state": item.state,
                        "quiesced": item.quiesced,
                        "backup_manifest": item.backupManifest,
                        "replaysupported": item.replaySupported,
                        "childs": [],
                    }
                    for child in item.childSnapshotList:
                        snapshot["childs"].append(VsphereServerSnapshot.get_mo_id(child.snapshot))
                    snapshots.append(snapshot)
                    self.__get_childs(snapshots, item.childSnapshotList)
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

        return snapshots

    def __get(self, server, childs, snapshot_id):
        """
        Recursive function to visit all childs, sub-childs, and so on for a given snapshot.

        :param childs: list of childs of a given snapshot
        :param snapshot_id: snapshot id to look for
        :return: snapshot instance
                :raise vmodl.MethodFault:
        """
        if server is not None:
            for item in server.snapshot.rootSnapshotList:
                if str(VsphereServerSnapshot.get_mo_id(item.snapshot)) == snapshot_id:
                    self.logger.debug("Found snapshot: %s", item.snapshot)
                    return item
                snap = self.__get(None, item.childSnapshotList, snapshot_id)
                if snap is not None:
                    return snap
        else:
            if len(childs) == 0:
                return None
            for item in childs:
                if str(VsphereServerSnapshot.get_mo_id(item.snapshot)) == snapshot_id:
                    self.logger.debug("Found snapshot: %s", item.snapshot)
                    return item
                return self.__get(None, item.childSnapshotList, snapshot_id)
        return None

    def get(self, server, snapshot_id):
        """
        Get server snapshot by managed object reference id.

        :param server: server instance
        :param snapshot_id: snapshot id
        :return: dict with snapshot info
        :raise VsphereError:
        """
        try:
            if server.snapshot is None:
                self.logger.error("Snapshot %s does not exist", snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg=f"Snapshot {snapshot_id} does not exist")

            snap = self.__get(server, None, snapshot_id)
            if snap is None:
                self.logger.error("Snapshot %s does not exist", snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg=f"Snapshot {snapshot_id} does not exist")

            snapshot = {
                "id": VsphereServerSnapshot.get_mo_id(snap.snapshot),
                "name": snap.name,
                "desc": snap.description,
                "creation_date": format_date(snap.createTime),
                "state": snap.state,
                "quiesced": snap.quiesced,
                "backup_manifest": snap.backupManifest,
                "replaysupported": snap.replaySupported,
                "childs": [],
            }
            for child in snap.childSnapshotList:
                snapshot["childs"].append(VsphereServerSnapshot.get_mo_id(child.snapshot))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

        return snapshot

    def get_current(self, server):
        """
        Get current server snapshot.

        :param server: server instance
        :return: dictionary with snapshot info
        :raise VsphereError:
        """
        try:
            item = server.rootSnapshot[0]
            vs_hw = VsphereServerHardware(self.server)

            snapshot = {
                "id": VsphereServerSnapshot.get_mo_id(item.snapshot),
                "config": vs_hw.get_config_data(item.config),
                "childs": [],
            }
            for child in item.childSnapshot:
                snapshot["childs"].append(VsphereServerSnapshot.get_mo_id(child.snapshot))
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

        return snapshot

    def create(self, server, name, desc=None, memory=False, quiesce=True):
        """
        Creates a new snapshot of this virtual machine. As a side effect,
        this updates the current snapshot.
        Snapshots are not supported for Fault Tolerance primary and secondary virtual machines.

        Any %(percent) character used in this name parameter must be escaped,
        unless it is used to start an escape sequence.
        Clients may also escape any other characters in this name parameter.

        :param server: server instance
        :param name: The name for this snapshot.
            The name need not be unique for this virtual machine.
        :param desc: A description for this snapshot.
            If omitted, a default description may be provided. [optional]
        :param memory: If TRUE, a dump of the internal state of the
            virtual machine (basically a memory dump) is included in the snapshot.
            Memory snapshots consume time and resources, and thus take longer to create.
            When set to FALSE, the power state of the snapshot is set to powered off.
            Capabilities indicates whether or not this virtual machine supports this operation.
            [default=False]
        :param quiesce: If TRUE and the virtual machine is powered on when the snapshot is taken,
            VMware Tools is used to quiesce the file system in the virtual machine.
            This assures that a disk snapshot represents a consistent state of the
            guest file systems.
            If the virtual machine is powered off or VMware Tools are not available,
            the quiesce flag is ignored. [default=True]
        :return: task
        :raise VsphereError:
        """
        try:
            if desc is None:
                desc = name
            task = server.CreateSnapshot_Task(name=name, description=desc, memory=memory, quiesce=quiesce)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

    def rename(self, server, snapshot_id, name, description=None):
        """
        Rename server snapshot snapshot_id.

        :param server: server instance
        :param snapshot_id: snapshot id
        :return: True
        :raise VsphereError:
        """
        try:
            if server.snapshot is None:
                self.logger.error("Snapshot %s does not exist", snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg=f"Snapshot {snapshot_id} does not exist")

            snap = self.__get(server, None, snapshot_id)
            if snap is None:
                self.logger.error("Snapshot %s does not exist", snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg=f"Snapshot {snapshot_id} does not exist")

            snap.RenameSnapshot(name=name, description=description)
            return True
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

    def revert(self, server, snapshot_id, suppress_power_on=False):
        """
        Revert to server snapshot snapshot_id.

        :param server: server instance
        :param snapshot_id: snapshot id
        :param suppress_power_on: (optional) If set to true, the virtual machine will not be
            powered on regardless of the power state when the snapshot was created.
            Default to false.
        :return: task
        :raise VsphereError:
        """
        try:
            if server.snapshot is None:
                self.logger.error("Snapshot %s does not exist", snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg=f"Snapshot {snapshot_id} does not exist")

            snap = self.__get(server, None, snapshot_id)
            if snap is None:
                self.logger.error("Snapshot %s does not exist", snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg=f"Snapshot {snapshot_id} does not exist")

            task = snap.snapshot.RevertToSnapshot_Task(suppressPowerOn=suppress_power_on)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error

    def remove(self, server, snapshot_id):
        """
        Remove server snapshot snapshot_id.

        :param server: server instance
        :param snapshot_id: snapshot id
        :return: task
        :raise VsphereError:
        """
        try:
            if server.snapshot is None:
                self.logger.error("Snapshot %s does not exist", snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg=f"Snapshot {snapshot_id} does not exist")

            snap = self.__get(server, None, snapshot_id)
            if snap is None:
                self.logger.error("Snapshot %s does not exist", snapshot_id, exc_info=False)
                raise vmodl.MethodFault(msg=f"Snapshot {snapshot_id} does not exist")

            task = snap.snapshot.RemoveSnapshot_Task(removeChildren=True, consolidate=True)
            return task
        except vmodl.MethodFault as error:
            self.logger.error(error.msg, exc_info=False)
            raise VsphereError(error.msg) from error
