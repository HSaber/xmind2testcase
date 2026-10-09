#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import json
import os
import xmind
import logging
from xmind2testcase.parser import xmind_to_testsuites
from xmindparser import xmind_to_dict


def get_absolute_path(path):
    """
        Return the absolute path of a file

        If path contains a start point (eg Unix '/') then use the specified start point
        instead of the current working directory. The starting point of the file path is
        allowed to begin with a tilde "~", which will be replaced with the user's home directory.
    """
    fp, fn = os.path.split(path)
    if not fp:
        fp = os.getcwd()
    fp = os.path.abspath(os.path.expanduser(fp))
    return os.path.join(fp, fn)


def get_xmind_testsuites(xmind_file):
    """Load the XMind file and parse to `xmind2testcase.metadata.TestSuite` list"""
    xmind_file = get_absolute_path(xmind_file)
    try:
        xmind_content_dict = xmind_to_dict(xmind_file)
    except Exception as e:
        logging.error('Failed to parse XMind file(%s): %s', xmind_file, e)
        return []
    logging.debug("loading XMind file(%s) dict data: %s", xmind_file, xmind_content_dict)

    if xmind_content_dict:
        testsuites = xmind_to_testsuites(xmind_content_dict)
        return testsuites
    else:
        logging.error('Invalid XMind file(%s): it is empty!', xmind_file)
        return []


def get_xmind_testsuite_list(xmind_file):
    """Load the XMind file and get all testsuite in it (支持任意深度层级嵌套)

    :param xmind_file: the target XMind file
    :return: a list of testsuite data
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testsuite data list...', xmind_file)
    testsuite_list = get_xmind_testsuites(xmind_file)
    suite_data_list = []

    def calculate_statistics(suite):
        """递归计算节点及其所有子节点的测试用例统计信息"""
        stats = {'case_num': 0, 'non_execution': 0, 'pass': 0, 'failed': 0, 'blocked': 0, 'skipped': 0}
        
        # 1. 统计当前套件直接包含的用例
        if hasattr(suite, 'testcase_list') and suite.testcase_list:
            for case in suite.testcase_list:
                stats['case_num'] += 1
                if case.result == 0:
                    stats['non_execution'] += 1
                elif case.result == 1:
                    stats['pass'] += 1
                elif case.result == 2:
                    stats['failed'] += 1
                elif case.result == 3:
                    stats['blocked'] += 1
                elif case.result == 4:
                    stats['skipped'] += 1
                else:
                    logging.warning('This testcase result is abnormal: %s, please check it: %s', case.result, case.to_dict())

        # 2. 递归统计子套件 (sub_suites) 的用例
        if hasattr(suite, 'sub_suites') and suite.sub_suites:
            for sub_suite in suite.sub_suites:
                sub_stats = calculate_statistics(sub_suite)
                for key in stats:
                    stats[key] += sub_stats[key]

        suite.statistics = stats
        return stats

    for testsuite in testsuite_list:
        # 对每一个根套件进行递归统计
        calculate_statistics(testsuite)
        suite_data_list.append(testsuite.to_dict())

    logging.info('Convert XMind file(%s) to testsuite data list successfully!', xmind_file)
    return suite_data_list


def get_xmind_testcase_list(xmind_file):
    """Load the XMind file and get all testcase in it

    :param xmind_file: the target XMind file
    :return: a list of testcase data
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testcases dict data...', xmind_file)
    testsuites = get_xmind_testsuites(xmind_file)
    testcases = []

    for testsuite in testsuites:
        product = testsuite.name
        for suite in testsuite.sub_suites:
            for case in suite.testcase_list:
                case_data = case.to_dict()
                case_data['product'] = product
                case_data['suite'] = suite.name
                testcases.append(case_data)

    logging.info('Convert XMind file(%s) to testcases dict data successfully!', xmind_file)
    return testcases


def xmind_testsuite_to_json_file(xmind_file):
    """Convert XMind file to a testsuite json file"""
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testsuites json file...', xmind_file)
    testsuites = get_xmind_testsuite_list(xmind_file)
    testsuite_json_file = xmind_file[:-6] + '_testsuite.json'

    if os.path.exists(testsuite_json_file):
        os.remove(testsuite_json_file)
        # logging.info('The testsuite json file already exists, return it directly: %s', testsuite_json_file)
        # return testsuite_json_file

    with open(testsuite_json_file, 'w', encoding='utf8') as f:
        f.write(json.dumps(testsuites, indent=4, separators=(',', ': '), ensure_ascii=False))
        logging.info('Convert XMind file(%s) to a testsuite json file(%s) successfully!', xmind_file, testsuite_json_file)

    return testsuite_json_file


def xmind_testcase_to_json_file(xmind_file):
    """Convert XMind file to a testcase json file"""
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testcases json file...', xmind_file)
    testcases = get_xmind_testcase_list(xmind_file)
    testcase_json_file = xmind_file[:-6] + '.json'

    if os.path.exists(testcase_json_file):
        os.remove(testcase_json_file)
        # logging.info('The testcase json file already exists, return it directly: %s', testcase_json_file)
        # return testcase_json_file

    with open(testcase_json_file, 'w', encoding='utf8') as f:
        f.write(json.dumps(testcases, indent=4, separators=(',', ': '), ensure_ascii=False))
        logging.info('Convert XMind file(%s) to a testcase json file(%s) successfully!', xmind_file, testcase_json_file)

    return testcase_json_file
