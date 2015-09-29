# vim: ai ts=4 sts=4 et sw=4 ft=python fdm=indent et foldlevel=0

# fabric task file for deploying a single node mesos cluster
#
# usage:
#       fab help
#
from envassert import (process,
                       package,
                       detect,
                       port)
from fabric.api import sudo, task, env, run
from fabric.context_managers import hide

from bookshelf.api_v1 import (apt_install,
                              log_green,
                              install_os_updates,
                              install_vagrant,
                              install_vagrant_plugin,
                              enable_apt_repositories,
                              install_mesos_single_box_mode,
                              install_virtualbox,
                              update_system_pip_to_latest_pip)


class MyCookbooks():
    """ Collection of helpers for fabric tasks

    Contains a collection of helper functions for fabric task used in this
    fabfile.
    List them a-z if you must.
    """

    def acceptance_tests(self, distribution):
        """ checks that the mesos cluster is configured correctly
            :param string distribution: which OS to use 'ubuntu1404'
        """

        # required for our acceptance tests using envassert
        env.platform_family = detect.detect()

        if 'ubuntu' in distribution:
            # make sure we installed all the packages we need
            log_green('assert that required deb packages are installed')
            for pkg in self.ubuntu14_required_packages():
                log_green('... checking package: %s' % pkg)
                assert package.installed(pkg)

            # the acceptance tests look for a package in a yum repository,
            # we provide one by starting a webserver and pointing the tests
            # to look over there.
            # for that we need 'nginx' installed and running
            log_green('check that nginx is running')
            assert package.installed('nginx')
            assert port.is_listening(80, "tcp")
            assert process.is_up("nginx")
            with hide('running', 'stdout'):
                assert 'nginx' in run('ls -l /etc/init.d/')

            # check that mesos is installed
            log_green('check that zookeeper is running')
            assert package.installed('zookeeper')
            assert port.is_listening('2181', "tcp")
            with hide('running', 'stdout'):
                assert 'zookeeper' in run('ls -l /etc/init/')

            log_green('check that mesos-master is running')
            assert package.installed('mesos')
            assert port.is_listening('5050', "tcp")
            with hide('running', 'stdout'):
                assert 'mesos-master' in run('ls -l /etc/init/')

            log_green('check that mesos-slave is running')
            assert package.installed('mesos')
            assert port.is_listening('5051', "tcp")
            with hide('running', 'stdout'):
                assert 'mesos-slave' in run('ls -l /etc/init/')

            log_green('check that marathon is running')
            assert package.installed('marathon')
            assert port.is_listening('8080', "tcp")
            with hide('running', 'stdout'):
                assert 'marathon' in run('ls -l /etc/init/')

            log_green('check that virtualbox is installed ')
            assert package.installed('virtualbox-5.0')
            with hide('running', 'stdout'):
                assert 'vboxdrv' in sudo('lsmod')

            log_green('check that vagrant is installed ')
            assert package.installed('vagrant')

            log_green('check that vagrant plugins are installed ')
            with hide('running', 'stdout'):
                assert 'vagrant-reload' in sudo('vagrant plugin list')

            # update pip
            # We have a devpi cache in AWS which we will consume instead of
            # going upstream to the PyPi servers.
            # We specify that devpi caching server using -i \$PIP_INDEX_URL
            # which requires as to include --trusted_host as we are not (yet)
            # using  SSL on our caching box.
            # The --trusted-host option is only available with pip 7
            log_green('check that pip is the latest version')
            with hide('running', 'stdout'):
                assert '7.' in run('pip --version')

    def bootstrap_mesos_on_ubuntu14(self):
        log_green('enabling APT repositories ...')
        enable_apt_repositories('deb',
                                'http://archive.ubuntu.com/ubuntu',
                                '$(lsb_release -sc)',
                                'main universe restricted multiverse')

        log_green('installing OS updates...')
        install_os_updates(distribution='ubuntu14.04')

        log_green('installing required packages...')
        apt_install(packages=self.ubuntu14_required_packages())

        log_green('installing mesos on a single node...')
        install_mesos_single_box_mode(distribution='ubuntu14.04')

        # to use wheels, we want the latest pip
        log_green('updating pip...')
        update_system_pip_to_latest_pip()

        # nginx is used during the acceptance tests, the VM built by
        # flocker provision will connect to the jenkins slave on p 80
        # and retrieve the just generated rpm/deb file
        log_green('installing virtualbox 5...')
        install_virtualbox(distribution='ubuntu14.04')

        log_green('installing vagrant 1.7.4...')
        install_vagrant('ubuntu1404', '1.7.4')
        install_vagrant_plugin('vagrant-reload')

    def ubuntu14_required_packages(self):
        packages = ["apt-transport-https",
                    "software-properties-common",
                    "build-essential",
                    "python-virtualenv",
                    "desktop-file-utils",
                    "git",
                    "python-dev",
                    "python-tox",
                    "python-virtualenv",
                    "libffi-dev",
                    "libssl-dev",
                    "wget",
                    "curl",
                    "openjdk-7-jre-headless",
                    "libffi-dev",
                    "lintian",
                    "ntp",
                    "rpm2cpio",
                    "createrepo",
                    "libexpat1-dev",
                    "libcurl4-openssl-dev",
                    "zlib1g-dev",
                    "libwww-curl-perl",
                    "libssl-dev",
                    "nginx",
                    "libsvn-perl",
                    "ruby-dev"]
        return packages


@task(default=True)
def help():
    """ help """
    print("""
          usage: fab -H <hostname> -i <path-to-private-key> <action>[:arguments]

            # shows this page
            $ fab help

            # does the whole thing in one go
            $ fab it:distribution=ubuntu14.04'

            # installs packages on an existing instance
            $ fab bootstrap:distribution=ubuntu14.04'

            # run acceptance tests against new instance
            $ fab tests

            metadata state is stored locally in state.json.
          """)


@task
def it(distribution):
    """ runs the full stack
    :param string distribution: which OS to use 'ubuntu1404'
    """
    bootstrap(distribution)
    tests(distribution)


@task
def bootstrap(distribution):
    """ bootstraps an existing running instance
    :param string distribution: which OS to use ubuntu1404'
    """
    cookbook = MyCookbooks()
    if 'ubuntu14.04' in distribution:
        cookbook.bootstrap_mesos_on_ubuntu14()


@task
def tests(distribution):
    """ run tests against an existing instance """
    cookbook.acceptance_tests(distribution=distribution)


"""
    ___main___
"""
cookbook = MyCookbooks()

# Modify some global Fabric behaviours:
# Let's disable known_hosts, since on Clouds that behaviour can get in the
# way as we continuosly destroy/create boxes.
env.disable_known_hosts = True
env.use_ssh_config = False
env.eagerly_disconnect = True
env.connection_attemtps = 5
env.user = 'root'
