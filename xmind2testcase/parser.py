#!/usr/bin/env python
# _*_ coding:utf-8 _*_

import logging
from xmind2testcase.metadata import TestSuite, TestCase, TestStep

config = {
    'sep': ' ',
    'valid_sep': '&>+/-',
    'precondition_sep': '\n----\n',
    'summary_sep': '\n----\n',
    'ignore_char': '#!！'
}


def xmind_to_testsuites(xmind_content_dict):
    """convert xmind file to `xmind2testcase.metadata.TestSuite` list"""
    suites = []
    print(
      f"\n DEBUG >>> 1. 开始解析 XMind，共收到 {len(xmind_content_dict)} 个 Sheet"
  )

    for sheet in xmind_content_dict:
        sheet_title = sheet.get('title', 'Sheet')
        logging.debug('start to parse a sheet: %s', sheet_title)
        root_topic = sheet.get('topic', {})
        sub_topics = root_topic.get('topics', [])
        print(
        f" DEBUG >>> 2. Sheet 名称: [{sheet_title}], 根节点:"
        f" [{root_topic.get('title')}], 子主题数量: {len(sub_topics)}"
    )

        if sub_topics:
            root_topic['topics'] = filter_empty_or_ignore_topic(sub_topics)
        else:
            logging.warning('This is a blank sheet(%s), should have at least 1 sub topic(test suite)', sheet_title)
            continue
        suite = sheet_to_suite(root_topic)
        logging.debug('sheet(%s) parsing complete: %s', sheet_title, suite.to_dict())
        suites.append(suite)

    return suites


def filter_empty_or_ignore_topic(topics):
    """filter blank or start with config.ignore_char topic"""
    result = []
    for topic in topics:
        title = topic.get('title')
        if title is not None and title.strip() != '' and title[0] not in config['ignore_char']:
            result.append(topic)

    for topic in result:
        sub_topics = topic.get('topics', [])
        if sub_topics:
            topic['topics'] = filter_empty_or_ignore_topic(sub_topics)

    return result


def filter_empty_or_ignore_element(values):
    """Filter all empty or ignore XMind elements, especially notes、comments、labels element"""
    result = []
    for value in values:
        if isinstance(value, str) and not value.strip() == '' and not value[0] in config['ignore_char']:
            result.append(value.strip())
    return result


def sheet_to_suite(root_topic):
    """convert a xmind sheet to a `TestSuite` instance"""
    suite = TestSuite()
    root_title = root_topic.get('title', '')
    separator = root_title[-1] if root_title else ' '

    if separator in config['valid_sep']:
        logging.debug('find a valid separator for connecting testcase title: %s', separator)
        config['sep'] = separator
        root_title = root_title[:-1]
    else:
        config['sep'] = ' '

    suite.name = root_title
    suite.details = root_topic.get('note', '') or ''
    suite.sub_suites = []

    for suite_dict in root_topic.get('topics', []):
        suite.sub_suites.append(parse_testsuite(suite_dict))

    return suite


def parse_testsuite(suite_dict):
    testsuite = TestSuite()
    testsuite.name = suite_dict.get('title', '')
    testsuite.details = suite_dict.get('note', '') or ''
    testsuite.testcase_list = []
    logging.debug('start to parse a testsuite: %s', testsuite.name)

    for cases_dict in suite_dict.get('topics', []):
        for case in recurse_parse_testcase(cases_dict):
            testsuite.testcase_list.append(case)

    logging.debug('testsuite(%s) parsing complete: %s', testsuite.name, testsuite.to_dict())
    return testsuite


def recurse_parse_testcase(case_dict, parent=None):
    if is_testcase_topic(case_dict):
        case = parse_a_testcase(case_dict, parent)
        yield case
    else:
        if parent is None:
            parent = []

        parent.append(case_dict)

        for child_dict in case_dict.get('topics', []):
            for case in recurse_parse_testcase(child_dict, parent):
                yield case

        parent.pop()


def is_testcase_topic(case_dict):
    """A topic with a priority marker, or no subtopic, indicates that it is a testcase"""
    priority = get_priority(case_dict)
    if priority:
        return True

    children = case_dict.get('topics', [])
    if children:
        return False

    return True


