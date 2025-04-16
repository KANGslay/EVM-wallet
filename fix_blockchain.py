#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
此脚本用于修复blockchain.py文件中的Web3.py版本兼容性问题
'''

def fix_raw_transaction():
    file_path = 'app/services/blockchain.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换所有的rawTransaction为raw_transaction
        updated_content = content.replace('rawTransaction', 'raw_transaction')
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f'文件 {file_path} 已成功更新，将rawTransaction替换为raw_transaction')
        return True
    except Exception as e:
        print(f'修复文件时出错: {str(e)}')
        return False

if __name__ == '__main__':
    fix_raw_transaction()
