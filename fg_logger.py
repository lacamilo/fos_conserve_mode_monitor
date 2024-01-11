#!/usr/bin/env python3

import logging
import re


# https://docs.python.org/3/howto/logging.html

def configure_logger(log_file, log_level):
    log = logging.getLogger('fortigate_logger')
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    return log


def remove_special_chars(text):
    pattern = r'[^\x20-\x7E\n\r\t]'
    clean_text = re.sub(pattern, '', text)
    return clean_text


def remove_last_line(text):
    lines = text.splitlines()
    if len(lines) > 1:
        return "\n".join(lines[:-1])
    return text

def print_fixed_top_row(header, data):
    # Print the fixed top row (header)
    print('\t'.join(header))

    # Print the data rows
    for row in data:
        print('\t'.join(map(str, row)))