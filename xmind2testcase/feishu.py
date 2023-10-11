#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import csv
import logging
import os
from xmind2testcase.utils import get_xmind_testcase_list, get_absolute_path

"""
Convert XMind fie to feishu testcase csv file 

feishu official document about import CSV testcase file: https://www.feishu.net/book/feishupmshelp/243.mhtml 
"""


def xmind_to_feishu_csv_file(xmind_file):
    """Convert XMind file to a feishu csv file"""
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to feishu file...', xmind_file)
    testcases = get_xmind_testcase_list(xmind_file)

#    fileheader = ["所属模块", "用例标题", "前置条件", "步骤", "预期", "关键词", "优先级", "用例类型", "适用阶段","负责人"]
    fileheader = ["工作项类型","用例名称", "业务线","描述","前置条件",
                  "执行步骤", "预期结果", "附件","标签", "步骤",
                  "结果预期", "用例分级","关联需求","用例类型", "创建人",
                  "优先级","关注人","拉群方式选择","流程角色","状态"]

    feishu_testcase_rows = [fileheader]
    feishu_testcase_rows.append(['','','','','','','','','','','','','','','','','','','负责人',''])
    for testcase in testcases:
        row = gen_a_testcase_row(testcase)
        feishu_testcase_rows.append(row)

    feishu_file = xmind_file[:-6] + '.csv'
    if os.path.exists(feishu_file):
        os.remove(feishu_file)
        # logging.info('The feishu csv file already exists, return it directly: %s', feishu_file)
        # return feishu_file

    with open(feishu_file, 'w', encoding='utf8') as f:
        writer = csv.writer(f)
        writer.writerows(feishu_testcase_rows)
        logging.info('Convert XMind file(%s) to a feishu csv file(%s) successfully!', xmind_file, feishu_file)

    return feishu_file


def gen_a_testcase_row(testcase_dict):
    case_title = gen_case_module(testcase_dict['suite'])+"-"+testcase_dict['name']
    case_jobtype='默认测试用例类型'
    case_business='交易'
    case_description=''
    case_precontion = testcase_dict['preconditions']
    case_step, case_expected_result = gen_case_step_and_expected_result(testcase_dict['steps'])
    case_attach = ''
    case_tag=''
    case_priority = gen_case_priority(testcase_dict['importance'])
    case_type = gen_case_type(testcase_dict['execution_type'])
 #   case_type= '功能测试'
    case_owner='胡欢'
    case_story='15715591'
    case_group='不拉群'
    case_status='待评审'
    row = [case_jobtype, case_title, case_business,case_description,case_precontion,
           case_step,case_expected_result, case_attach,case_tag,case_step,
           case_expected_result,case_priority, case_story, case_type,case_owner,
           case_priority,case_owner,case_group,case_owner,case_status]
    return row

def gen_case_module(module_name):
    if module_name:
        module_name = module_name.replace('（', '(')
        module_name = module_name.replace('）', ')')
    else:
        module_name = '/'
    return module_name


def gen_case_step_and_expected_result(steps):
    case_step = ''
    case_expected_result = ''

    for step_dict in steps:
        case_step += str(step_dict['step_number']) + '. ' + step_dict['actions'].replace('\n', '').strip() + '\n'
        case_expected_result += str(step_dict['step_number']) + '. ' + \
            step_dict['expectedresults'].replace('\n', '').strip() + '\n' \
            if step_dict.get('expectedresults', '') else ''

    return case_step, case_expected_result


def gen_case_priority(priority):
    mapping = {1: 'P0', 2: 'P1', 3: 'P2'}
    if priority in mapping.keys():
        return mapping[priority]
    else:
        return 'P1'


def gen_case_type(case_type):
    mapping = {1: '功能用例', 2: '性能用例'}
    if case_type in mapping.keys():
        return mapping[case_type]
    else:
        return '功能用例'


if __name__ == '__main__':
    xmind_file = '../docs/feishu_testcase_template.xmind'
    feishu_csv_file = xmind_to_feishu_csv_file(xmind_file)
    print('Conver the xmind file to a feishu csv file succssfully: %s', feishu_csv_file)