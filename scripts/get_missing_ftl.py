#!/usr/bin/env python3

# Until we have some nicer interface for managing translations
# that supports FTL syntax well. (Pontoon doesn't work great
# yet for complex messages)

# 1. Locate missing messages using compare locales

# 2. Parse original English files for each
#
# 3. Go through and remove any message that is not
#    in the missing one
#
# 3. Locate message, along with comments, and previous
#    headings

import argparse
import json
import os.path
import subprocess

from fluent.syntax import ast
from fluent.syntax import parse as parse_fluent
from fluent.syntax import serialize as serialize_fluent

parser = argparse.ArgumentParser()
parser.add_argument('language')


BASE_DIRECTORY = 'learnscripture/locales/{0}/learnscripture'
PRIMARY_LANGUAGE = 'en'


def main(language):
    s = subprocess.check_output(['compare-locales', 'l10n.toml', '.', '--json', '-']).decode('utf-8')
    data = json.loads(s)[0]
    directory = BASE_DIRECTORY.format(language)
    files = data['details'][directory]
    output = []
    for filename, problems in sorted(files.items()):
        output.append("\n### File: {}\n".format(filename))
        missing = set()
        for item in problems:
            if 'missingEntity' in item:
                missing.add(item['missingEntity'])

        d = open(os.path.join(BASE_DIRECTORY.format(PRIMARY_LANGUAGE), filename)).read()
        resource = parse_fluent(d)
        resource_body = []
        # Pass one - remove messages that are not missing
        for item in resource.body:
            if isinstance(item, ast.Message) and item.id.name not in missing:
                continue
            resource_body.append(item)
        # Pass two - remove irrelevant group comments
        resource_body_2 = []
        # Note reverse order processing
        for item in reversed(resource_body):
            if isinstance(item, ast.Message):
                resource_body_2.insert(0, item)
                # Add extra whitespace to make it format nicer at the end
                if not item.attributes:
                    item.value.elements.append(ast.TextElement("\n"))
            elif isinstance(item, ast.ResourceComment):
                resource_body_2.insert(0, item)
            elif isinstance(item, ast.GroupComment):
                if resource_body_2 and isinstance(resource_body_2[0], ast.Message):
                    resource_body_2.insert(0, item)

        resource.body = resource_body_2
        output.append(serialize_fluent(resource))
    return ''.join(output)


if __name__ == '__main__':
    args = parser.parse_args()
    print(main(args.language))
