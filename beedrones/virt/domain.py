# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2018-2022 CSI-Piemonte

from beecell.simple import jsonDumps
import base64
from time import sleep
import libvirt
import libvirt_qemu
import logging
import ujson as json
from xml.dom.minidom import parseString
from re import split
from six import ensure_text
from xmltodict import parse as xmltodict
from beecell.types.type_dict import dict_get
from beecell.types.type_string import bool2str, str2bool
from beecell.password import random_password
from beecell.types.type_date import format_date, get_date_from_timestamp


class VirtDomainError(Exception):
    pass


class VirtDomain(object):
    def __init__(self, server, dom):
        """Create a virt domain instance

        :param server: instance of qemu server
        :param dom: instance of qemu domain
        """
        self.logger = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)

        self._server = server
        self._domain = dom

    @property
    def domain(self):
        """Get domain."""
        return self._domain

    def switch(self):
        self._server.switch()

    def __get_state(self):
        """get domain state"""
        state, reason = self._domain.state()

        if state == libvirt.VIR_DOMAIN_NOSTATE:
            resp = 'VIR_DOMAIN_NOSTATE'
        elif state == libvirt.VIR_DOMAIN_RUNNING:
            resp = 'VIR_DOMAIN_RUNNING'
        elif state == libvirt.VIR_DOMAIN_BLOCKED:
            resp = 'VIR_DOMAIN_BLOCKED'
        elif state == libvirt.VIR_DOMAIN_PAUSED:
            resp = 'VIR_DOMAIN_PAUSED'
        elif state == libvirt.VIR_DOMAIN_SHUTDOWN:
            resp = 'VIR_DOMAIN_SHUTDOWN'
        elif state == libvirt.VIR_DOMAIN_SHUTOFF:
            resp = 'VIR_DOMAIN_SHUTOFF'
        elif state == libvirt.VIR_DOMAIN_CRASHED:
            resp = 'VIR_DOMAIN_CRASHED'
        elif state == libvirt.VIR_DOMAIN_PMSUSPENDED:
            resp = 'VIR_DOMAIN_PMSUSPENDED'
        else:
            resp = 'unknown'
        return resp

    def __info(self):
        """get virtual machine description. Specify at least name or id.
        
        XMLDesc flags:
        1 VIR_DOMAIN_XML_SECURE     dump security sensitive information too
        2 VIR_DOMAIN_XML_INACTIVE   dump inactive domain information
        4 VIR_DOMAIN_XML_UPDATE_CPU update guest CPU requirements according to host CPU
        8 VIR_DOMAIN_XML_MIGRATABLE dump XML suitable for migration
        """
        is_active = str2bool(self._domain.isActive())
        ext_infos = xmltodict(self._domain.XMLDesc(8), dict_constructor=dict, attr_prefix='')
        resp = ext_infos.get('domain')
        resp['state'] = self.__get_state()
        resp['active'] = is_active
        resp['persistent'] = bool2str(self._domain.isPersistent())
        if is_active is True:
            # resp['ifaces'] = self._domain.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT)
            try:
                resp['time'] = format_date(get_date_from_timestamp(int(self._domain.getTime().get('seconds'))))
                resp['ifaces'] = self.qemu_guest_network_get_interfaces()
                resp['file_system'] = self.qemu_guest_fsinfo()
                resp['quest_agent'] = True
            except:
                resp['time'] = None
                resp['file_system'] = []
                resp['ifaces'] = None
                resp['quest_agent'] = False
        else:
            resp['time'] = None
            resp['file_system'] = []
            resp['ifaces'] = None
            resp['quest_agent'] = False

        return resp

    def info(self):
        """Get base info
        """
        info = self.__info()
        disks = dict_get(info, 'devices.disk')
        if isinstance(disks, dict):
            disks = [disks]

        resp = {
            'uuid': info.get('uuid'),
            'name': info.get('name'),
            'type': info.get('type'),
            'metadata': info.get('metadata'),
            'cpu': info.get('cpu').get('topology'),
            'memory': info.get('memory'),
            'disk': [d for d in disks if d.get('device') == 'disk'],
            'active': info.get('active'),
            'persistent': info.get('persistent'),
            'state': info.get('state'),
            'ifaces': info.get('ifaces'),
            'file_system': info.get('file_system'),
            'time': info.get('time'),
            'quest_agent': info.get('quest_agent')
        }
        return resp

    def ext_info(self):
        """Get extended info
        """
        resp = self.__info()
        resp['guest_info'] = self.qemu_guest_info()
        resp['error'] = {
            'disk': self._domain.diskErrors()
        }
        return resp

    def get_job(self):
        """Extract information about an active job being processed for a domain.
        """
        resp = self._domain.jobInfo()
        return resp

    def monitor(self):
        print(self._domain.numaParameters())
        print(self._domain.memoryStats())
        print(self._domain.maxMemory())
        print(self._domain.maxVcpus())

    def _get_xml_description(self):
        """ Get virtual machine description.
        
        Exception: VirtDomainError.
        
        :param domain: libvirt domain
        """
        try:
            data = self._domain.XMLDesc(8)
            self.switch()
            return parseString(data)
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def print_xml_description(self):
        """ Get virtual machine description.
        
        Exception: VirtDomainError.
        
        :param domain: libvirt domain
        """
        try:
            data = self._domain.XMLDesc(8)
            self.switch()
            return data
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _append_device_spice_graphics(self, xml_desc):
        """Append configuration for spice display
            TODO : tlsPort='-1'  unsupported configuration: spice secure channels set in XML configuration, but TLS is disabled in qemu.conf
            "<channel name='main' mode='secure'/>",
        """
        try:
            password = random_password()
            # TODO to add tlsPort='-1' you must configure tls in /etc/libvirt/qemu.conf
            data = ["<graphics type='spice' port='-1' autoport='yes' passwd='%s'>" % password,
                    #"<channel name='main' mode='secure'/>", to use configure tls
                    "<image compression='auto_glz'/>",
                    "<streaming mode='filter'/>",
                    "<clipboard copypaste='yes'/>",
                    "<mouse mode='client'/>",
                    "<filetransfer enable='yes'/>",
                    "<listen type='address' address='0.0.0.0'/>",
                    "</graphics>"]         
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            graphic_device = devices_tag.getElementsByTagName("graphics")[0]
            #print devices_tag.toxml
            devices_tag.removeChild(graphic_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)          
    
    def _append_device_vnc_graphics(self, xml_desc):
        """Append configuration for spice display
        """
        try:
            data = ["<graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0' password='xxx'>",
                    "<listen type='address' address='0.0.0.0'/>",
                    "</graphics>"]
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            graphic_device = devices_tag.getElementsByTagName("graphics")[0]
            #print devices_tag.toxml()
            devices_tag.removeChild(graphic_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
    
    def _append_device_video_cirrus(self, xml_desc):
        """Append configuration for spice display
              
        """
        try:
            data = ["<video>",
                    "<model type='cirrus' vram='8192' heads='1'/>",
                    "<acceleration accel3d='yes' accel2d='yes'/>",
                    #"<alias name='video0'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>",
                    "</video>"]
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            video_device = devices_tag.getElementsByTagName("video")[0]
            devices_tag.removeChild(video_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)      

    def _append_device_video_qxl(self, xml_desc):
        """Append configuration for spice display
        """
        try:
            data = ["<video>",
                    "<model type='qxl' vram='131072' heads='1'/>",
                    #"<alias name='video0'/>",
                    "<acceleration accel3d='yes' accel2d='yes'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>",
                    "</video>"]
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            video_device = devices_tag.getElementsByTagName("video")[0]
            devices_tag.removeChild(video_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)      

    def _append_device_video_vmware(self, xml_desc):
        """Append configuration for spice display
        """
        try:
            data = ["<video>",
                    "<model type='vmware'/>",
                    "</video>"]
            new_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("image")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            video_device = devices_tag.getElementsByTagName("video")[0]
            devices_tag.removeChild(video_device)
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex) 

    def _append_device_channel_unix(self, xml_desc):
        """Append configuration for spice display
        """
        try:
            agent_name = xml_desc.getElementsByTagName("name")[0].firstChild.data

            #"<address type='virtio-serial' controller='0' bus='0' port='1'/>",
            data = ["<channel type='unix'>",
                    "<source mode='bind' path='/var/lib/libvirt/qemu/%s.agent'/>" % agent_name,
                    "<target type='virtio' name='org.qemu.guest_agent.0'/>",
                    "<alias name='channel0'/>",
                    "</channel>"]
            serial_device = parseString(''.join(data)).documentElement
            #print new_device.getElementsByTagName("Errorimage")
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            #graphic_device = devices_tag.getElementsByTagName("graphics")[0]
            #print devices_tag.toxml()
            #devices_tag.removeChild(graphic_device)
            devices_tag.appendChild(serial_device)
            
            return xml_desc
        except Exception as ex:
           self.logger.error(ex)
           raise VirtDomainError(ex)      

    def _append_device_channel_spicevmc(self, xml_desc):
        """Append configuration for spice display
        
        """
        try:
            agent_name = xml_desc.getElementsByTagName("name")[0]
            
            data = ["<channel type='spicevmc'>",
                    "<target type='virtio' name='com.redhat.spice.0'/>",
                    "</channel>"]
            device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            devices_tag.appendChild(device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)  

    def _append_device_usb_redirect(self, xml_desc):
        """Append configuration for spice display
        
        :param alias: value like redir0, redir1. Be careful to use different 
                      alias for every device.
        """
        device_num = 3
        try:
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            usbr_device = devices_tag.getElementsByTagName("redirdev")

            dev_num = len(usbr_device)
            # there are existing usbredir devices
            data = []
            if dev_num > 0:
                # TODO delete all redirdev
                pass
            
            # create new devices
            for i in range(0, device_num):
                alias = 'redir%s' % str(i)
                data = ["<redirdev bus='usb' type='spicevmc'>",
                        "<alias name='%s'/>" % alias,
                        "</redirdev>"]
            
                usbr_device = parseString(''.join(data)).documentElement
                #print new_device.getElementsByTagName("image")
                #devices_tag.removeChild(graphic_device)
                devices_tag.appendChild(usbr_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)      

    def _append_device_usb2_controller(self, xml_desc):
        """Append configuration for spice display
        
        :param alias: value like redir0, redir1. Be careful to use different 
                      alias for every device.
        """
        try:
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            cotroller_usb_nodes = devices_tag.getElementsByTagName("controller")
            
            # remove existing controllor with type = 'usb'
            for item in cotroller_usb_nodes:
                controlle_type = item.getAttribute('type')
                if controlle_type == 'usb':
                    devices_tag.removeChild(item)
            
            # first usb controller
            data = ["<controller type='usb' index='0' model='ich9-ehci1'>",
                    "<alias name='usb0'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x7'/>",
                    "</controller>"]
            usb_controller = parseString(''.join(data)).documentElement
            devices_tag.appendChild(usb_controller)
                         
            # second usb controller
            data = ["<controller type='usb' index='0' model='ich9-uhci1'>",
                    "<alias name='usb0'/>",
                    "<master startport='0'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0' multifunction='on'/>",
                    "</controller>"]
            usb_controller = parseString(''.join(data)).documentElement
            devices_tag.appendChild(usb_controller)                      

            # third usb controller
            data = ["<controller type='usb' index='0' model='ich9-uhci2'>",
                    "<alias name='usb0'/>",
                    "<master startport='2'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x1'/>",
                    "</controller>"]
            usb_controller = parseString(''.join(data)).documentElement
            devices_tag.appendChild(usb_controller) 

            # fourth usb controller
            data = ["<controller type='usb' index='0' model='ich9-uhci3'>",
                    "<alias name='usb0'/>",
                    "<master startport='4'/>",
                    "<address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x2'/>",
                    "</controller>"]
            usb_controller = parseString(''.join(data)).documentElement
            devices_tag.appendChild(usb_controller) 

            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _append_device_sound_card_ac97(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            data = ["<sound model='ac97'>",
                    "<alias name='sound0'/>",
                    #"<address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>",
                    "</sound>"]
            new_device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            sound_device = devices_tag.getElementsByTagName("sound")
            if len(sound_device) > 0:
                devices_tag.removeChild(sound_device[0])
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _append_device_sound_card_es1370(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            data = ["<sound model='es1370'>",
                    "<alias name='sound0'/>",
                    "</sound>"]
            new_device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            sound_device = devices_tag.getElementsByTagName("sound")
            if len(sound_device) > 0:
                devices_tag.removeChild(sound_device[0])
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
        
    def _append_device_sound_card_sb16(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            data = ["<sound model='sb16'>",
                    "<alias name='sound0'/>",
                    "</sound>"]
            new_device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            sound_device = devices_tag.getElementsByTagName("sound")
            if len(sound_device) > 0:
                devices_tag.removeChild(sound_device[0])
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _append_device_sound_card_ich6(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            data = ["<sound model='ich6'>",
                    "<alias name='sound0'/>",
                    "</sound>"]
            new_device = parseString(''.join(data)).documentElement
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            sound_device = devices_tag.getElementsByTagName("sound")
            if len(sound_device) > 0:
                devices_tag.removeChild(sound_device[0])
            devices_tag.appendChild(new_device)
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
    
    def _change_interface_model(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            interface_devices = devices_tag.getElementsByTagName("interface")
            if len(interface_devices) > 0:
                for dev in interface_devices:
                    # get only interface of type bridge
                    if dev.getAttribute('type') == 'bridge':
                        model = dev.getElementsByTagName('model')[0]
                        model.setAttribute('type', 'virtio')
                    
                        # remove bandwidth tag
                        bandwidth = dev.getElementsByTagName('bandwidth')
                        if bandwidth:
                            dev.removeChild(bandwidth[0])
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def _change_disk_bus(self, xml_desc):
        """Append configuration for spice display

        """
        try:
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            disk_devices = devices_tag.getElementsByTagName("disk")
            if len(disk_devices) > 0:
                for dev in disk_devices:
                    # get only disk device. Exclude other disk type like cdrom
                    if dev.getAttribute('device') == 'disk':
                        # create new disk target
                        new_target = parseString("<target dev='vda' bus='virtio'/>").documentElement
                        old_target = dev.getElementsByTagName("target")[0]
                        dev.replaceChild(new_target, old_target)

                        # remove disk address
                        address = dev.getElementsByTagName('address')
                        if address:
                            dev.removeChild(address[0])
            
            return xml_desc
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
    
    def change_graphics_password(self, password):
        """Append configuration for spice display
              
        """
        try:
            # get graphics device type
            xml_desc = self._get_xml_description()
            devices_tag = xml_desc.getElementsByTagName("devices")[0]
            graphic_device = devices_tag.getElementsByTagName("graphics")[0]
            graphic_type = graphic_device.attributes['type'].value
            
            if graphic_type == 'spice':
                # TODO to add tlsPort='-1' you must configure tls in /etc/libvirt/qemu.conf
                data = ["<graphics type='spice' port='-1' autoport='yes' passwd='%s'>" % password,
                        #"<channel name='main' mode='secure'/>", to use configure tls
                        "<image compression='auto_glz'/>",
                        "<streaming mode='filter'/>",
                        "<clipboard copypaste='yes'/>",
                        "<mouse mode='client'/>",
                        "<filetransfer enable='yes'/>",
                        "<listen type='address' address='0.0.0.0'/>",
                        "</graphics>"]
                xml = ''.join(data)              
                self._domain.updateDeviceFlags(xml, flags=0)
            self.switch()
            self.logger.debug('Change password of graphics devices %s for libvirt domain: %s' % (
                                graphic_type, self._name))                
        except Exception as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)  
    
    def destroy(self):
        """Destroy domain.
        
        :param domain: libvirt domain
        """
        try:
            data = self._domain.destroy()
            self.switch()
            self.logger.debug('Destroy libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def start(self):
        """Start domain.
        """
        try:
            data = self._domain.create()
            self.switch()
            self.logger.debug('Start libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def reboot(self):
        """Reboot domain.  
        """
        try:
            data = self._domain.reboot(libvirt.VIR_DOMAIN_SHUTDOWN_GUEST_AGENT)
            self.switch()
            self.logger.debug('Reboot libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
        
    def shutdown(self):
        """Shutdown domain.   
        """
        try:
            data = self._domain.shutdownFlags(libvirt.VIR_DOMAIN_SHUTDOWN_GUEST_AGENT)
            self.switch()
            self.logger.debug('Shutdown libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def define(self, xml_desc):
        """Define domain form xml descriptor.
        
        :param xml_desc: domain xml descriptor
        """
        try:
            dom = self._server.conn.defineXML(xml_desc)
            self.switch()
            self.logger.debug('Define libvrit domain: %s' % self._domain)
            return dom
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)            

    def undefine(self, domain):
        """Undefine domain.

        :param domain: libvirt domain        
        """        
        try:
            data = self._domain.undefine()
            self.switch()
            self.logger.debug('Undefine libvrit domain: %s' % self._domain)
            return data
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

    def append_device(self, devices):
        """append device to domain
        
        :param device: device like : spice_graphics, vnc_graphics, rdp_graphics, video_cirrus, video_qxl, virtio_serial,
            usb_redirect, sound_card,
        """
        # get xml description of domain
        xml_desc = self._get_xml_description()        
        
        # default device to always append
        xml_desc2 = self._append_device_channel_spicevmc(xml_desc)
        xml_desc2 = self._append_device_usb2_controller(xml_desc)
        
        # change default device model (desk, network) to virtio
        xml_desc2 = self._change_interface_model(xml_desc)
        
        if devices and len(devices) > 0:
            # append devices configuration
            for device in devices:
                if device == 'spice_graphics':
                    xml_desc2 = self._append_device_spice_graphics(xml_desc)
                elif device == 'vnc_graphics':
                    xml_desc2 = self._append_device_vnc_graphics(xml_desc)
                elif device == 'video_cirrus':
                    xml_desc2 = self._append_device_video_cirrus(xml_desc)
                elif device == 'video_qxl':
                    xml_desc2 = self._append_device_video_qxl(xml_desc)
                elif device == 'video_vmware':
                    xml_desc2 = self._append_device_video_vmware(xml_desc)                    
                elif device == 'virtio_serial':
                    xml_desc2 = self._append_device_channel_unix(xml_desc)
                elif device == 'usb_redirect':
                    xml_desc2 = self._append_device_usb_redirect(xml_desc)
                elif device == 'sound_card_ac97':
                    xml_desc2 = self._append_device_sound_card_ac97(xml_desc)
                elif device == 'sound_card_es1370':
                    xml_desc2 = self._append_device_sound_card_es1370(xml_desc)
                elif device == 'sound_card_sb16':
                    xml_desc2 = self._append_device_sound_card_sb16(xml_desc)
                elif device == 'sound_card_ich6':
                    xml_desc2 = self._append_device_sound_card_ich6(xml_desc)
            
            self.logger.debug('Append devices %s to libvirt domain: %s' % (devices, self._domain))
            
        # destroy domain
        self.destroy()
        # define domain with new xml descriptor
        domain2 = self.define(xml_desc2.toxml())
        # start new domain
        res = self.start()
        
        self._domain = domain2

        return self._domain

    def set_user_password(self, user, password):
        """Sets the user password to the value specified by password.

        :return: list of spice connection channels
        """
        try:
            stat = self._domain.setUserPassword(user, password, flags=0)
            self.switch()
            self.logger.debug('set domain %s user %s password' % (self._domain, user))
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

        return True

    def freeze_filesystem(self, mountpoints):
        """Freeze specified filesystems within the guest

        :param mountpoints: list mountpoint
        """
        try:
            stat = self._domain.fsFreeze(self, mountpoints, flags=0)
            self.switch()
            self.logger.debug('Freeze domain %s filesystems %s' % (self._domain, mountpoints))
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)

        return True

    def run_qemu_agent_command(self, cmd):
        """run qemu agent command

        :param cmd: command
        """
        try:
            data = libvirt_qemu.qemuAgentCommand(self._domain, cmd, 5, 0)
            self.switch()
            data = json.loads(data)['return']
            self.logger.debug('qemu guest agent command %s response: %s' % (cmd, data))
            return data
        except libvirt.libvirtError as ex:
            self.logger.error('domain %s error: %s' % (self._domain.name(), ex))
            raise VirtDomainError(ex)

    def qemu_guest_exec(self, path, args):
        """Execute a command in the guest

        :param path: path or executable name to execute
        :param arg: argument list to pass to executable
        :param env: environment variables to pass to executable
        :param input-data: data to be passed to process stdin (base64 encoded)
        :retunr: PID on success
        """
        cmd = {
            'execute': 'guest-exec',
            'arguments': {
                'capture-output': True,
                'path': path,
                'arg': args
            }
        }
        cmd = jsonDumps(cmd)
        res = self.run_qemu_agent_command(cmd)
        if res is not None:
            sleep(0.01)
            pid = res.get('pid')
            cmd = '{"execute":"guest-exec-status", "arguments":{"pid": %s}}' % pid
            res = self.run_qemu_agent_command(cmd)
            if res['exitcode'] == 0:
                res['parsed-out-data'] = ensure_text(base64.b64decode(res['out-data']))
            return res
        return None

    def qemu_guest_ping(self):
        """get qemu guest ping"""
        try:
            self.run_qemu_agent_command('{ "execute": "guest-ping" }')
            return True
        except:
            return False

    def qemu_guest_info(self):
        """get qemu guest info"""
        return self.run_qemu_agent_command('{ "execute": "guest-info" }')

    def qemu_guest_osinfo(self):
        return self.run_qemu_agent_command('{ "execute": "guest-get-osinfo" }')

    def qemu_guest_osinfo(self):
        return self.run_qemu_agent_command('{ "execute": "guest-get-osinfo" }')

    def qemu_guest_network_get_interfaces(self):
        return self.run_qemu_agent_command('{ "execute": "guest-network-get-interfaces" }')

    def qemu_guest_fsinfo(self):
        try:
            fsinfo = self.run_qemu_agent_command('{ "execute": "guest-get-fsinfo" }')
        except:
            fsinfo = []

        try:
            """get qemu guest file system usage"""
            file_system_data = {}
            info = self.qemu_guest_exec('df', ['-m']).get('parsed-out-data')
            for fs in info.split('\n'):
                try:
                    if fs is not None and fs != '':
                        m = split(r'\s+', fs)
                        file_system_data[m[5]] = {'size': '%sMB' % m[3], 'used': m[2], 'usage': m[4]}
                except Exception as ex:
                    pass

            for item in fsinfo:
                item.update(file_system_data.get(item['mountpoint']))
        except:
            pass

        return fsinfo

    def qemu_guest_exec_ping(self, ip_address):
        try:
            info = self.qemu_guest_exec('ping', ['-c 3', ip_address])#.get('parsed-out-data')
            print(info)
        except:
            pass

    def spice_connection_status(self):
        """Return spice connection channels
        
        :return: list of spice connection channels
        """
        try:
            stat = libvirt_qemu.qemuMonitorCommand(self._domain, '{ "execute": "query-spice" }',
                                                   libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT)
            self.switch()
            data = json.loads(stat)['return']['channels']
            self.logger.debug('Get spice connection status: %s' % data)
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
            
        return data
    
    def vnc_connection_status(self):
        """Return vnc connection channels
        
        :return: list of spice connection channels
        """
        try:
            stat = libvirt_qemu.qemuMonitorCommand(self._domain, '{ "execute": "query-vnc" }',
                                                   libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT)
            self.switch()
            data = json.loads(stat)['return']['clients']
            self.logger.debug('Get spice connection status: %s' % data)
        except libvirt.libvirtError as ex:
            self.logger.error(ex)
            raise VirtDomainError(ex)
            
        return data
