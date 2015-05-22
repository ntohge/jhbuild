# jhbuild - a tool to ease building collections of source packages
# Copyright (C) 2011-2012  Craig Keogh
#
#   systemmodule.py: systemmodule type definitions.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__metaclass__ = type

from jhbuild.modtypes import Package, register_module_type

__all__ = [ 'SystemModule' ]


class SystemModule(Package):

    def __init__(self, name, runtime=False, apt_source=None, apt_key=None, apt_key_server=None, **kwargs):
        Package.__init__(self, name, **kwargs)
        self.runtime = runtime
        self.apt_source = apt_source
        self.apt_key = apt_key
        self.apt_key_server = apt_key_server

    @classmethod
    def create_virtual(cls, name, branch, deptype, value):
        return cls(name, branch=branch, systemdependencies=[(deptype, value)])

def parse_systemmodule(node, config, uri, repositories, default_repo):
    instance = SystemModule.parse_from_xml(node, config, uri, repositories,
                                           default_repo)

    if any(deptype == 'xml' for deptype, value in instance.systemdependencies):
        instance.dependencies += ['xmlcatalog']

    # for sysdeps specified in modules files, assume they are needed for runtime
    # package maintainers can choose to exclude them from being installed to runtime
    instance.runtime = True
    if node.hasAttribute('runtime'):
        instance.runtime = node.getAttribute('runtime') != 'no'

    # for packages that requires a special apt source, they can be specified via
    # apt-source and apt-key attributes
    if node.hasAttribute('apt-source'):
        instance.apt_source = node.getAttribute('apt-source')

    if node.hasAttribute('apt-key'):
        instance.apt_key = node.getAttribute('apt-key')

    if node.hasAttribute('apt-key-server'):
        instance.apt_key_server = node.getAttribute('apt-key-server')

    return instance

register_module_type('systemmodule', parse_systemmodule)
