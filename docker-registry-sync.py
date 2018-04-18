#!/usr/bin/python

import argparse
import os
import sys
import urllib2
import json

def retrieve_repositories_tags_all(source_registry):
    repos = []
    try:
        resp = urllib2.urlopen('http://%s/v2/_catalog' %(source_registry))
        data = json.loads(resp.read())
        repos = data['repositories']
    except urllib2.HTTPError:
        pass
    images = []
    for repo in repos:
        images.extend(retrieve_repositories_tags(source_registry, repo))
    return (images)

def retrieve_repositories_tags_by_file(source_registry, filename):
    images = []
    if (not os.path.exists(filename)):
        print("Cannot file configuration for image sync: %s" % filename)
        sys.exit(1)
    lines = [line.strip() for line in open(filename)]
    for line in lines:
        if line.startswith('#'):
            continue
        if line == "":
            continue
        if line.rfind(":") > 0:
            images.append(line)
        else:
            images.extend(retrieve_repositories_tags(source_registry, line))
    return images

def retrieve_repositories_tags(source_registry, repo):
    images = []
    try:
        resp = urllib2.urlopen('http://%s/v2/%s/tags/list' %(source_registry,repo))
        data = json.loads(resp.read())
        name = data['name']
        for tag in data['tags']:
            images.append("%s:%s"%(name,tag))
    except urllib2.HTTPError:
        pass
    return images

def dry_run_print_docker_commands(source_registry, target_registry, images):
    for image in images:
        print("docker pull %s/%s" % (source_registry, image))
        print("docker tag %s/%s %s/%s" % (source_registry, image, target_registry, image))
        print("docker push %s/%s" % (target_registry, image))
        print("")

# TODO: exec docker commands
def exec_sync_docker_commands(source_registry,target_registry, images):
    for image in images:
        print("sync image %s/%s" % (source_registry, image))
        #os.popen( "docker pull %s/%s" % (source_registry, image)).read()
        #os.popen( "docker tag %s/%s %s/%s" % (source_registry, image, target_registry, image)).read()
        #os.popen( "docker push %s/%s" % (target_registry, image)).read()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Syncs images from a source registry to target registry.',
                                             epilog='\nSample usage: --from=<source-registry> '
                                             '--to=<target-registry>',
                                             formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--from', action='store', dest='source_registry', help='The source registry hostname',
                    required=True)
    parser.add_argument('--to', action='store', dest='target_registry', help='The target registry hostname',
                    required=True)
    parser.add_argument('--file', action='store', dest='images_file', help='The images list, each image a line')
    parser.add_argument('--dry-run', action='store_true', dest='dry_run', help='If this flag is present, commands will be'
                                                                         'dumped to stdout instead of run')
    options = parser.parse_args()

    if options.images_file:
        images = retrieve_repositories_tags_by_file(options.source_registry, options.images_file)
    else:
        images = retrieve_repositories_tags_all(options.source_registry)

    if options.dry_run:
        dry_run_print_docker_commands(options.source_registry,options.target_registry, images)
    else:
        exec_sync_docker_commands(options.source_registry,options.target_registry, images)