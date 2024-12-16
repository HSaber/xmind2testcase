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
    fileheader = ["测试用例类型(template)","用例名称(name)", "业务线(business)","描述(description)","前置条件(field_f717b4)","执行步骤(field_023f96)", "预期结果(field_2c7371)", "附件(field_603db5)","标签(field_65e1cc)",
                  "用例分级(field_ad0ad4)","关联需求(field_d73be1)","用例类型(field_e42a97)", "创建人(owner)","优先级(priority)","关注人(watchers)","拉群方式选择(group_type)","流程角色(role_owners)","当前状态(work_item_status)","自增数字(auto_number)","是否冻结(is_frozen)","当前状态开始时间(status_begin_time)"]

    feishu_testcase_rows = [fileheader]
    feishu_testcase_rows.append(['','','','','','','','','','','','','','','','','','','负责人(test_case_owner)','','',''])
    for testcase in testcases:
        row = gen_a_testcase_row(testcase)
        feishu_testcase_rows.append(row)

    feishu_file = xmind_file[:-6] + '.csv'
    if os.path.exists(feishu_file):
        os.remove(feishu_file)
        # logging.info('The feishu csv file already exists, return it directly: %s', feishu_file)
        # return feishu_file

    with open(feishu_file, 'w',newline='', encoding='utf8') as f:
        writer = csv.writer(f)
        writer.writerows(feishu_testcase_rows)
        logging.info('Convert XMind file(%s) to a feishu csv file(%s) successfully!', xmind_file, feishu_file)

    return feishu_file


def gen_a_testcase_row(testcase_dict):
    product=gen_case_module(testcase_dict['product'])
    logging.info(product)
    if product.__contains__('_'):
        case_story=product.split('_')[0]
        case_owner=product.split('_')[1]
    else:
        case_story=product
        case_owner=''
    case_title = gen_case_module(testcase_dict['suite'])+">"+testcase_dict['name']
    case_jobtype='默认测试用例类型'
    case_business=''
    case_description=''
    case_precontion = testcase_dict['preconditions']
    case_step, case_expected_result = gen_case_step_and_expected_result(testcase_dict['steps'])
    case_attach = ''
    case_tag=''
    case_priority = gen_case_priority(testcase_dict['importance'])
    case_type = gen_case_type(testcase_dict['execution_type'])
 #   case_type= '功能测试'
    case_group='不拉群'
    case_status='评审通过'
    row = [case_jobtype, case_title, case_business,case_description,case_precontion,
           case_step,case_expected_result, case_attach,case_tag,case_step,
           case_expected_result,case_priority, case_story, case_type,case_owner,
           case_priority,case_owner,case_group,case_owner,case_status]
    # logging.info('row : %s',row)
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
 #   return caseowener=case_type.split('_')
    if case_type in mapping.keys():
        return mapping[case_type]
    else:
        return '功能用例'

# def gen_case_type(case_type):
#     mapping = {1: '功能用例', 2: '性能用例'}
#     if case_type in mapping.keys():
#         return mapping[case_type]
#     else:
#         return '功能用例'


if __name__ == '__main__':
    xmind_file = '../docs/feishu_testcase_template.xmind'
    feishu_csv_file = xmind_to_feishu_csv_file(xmind_file)
    print('Conver the xmind file to a feishu csv file succssfully: %s', feishu_csv_file)