def parse_a_testcase(case_dict, parent):
    testcase = TestCase()
    topics = parent + [case_dict] if parent else [case_dict]

    testcase.name = gen_testcase_title(topics)

    preconditions = gen_testcase_preconditions(topics)
    testcase.preconditions = preconditions if preconditions else '无'

    summary = gen_testcase_summary(topics)
    testcase.summary = summary if summary else testcase.name
    testcase.execution_type = get_execution_type(topics)
    testcase.importance = get_priority(case_dict) or 2

    step_dict_list = case_dict.get('topics', [])
    if step_dict_list:
        testcase.steps = parse_test_steps(step_dict_list)

    markers = (
      case_dict.get("makers")
      or case_dict.get("maker")
      or case_dict.get("markers")
      or []
  )
    testcase.result = get_test_result(markers)
    print(
      f"   发现有效用例 -> 标题: {testcase.name} | 优先级:"
      f" P{testcase.importance-1}"
  )

    if testcase.result == 0 and testcase.steps:
        for step in testcase.steps:
            if step.result == 2:
                testcase.result = 2
                break
            if step.result == 3:
                testcase.result = 3
                break

            testcase.result = step.result

    logging.debug('finds a testcase: %s', testcase.to_dict())
    return testcase


def get_execution_type(topics):
    labels = []
    for topic in topics:
        l = topic.get('label') or topic.get('labels') or ''
        if isinstance(l, list):
            labels.extend(l)
        elif isinstance(l, str) and l:
            labels.append(l)

    labels = filter_empty_or_ignore_element(labels)
    exe_type = 1
    for item in labels[::-1]:
        if item.lower() in ['自动', 'auto', 'automate', 'automation']:
            exe_type = 2
            break
        if item.lower() in ['手动', '手工', 'manual']:
            exe_type = 1
            break
    return exe_type


def get_priority(case_dict):
    """Get the topic's priority（兼容 makers/maker/markers 和 priority-1）"""
    markers = case_dict.get('makers') or case_dict.get('maker') or case_dict.get('markers') or []
    if isinstance(markers, list):
        for marker in markers:
            marker_str = str(marker)
            if 'priority' in marker_str:
                try:
                    return int(marker_str[-1])
                except ValueError:
                    pass
    return None


def gen_testcase_title(topics):
    """Link all topic's title as testcase title"""
    titles = [topic.get('title', '') for topic in topics if topic.get('title')]
    titles = filter_empty_or_ignore_element(titles)

    separator = config['sep']
    if separator != ' ':
        separator = ' {} '.format(separator)

    return separator.join(titles)


def gen_testcase_preconditions(topics):
    notes = [topic.get('note', '') for topic in topics if topic.get('note')]
    notes = filter_empty_or_ignore_element(notes)
    return config['precondition_sep'].join(notes)


def gen_testcase_summary(topics):
    comments = [topic.get('comment', '') or topic.get('comments', '') for topic in topics if topic.get('comment') or topic.get('comments')]
    comments = filter_empty_or_ignore_element(comments)
    return config['summary_sep'].join(comments)


def parse_test_steps(step_dict_list):
    steps = []

    for step_num, step_dict in enumerate(step_dict_list, 1):
        test_step = parse_a_test_step(step_dict)
        test_step.step_number = step_num
        steps.append(test_step)

    return steps


def parse_a_test_step(step_dict):
    test_step = TestStep()
    test_step.actions = step_dict.get('title', '')

    expected_topics = step_dict.get('topics', [])
    if expected_topics:
        expected_topic = expected_topics[0]
        test_step.expectedresults = expected_topic.get('title', '')
        markers = expected_topic.get('makers') or expected_topic.get('maker') or expected_topic.get('markers') or []
        test_step.result = get_test_result(markers)
    else:
        markers = step_dict.get('makers') or step_dict.get('maker') or step_dict.get('markers') or []
        test_step.result = get_test_result(markers)

    logging.debug('finds a teststep: %s', test_step.to_dict())
    return test_step


def get_test_result(markers):
    """test result: non-execution:0, pass:1, failed:2, blocked:3, skipped:4"""
    if isinstance(markers, list):
        markers_str = [str(m) for m in markers]
        if any(m in markers_str for m in ['symbol-right', 'c_simbol-right', 'right']):
            return 1
        elif any(m in markers_str for m in ['symbol-wrong', 'c_simbol-wrong', 'wrong']):
            return 2
        elif any(m in markers_str for m in ['symbol-pause', 'c_simbol-pause', 'pause']):
            return 3
        elif any(m in markers_str for m in ['symbol-minus', 'c_simbol-minus', 'minus']):
            return 4
    return 0