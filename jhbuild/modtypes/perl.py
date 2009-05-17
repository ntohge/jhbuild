# jhbuild - a build script for GNOME 1.x and 2.x
# Copyright (C) 2001-2006  James Henstridge
#
#   perl.py: perl module type definitions.
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

import os
import re

from jhbuild.errors import BuildStateError
from jhbuild.modtypes import \
     Package, get_dependencies, get_branch, register_module_type

__all__ = [ 'PerlModule' ]

class PerlModule(Package):
    """Base type for modules that are distributed with a Perl style
    "Makefile.PL" Makefile."""
    type = 'perl'

    PHASE_CHECKOUT = 'checkout'
    PHASE_FORCE_CHECKOUT = 'force_checkout'
    PHASE_BUILD = 'build'
    PHASE_INSTALL = 'install'

    def __init__(self, name, branch, makeargs='',
                 dependencies=[], after=[], suggests=[]):
        Package.__init__(self, name, dependencies, after, suggests)
        self.branch = branch
        self.makeargs = makeargs

    def get_srcdir(self, buildscript):
        return self.branch.srcdir

    def get_builddir(self, buildscript):
        # does not support non-srcdir builds
        return self.get_srcdir(buildscript)

    def get_revision(self):
        return self.branch.branchname

    def do_start(self, buildscript):
        pass
    do_start.error_phases = []

    def do_deb_start(self, buildscript):
        buildscript.set_action('Starting building', self)
        buildscript.execute(['sudo', 'apt-get', 'update'])
        ext_dep = buildscript.config.external_dependencies.get(self.name)
        if not ext_dep:
            raise BuildStateError('No external dep for %s' % self.name)

        #print buildscript.config.external_dependencies

        available = self.get_available_debian_version(buildscript).split('-')[0]
        if ':' in available: # remove epoch
            available = available.split(':')[-1]

        def lax_int(s):
            try:
                return int(s)
            except ValueError:
                return -1

        deb_available = [lax_int(x) for x in available.split('.')]
        ext_minimum = [lax_int(x) for x in ext_dep.get('minimum').split('.')]
        ext_recommended = [lax_int(x) for x in ext_dep.get('recommended').split('.')]

        if deb_available >= ext_recommended:
            return (self.STATE_DONE, None, None)

        if deb_available >= ext_minimum:
            # XXX: warn it would be better to have a newer version
            raise SkipToState(self.STATE_DONE)
    do_deb_start.error_phases = []

    def do_checkout(self, buildscript):
        self.checkout(buildscript)
    do_checkout.error_phases = [PHASE_FORCE_CHECKOUT]

    def do_force_checkout(self, buildscript):
        buildscript.set_action(_('Checking out'), self)
        self.branch.force_checkout(buildscript)
    do_force_checkout.error_phases = [PHASE_FORCE_CHECKOUT]

    def do_build(self, buildscript):
        buildscript.set_action(_('Building'), self)
        builddir = self.get_builddir(buildscript)
        perl = os.environ.get('PERL', 'perl')
        make = os.environ.get('MAKE', 'make')
        makeargs = self.makeargs + ' ' + self.config.module_makeargs.get(
                self.name, self.config.makeargs)
        cmd = '%s Makefile.PL INSTALLDIRS=vendor PREFIX=%s %s' % (perl, buildscript.config.prefix, makeargs)
        buildscript.execute(cmd, cwd=builddir, extra_env = self.extra_env)
        buildscript.execute([make, 'LD_RUN_PATH='], cwd=builddir,
                extra_env = self.extra_env)
    do_build.depends = [PHASE_CHECKOUT]
    do_build.error_phases = [PHASE_FORCE_CHECKOUT]

    def do_install(self, buildscript):
        buildscript.set_action(_('Installing'), self)
        builddir = self.get_builddir(buildscript)
        make = os.environ.get('MAKE', 'make')
        buildscript.execute(
                [make, 'install', 'PREFIX=%s' % buildscript.config.prefix],
                cwd = builddir, extra_env = self.extra_env)
        buildscript.packagedb.add(self.name, self.get_revision() or '')
    do_install.depends = [PHASE_CHECKOUT]

    def xml_tag_and_attrs(self):
        return 'perl', [('id', 'name', None),
                         ('makeargs', 'makeargs', '')]


def parse_perl(node, config, uri, repositories, default_repo):
    id = node.getAttribute('id')
    makeargs = ''
    if node.hasAttribute('makeargs'):
        makeargs = node.getAttribute('makeargs')

    # Make some substitutions; do special handling of '${prefix}'
    p = re.compile('(\${prefix})')
    makeargs = p.sub(config.prefix, makeargs)
    
    dependencies, after, suggests = get_dependencies(node)
    branch = get_branch(node, repositories, default_repo, config)

    return PerlModule(id, branch, makeargs,
            dependencies=dependencies, after=after,
            suggests=suggests)
register_module_type('perl', parse_perl)

