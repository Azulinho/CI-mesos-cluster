contains fabric code to build a single node mesos cluster
Use it with a base-metal box.

usage:

clone the following repos:


```
     git clone git@github.com:ClusterHQ/CI-mesos-cluster
     cd CI-mesos-cluster
     git clone git@github.com:ClusterHQ/segredos.git segredos
```

create your virtualenv:

```
    virtualenv2 venv
    . venv/bin/activate
    pip2 install -r requirements.txt --upgrade

```

then execute as:

```
    fab -H <host> -i private.pem it:distribution=centos7
    fab destroy
    fab -H <host> -i private.pem it:distribution=ubuntu14.04

    fab help

    Available commands:

        bootstrap     bootstraps an existing running instance
        help          help
        it            runs the full stack
        tests         run tests against an existing instance

```

The fab code should bootstrap an existing instance with a running mesos cluster
suitable for running virtualbox CI jobs