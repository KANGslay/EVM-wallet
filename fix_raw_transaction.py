#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
此脚本用于将blockchain.py文件中的rawTransaction替换为raw_transaction
'''

import os

def fix_raw_transaction(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有的rawTransaction为raw_transaction
    updated_content = content.replace('rawTransaction', 'raw_transaction')
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f'文件 {file_path} 已更新。')

if __name__ == '__main__':
    blockchain_path = 'app/services/blockchain.py'
    fix_raw_transaction(blockchain_path)
