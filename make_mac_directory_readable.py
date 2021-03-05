#!/usr/bin/env python3

import subprocess
import plistlib
import argparse
import datetime
import sqlite3
import time
import os

# Global Variables
global_dict = {}
Indent_Level = int(16)
Output_Set = set()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', help='Target Directory Path', type=str, required=True)
    arguments = parser.parse_args()
    return arguments


def convert_sqlite3_to_sql_dict(_path):
    result_dict = {}
    conn = sqlite3.connect(_path)
    cursor = conn.cursor()
    cursor.execute('SELECT name from sqlite_master where type="table"')
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        qry = f'SELECT * from "{table_name}"'
        cursor.execute(qry)
        contents = cursor.fetchall()
        for content in contents:
            uuid = content[0]
            key = f'{table_name}_{uuid}'
            result_dict[key] = content
    return result_dict


def get_filetype(_file_path):
    process = subprocess.run(['file', _file_path], check=True, stdout=subprocess.PIPE, universal_newlines=True)
    output = f'{process.stdout}'.lower().split(':')[1]
    if 'apple binary property list' in output:              # For Official Apple Plists
        return 'plist'
    if 'sqlite 3.x database' in output:                     # For SQLite3 Database
        return 'sqlite3'
    if 'xml 1.0 document text' in output:                   # For XML Files
        return 'xml'
    if 'data' in output and len(output) < 7:
        return 'data'
    return None


def parse_plist(_path):
    process = subprocess.run(['/usr/libexec/PlistBuddy', '-x', '-c', 'Print', _path],
                             check=True, stdout=subprocess.PIPE, universal_newlines=True)
    return f'{process.stdout}'.lower().split(':')[1]


def parse_sqlite3(_path):
    return convert_sqlite3_to_sql_dict(_path)


def parse_generic(_path):
    process = subprocess.run(['cat', _path], check=True, stdout=subprocess.PIPE, universal_newlines=True)
    return f'{process.stdout}'.lower().split(':')[1]


def parse_binary(_path):
    process = subprocess.run(['strings', '-n', '5', _path], check=True, stdout=subprocess.PIPE, universal_newlines=True)
    try:
        return f'{process.stdout}'.lower().split(':')
    except Exception as e:
        print(f'[-] Error: {e}')
        return '!OUTPUT FAILED TO BE READ!\n'


def global_filter(_obj):
    global Indent_Level, Output_Set
    if isinstance(_obj, str):
        Output_Set.add(f'{_obj}\n')
    elif isinstance(_obj, (datetime.date, datetime.date)):
        Output_Set.add(f'\t{" " * Indent_Level}[i] TIMESTAMP:\t{_obj}\n')
    elif isinstance(_obj, (float, int, complex)):
        Output_Set.add(f'\t{" " * Indent_Level}{_obj}\n')
    elif isinstance(_obj, (list, set, slice, tuple)):
        for _item in _obj:
            global_filter(_item)
    elif isinstance(_obj, dict):
        for _entry in _obj:
            Output_Set.add(f'\t{_entry}\n')
            global_filter(_obj[_entry])
    elif isinstance(_obj, (bytes, bytearray)):
        try:
            return global_filter(plistlib.loads(_obj, fmt=None, dict_type=dict))
        except Exception as e:
            return global_filter(_obj.decode('utf-8', errors='ignore'))
    if not isinstance(_obj, (list, set, slice, tuple)):
        Output_Set.add(f'{"*" * 120}\n')
    return Output_Set


def generate_report(_global_dict, _dir):
    global Output_Set
    report_name = f'{time.strftime("%Y%m%d-%H%M%S")}_{_dir}_report'
    folder_name = report_name[1:128] if len(report_name) > 128 else report_name.replace('/', '_')
    os.mkdir(f'/tmp/{folder_name}')
    for entry in _global_dict:
        file_out = open(f'/tmp/{folder_name}/{entry.replace("/", "_")}', 'w')
        Output_Set = set()
        _data_set = global_filter(_global_dict[entry]['data'])
        _data = _global_dict[entry]['data']
        for _entry in _data:
            print(_entry)
            file_out.write(f'{_entry}\n')
        file_out.close()
    print(f'[+] Report Generated. Please see the following location for converted files:\n[^] `/tmp/{folder_name}`\n')


def cycle(_path):
    global global_dict
    for _root, _dirs, _files in os.walk(_path):
        if _files:
            for _file in _files:
                target_path = f'{_root}/{_file}'
                file_type = get_filetype(target_path)
                if file_type == 'plist':
                    global_dict[target_path] = {'data': parse_plist(target_path), 'type': file_type}
                if file_type == 'sqlite3':
                    global_dict[target_path] = {'data': parse_sqlite3(target_path), 'type': file_type}
                if file_type == 'xml':
                    global_dict[target_path] = {'data': parse_generic(target_path), 'type': file_type}
                if file_type == 'data':
                    global_dict[target_path] = {'data': parse_binary(target_path), 'type': file_type}
        if _dirs:
            for _dir in _dirs:
                cycle(f'{_path}/{_dir}')


def main():
    global global_dict
    args = parse_args()
    cycle(args.directory)
    generate_report(global_dict, args.directory)


if __name__ == '__main__':
    main()
